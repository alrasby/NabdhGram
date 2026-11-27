package org.telegram.ui;

import android.app.Activity;
import org.telegram.ui.ActionBar.AlertDialog;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.BitmapRegionDecoder;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.os.Bundle;
import android.util.AtomicFile;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.exifinterface.media.ExifInterface;
import org.telegram.ui.Components.NabdhToolUi;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Manual, offline crop/rotate editor; uses a bounded bitmap region decode.
 * Edits are saved as new private files by default and never upload media.
 */
public final class NabdhPhotoEditorActivity extends Activity {
    public static final String EXTRA_NAME = "nabdh_photo_name";
    private final ThreadPoolExecutor worker = new ThreadPoolExecutor(
            1, 1, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(2));
    private File original;
    private CropView preview;
    private TextView status;
    private Button save;
    private CheckBox keepOriginal;
    private int rawWidth, rawHeight, exifRotation, userRotation;
    private boolean exifFlipped, destroyed, saving;
    private int renderGeneration;

    private String local(String en, String ar) {
        return org.telegram.messenger.LocaleController.isRTL ? ar : en;
    }
    private int dp(int d) {
        return Math.round(d * getResources().getDisplayMetrics().density);
    }
    private Button button(String en, String ar, Runnable click) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(local(en, ar));
        NabdhToolUi.styleButton(this, b);
        b.setOnClickListener(v -> click.run());
        return b;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        try {
            original = NabdhCameraFiles.photo(this, getIntent().getStringExtra(EXTRA_NAME));
        } catch (IOException invalid) {
            finish();
            return;
        }
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(10), dp(8), dp(10), dp(10));
        page.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundGray));
        preview = new CropView();
        page.addView(preview, new LinearLayout.LayoutParams(-1, 0, 1));
        LinearLayout rotateRow = new LinearLayout(this);
        rotateRow.addView(button("Rotate left 90°", "تدوير 90° لليسار", () -> rotate(-90)),
                new LinearLayout.LayoutParams(0, dp(52), 1));
        rotateRow.addView(button("Rotate right 90°", "تدوير 90° لليمين", () -> rotate(90)),
                new LinearLayout.LayoutParams(0, dp(52), 1));
        page.addView(rotateRow);
        LinearLayout cropRow = new LinearLayout(this);
        cropRow.addView(button("Free crop", "اقتصاص حر", () -> preview.setAspect(0, 0)),
                new LinearLayout.LayoutParams(0, dp(50), 1));
        cropRow.addView(button("Square 1:1", "مربع 1:1", () -> preview.setAspect(1, 1)),
                new LinearLayout.LayoutParams(0, dp(50), 1));
        cropRow.addView(button("4:3", "4:3", () -> preview.setAspect(4, 3)),
                new LinearLayout.LayoutParams(0, dp(50), 1));
        cropRow.addView(button("16:9", "16:9", () -> preview.setAspect(16, 9)),
                new LinearLayout.LayoutParams(0, dp(50), 1));
        page.addView(cropRow);
        page.addView(button("Use whole image", "الصورة كاملة", () -> preview.resetCrop()),
                new LinearLayout.LayoutParams(-1, dp(46)));
        keepOriginal = new CheckBox(this);
        keepOriginal.setText(local("Keep original photo (recommended)",
                "الاحتفاظ بالصورة الأصلية (موصى به)"));
        keepOriginal.setChecked(true);
        page.addView(keepOriginal);
        TextView note = new TextView(this);
        note.setText(local("Drag the crop frame or resize its lower corner. "
                        + "A cropped copy may be downsampled to 12 MP for memory safety. "
                        + "Rotation without cropping preserves JPEG pixel data.",
                        "اسحب إطار القص أو غيّر حجمه من زاويته السفلية. قد تنخفض دقة النسخة "
                        + "المقتصّة إلى 12 ميجابكسل لحماية الذاكرة؛ أما التدوير دون قص "
                        + "فيحافظ على بيانات JPEG الأصلية."));
        note.setTextSize(12);
        note.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        page.addView(note);
        status = new TextView(this);
        status.setText(local("Loading private image…", "جارٍ فتح الصورة الخاصة…"));
        status.setTextSize(13);
        page.addView(status);
        save = button("Save edited image", "حفظ الصورة المعدّلة", this::confirmSave);
        save.setEnabled(false);
        page.addView(save, new LinearLayout.LayoutParams(-1, dp(52)));
        NabdhToolUi.install(this, page, local("Nabdh Photo Editor", "محرر صور نبض"));
        loadPreview();
    }
    /** Compatible with Android API 23; Math.floorMod requires API 24. */
    private static int normalRotation(int degrees) {
        int remainder = degrees % 360;
        return remainder < 0 ? remainder + 360 : remainder;
    }
    private void rotate(int amount) {
        userRotation = normalRotation(userRotation + amount);
        loadPreview();
    }
    private void loadPreview() {
        int version = ++renderGeneration;
        save.setEnabled(false);
        status.setText(local("Preparing preview…", "جارٍ تجهيز المعاينة…"));
        try {
            worker.execute(() -> {
                Bitmap bitmap = null;
                int w = 0, h = 0, exif = 0;
                boolean flip = false;
                try {
                    BitmapFactory.Options bounds = new BitmapFactory.Options();
                    bounds.inJustDecodeBounds = true;
                    try (InputStream in = new FileInputStream(original)) {
                        BitmapFactory.decodeStream(in, null, bounds);
                    }
                    w = bounds.outWidth; h = bounds.outHeight;
                    if (w < 2 || h < 2) throw new IOException("Invalid JPEG size");
                    ExifInterface sourceExif = new ExifInterface(original);
                    exif = sourceExif.getRotationDegrees();
                    flip = sourceExif.isFlipped();
                    BitmapFactory.Options opt = new BitmapFactory.Options();
                    opt.inSampleSize = 1;
                    while (Math.max(w, h) / opt.inSampleSize > 1400) opt.inSampleSize *= 2;
                    opt.inPreferredConfig = Bitmap.Config.RGB_565;
                    Bitmap raw;
                    try (InputStream in = new FileInputStream(original)) {
                        raw = BitmapFactory.decodeStream(in, null, opt);
                    }
                    if (raw == null) throw new IOException("Preview decoder failed");
                    Matrix transform = new Matrix();
                    transform.postRotate(normalRotation(exif + userRotation));
                    if (flip) transform.postScale(-1, 1);
                    bitmap = Bitmap.createBitmap(raw, 0, 0, raw.getWidth(),
                            raw.getHeight(), transform, true);
                    if (bitmap != raw) raw.recycle();
                } catch (Exception | OutOfMemoryError fail) { /* show safe failure */ }
                final Bitmap rendered = bitmap;
                final int width = w, height = h, rotation = exif;
                final boolean flipped = flip;
                runOnUiThread(() -> {
                    if (destroyed || version != renderGeneration) {
                        if (rendered != null) rendered.recycle();
                        return;
                    }
                    rawWidth = width;
                    rawHeight = height;
                    exifRotation = rotation;
                    exifFlipped = flipped;
                    preview.setImage(rendered);
                    save.setEnabled(rendered != null);
                    status.setText(rendered == null
                            ? local("Could not decode image", "تعذر فتح الصورة")
                            : local("Preview ready; drag to adjust crop",
                                    "المعاينة جاهزة، اسحب لضبط الاقتصاص"));
                });
            });
        } catch (RejectedExecutionException busy) {
            status.setText(local("Editor busy", "المحرر مشغول"));
        }
    }
    private void confirmSave() {
        if (saving || preview == null || rawWidth < 2 || rawHeight < 2) return;
        if (!keepOriginal.isChecked()) {
            new AlertDialog.Builder(this)
                    .setTitle(local("Replace original photo?", "استبدال الصورة الأصلية؟"))
                    .setMessage(local("Your original will be replaced after the edited "
                                    + "image is safely written. This cannot be undone.",
                                    "ستُستبدل الصورة الأصلية بعد كتابة الصورة المعدلة بأمان. "
                                    + "لا يمكن التراجع عن هذا الإجراء."))
                    .setNegativeButton(local("Cancel", "إلغاء"), null)
                    .setPositiveButton(local("Replace", "استبدال"),
                            (dialog, which) -> beginSave(false)).show();
        } else beginSave(true);
    }
    private void beginSave(boolean preserve) {
        RectF crop = preview.crop();
        final int rotation = normalRotation(exifRotation + userRotation);
        final boolean flipped = exifFlipped;
        final int w = rawWidth, h = rawHeight;
        final int rotateByUser = userRotation;
        saving = true;
        save.setEnabled(false);
        status.setText(local("Saving edited copy…", "جارٍ حفظ التعديل…"));
        try {
            worker.execute(() -> {
                File temp = null;
                try {
                    temp = NabdhCameraFiles.newPhoto(this);
                    boolean full = crop.left < .002f && crop.top < .002f
                            && crop.right > .998f && crop.bottom > .998f;
                    if (full) {
                        // 90-degree rotation by modifying EXIF, without any
                        // recompression or image pixel resampling.
                        try (InputStream in = new FileInputStream(original);
                             FileOutputStream out = new FileOutputStream(temp)) {
                            byte[] block = new byte[32 * 1024];
                            int n;
                            while ((n = in.read(block)) >= 0) if (n > 0) out.write(block, 0, n);
                        }
                        if (rotateByUser != 0) {
                            ExifInterface exif = new ExifInterface(temp);
                            exif.rotate(rotateByUser);
                            exif.saveAttributes();
                        }
                    } else {
                        // Pixel-accurate region decoding; memory bounded to 12 MP.
                        Rect region = toRaw(crop, rotation, flipped, w, h);
                        BitmapRegionDecoder decoder = BitmapRegionDecoder.newInstance(
                                original.getAbsolutePath(), false);
                        Bitmap bitmap;
                        try {
                            BitmapFactory.Options options = new BitmapFactory.Options();
                            options.inPreferredConfig = Bitmap.Config.ARGB_8888;
                            options.inSampleSize = 1;
                            while ((long) region.width() * region.height() /
                                    (options.inSampleSize * options.inSampleSize) > 12_000_000L)
                                options.inSampleSize *= 2;
                            bitmap = decoder.decodeRegion(region, options);
                        } finally { decoder.recycle(); }
                        if (bitmap == null) throw new IOException("Crop decoding failed");
                        try (FileOutputStream out = new FileOutputStream(temp)) {
                            if (!bitmap.compress(Bitmap.CompressFormat.JPEG, 96, out))
                                throw new IOException("Crop JPEG encoding failed");
                        } finally { bitmap.recycle(); }
                        // A newly encoded crop has no original GPS or XMP.
                        ExifInterface exif = new ExifInterface(temp);
                        exif.setAttribute(ExifInterface.TAG_ORIENTATION,
                                Integer.toString(orientationTag(rotation, flipped)));
                        exif.saveAttributes();
                    }
                    if (temp.length() <= 0) throw new IOException("Empty edit");
                    if (!preserve) {
                        AtomicFile atom = new AtomicFile(original);
                        FileOutputStream out = null;
                        try {
                            out = atom.startWrite();
                            try (InputStream in = new FileInputStream(temp)) {
                                byte[] block = new byte[32 * 1024];
                                int n;
                                while ((n = in.read(block)) != -1) if (n > 0) out.write(block, 0, n);
                            }
                            atom.finishWrite(out);
                        } catch (IOException failure) {
                            if (out != null) atom.failWrite(out);
                            throw failure;
                        }
                        temp.delete();
                    }
                    runOnUiThread(() -> {
                        if (destroyed) return;
                        saving = false;
                        status.setText(preserve ?
                                local("Edited copy saved in private Nabdh Gallery",
                                        "حُفظت نسخة معدّلة في معرض نبض الخاص") :
                                local("Original replaced safely", "استُبدلت الصورة الأصلية بأمان"));
                        save.setEnabled(true);
                    });
                } catch (Exception | OutOfMemoryError failure) {
                    if (temp != null) temp.delete();
                    runOnUiThread(() -> {
                        if (destroyed) return;
                        saving = false;
                        save.setEnabled(true);
                        status.setText(local("Edit failed; original kept",
                                "فشل التعديل، وبقيت الصورة الأصلية محفوظة"));
                    });
                }
            });
        } catch (RejectedExecutionException busy) {
            saving = false;
            save.setEnabled(true);
            status.setText(local("Editor busy; retry", "المحرر مشغول، أعد المحاولة"));
        }
    }
    private static int orientationTag(int angle, boolean flip) {
        switch (normalRotation(angle)) {
            case 90: return flip ? ExifInterface.ORIENTATION_TRANSPOSE :
                    ExifInterface.ORIENTATION_ROTATE_90;
            case 180: return flip ? ExifInterface.ORIENTATION_FLIP_VERTICAL :
                    ExifInterface.ORIENTATION_ROTATE_180;
            case 270: return flip ? ExifInterface.ORIENTATION_TRANSVERSE :
                    ExifInterface.ORIENTATION_ROTATE_270;
            default: return flip ? ExifInterface.ORIENTATION_FLIP_HORIZONTAL :
                    ExifInterface.ORIENTATION_NORMAL;
        }
    }
    private static Rect toRaw(RectF crop, int degrees, boolean flip, int w, int h) {
        float[][] corners = {{crop.left,crop.top}, {crop.right,crop.top},
                {crop.left,crop.bottom}, {crop.right,crop.bottom}};
        float minX=1, minY=1, maxX=0, maxY=0;
        for (float[] p : corners) {
            float u = flip ? 1f - p[0] : p[0], v = p[1];
            float x, y;
            switch (degrees) {
                case 90: x=v; y=1f-u; break;
                case 180: x=1f-u; y=1f-v; break;
                case 270: x=1f-v; y=u; break;
                default: x=u; y=v; break;
            }
            minX=Math.min(minX,x); maxX=Math.max(maxX,x);
            minY=Math.min(minY,y); maxY=Math.max(maxY,y);
        }
        int l = Math.max(0, Math.min(w-1, (int) (minX*w)));
        int t = Math.max(0, Math.min(h-1, (int) (minY*h)));
        int r = Math.min(w, Math.max(l+1, (int) Math.ceil(maxX*w)));
        int b = Math.min(h, Math.max(t+1, (int) Math.ceil(maxY*h)));
        return new Rect(l,t,r,b);
    }
    @Override protected void onDestroy() {
        destroyed = true;
        ++renderGeneration;
        worker.shutdownNow();
        if (preview != null) preview.clear();
        super.onDestroy();
    }

    /** Move a draggable, resizable crop rectangle. Normalized coordinates
     * give consistent controls across front/rear sensor resolutions.
     */
    private final class CropView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
        private Bitmap image;
        private RectF box = new RectF(0,0,1,1);
        private RectF frame = new RectF();
        private int aspectNumerator, aspectDenominator;
        private float pointerX, pointerY;
        private boolean resize;
        CropView() { super(NabdhPhotoEditorActivity.this); setBackgroundColor(Color.BLACK); }
        void clear() { if (image != null && !image.isRecycled()) image.recycle(); image=null; }
        void setImage(Bitmap bitmap) {
            clear(); image=bitmap; resetCrop(); invalidate();
        }
        void resetCrop() { box.set(0,0,1,1); invalidate(); }
        RectF crop() { return new RectF(box); }
        void setAspect(int num, int den) {
            aspectNumerator=num; aspectDenominator=den;
            if (image == null) return;
            float width=.78f, height=.78f;
            if (num > 0) {
                float normRatio=(num / (float) den) /
                        (image.getWidth() / (float) image.getHeight());
                if (normRatio < 1) width=height*normRatio;
                else height=width/normRatio;
            }
            box.set((1-width)/2,(1-height)/2,(1+width)/2,(1+height)/2);
            invalidate();
        }
        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            if (image == null || image.isRecycled()) return;
            float scale=Math.min(getWidth()/(float)image.getWidth(),
                    getHeight()/(float)image.getHeight());
            float width=scale*image.getWidth(),height=scale*image.getHeight();
            frame.set((getWidth()-width)/2,(getHeight()-height)/2,
                    (getWidth()+width)/2,(getHeight()+height)/2);
            paint.setColor(Color.WHITE);
            c.drawBitmap(image,null,frame,paint);
            float l=frame.left+box.left*width,t=frame.top+box.top*height;
            float r=frame.left+box.right*width,b=frame.top+box.bottom*height;
            paint.setColor(0x99000000);
            c.drawRect(frame.left,frame.top,frame.right,t,paint);
            c.drawRect(frame.left,b,frame.right,frame.bottom,paint);
            c.drawRect(frame.left,t,l,b,paint);
            c.drawRect(r,t,frame.right,b,paint);
            paint.setColor(Color.WHITE); paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(dp(2));
            c.drawRect(l,t,r,b,paint);
            paint.setStyle(Paint.Style.FILL);
            c.drawCircle(r,b,dp(7),paint);
        }
        @Override public boolean onTouchEvent(MotionEvent event) {
            if (image == null || frame.width() <= 0 || frame.height() <= 0)
                return false;
            float u=Math.max(0,Math.min(1,(event.getX()-frame.left)/frame.width()));
            float v=Math.max(0,Math.min(1,(event.getY()-frame.top)/frame.height()));
            if (event.getActionMasked()==MotionEvent.ACTION_DOWN) {
                pointerX=u;pointerY=v;
                resize=Math.abs(u-box.right)<.08f && Math.abs(v-box.bottom)<.08f;
                return true;
            }
            if (event.getActionMasked()==MotionEvent.ACTION_MOVE) {
                float dx=u-pointerX,dy=v-pointerY;
                if (resize) {
                    box.right=Math.max(box.left+.10f,Math.min(1,u));
                    box.bottom=Math.max(box.top+.10f,Math.min(1,v));
                    if (aspectNumerator>0) {
                        float ratio=(aspectNumerator/(float)aspectDenominator)/
                                (image.getWidth()/(float)image.getHeight());
                        float need=(box.right-box.left)/ratio;
                        box.bottom=Math.min(1,box.top+Math.max(.10f,need));
                        box.right=Math.min(1,box.left+
                                (box.bottom-box.top)*ratio);
                    }
                } else {
                    float left=Math.max(0,Math.min(1-box.width(),box.left+dx));
                    float top=Math.max(0,Math.min(1-box.height(),box.top+dy));
                    box.offsetTo(left,top);
                }
                pointerX=u;pointerY=v;invalidate();
                return true;
            }
            return event.getActionMasked()==MotionEvent.ACTION_UP;
        }
    }
}
