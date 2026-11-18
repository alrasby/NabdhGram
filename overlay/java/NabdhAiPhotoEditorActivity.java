package org.telegram.ui;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.exifinterface.media.ExifInterface;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.segmentation.Segmentation;
import com.google.mlkit.vision.segmentation.SegmentationMask;
import com.google.mlkit.vision.segmentation.Segmenter;
import com.google.mlkit.vision.segmentation.selfie.SelfieSegmenterOptions;
import org.telegram.ui.Components.NabdhToolUi;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Real ML Kit bundled on-device selfie segmentation, opt-in from private album.
 * This AI editor ONLY isolates people and blurs backgrounds. It does not
 * upscale image detail, invent pixels, or transmit photos to a cloud model.
 */
public final class NabdhAiPhotoEditorActivity extends Activity {
    public static final String EXTRA_NAME = "nabdh_photo_name";
    private static final int MAX_AI_EDGE = 2100;
    private final ThreadPoolExecutor worker = new ThreadPoolExecutor(
            1, 1, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(1));
    private File original;
    private ImageView preview;
    private TextView state;
    private Button save;
    private Bitmap resultBitmap;
    private boolean destroyed, working;

    private String local(String en, String ar) {
        return org.telegram.messenger.LocaleController.isRTL ? ar : en;
    }
    private int dp(int n) {
        return Math.round(n * getResources().getDisplayMetrics().density);
    }
    private Button button(String en, String ar, Runnable click) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(local(en, ar));
        NabdhToolUi.styleButton(this, b);
        b.setOnClickListener(v -> click.run());
        return b;
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        try {
            original = NabdhCameraFiles.photo(this, getIntent().getStringExtra(EXTRA_NAME));
        } catch (IOException invalid) {
            finish(); return;
        }
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(12), dp(8), dp(12), dp(10));
        page.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundGray));
        preview = new ImageView(this);
        preview.setScaleType(ImageView.ScaleType.FIT_CENTER);
        page.addView(preview, new LinearLayout.LayoutParams(-1, 0, 1));
        TextView note = new TextView(this);
        note.setText(local("Actual on-device ML Kit model: separates people from "
                    + "background, producing a private portrait blur. AI effect "
                    + "is limited to about 4 MP for stable RAM; your full-resolution "
                    + "original is always preserved. No cloud or AICore required.",
                    "نموذج ML Kit حقيقي على الجهاز: يفصل الشخص عن الخلفية ويُنشئ "
                    + "تأثير تمويه خاصًا. تُحدد نسخة التأثير بحوالي 4 ميجابكسل "
                    + "لحماية الذاكرة، وتبقى الصورة الأصلية بكامل دقتها دائمًا. "
                    + "لا رفع سحابي ولا حاجة إلى AICore."));
        note.setTextSize(13);
        note.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        page.addView(note);
        state = new TextView(this);
        state.setText(local("Select Apply AI portrait blur",
                "اضغط على تطبيق عزل الخلفية بالذكاء الاصطناعي"));
        state.setTextSize(13);
        page.addView(state);
        Button process = button("Apply AI portrait blur (local)",
                "تطبيق تمويه الخلفية بالذكاء المحلي", this::runModel);
        page.addView(process, new LinearLayout.LayoutParams(-1, dp(56)));
        save = button("Save AI edit as a separate private photo",
                "حفظ تعديل AI كصورة خاصة منفصلة", this::saveCopy);
        save.setEnabled(false);
        page.addView(save, new LinearLayout.LayoutParams(-1, dp(52)));
        NabdhToolUi.install(this, page,
                local("Nabdh AI Portrait Editor", "محرر نبض الذكي للصور الشخصية"));
    }
    private Bitmap decodeOriented() throws IOException {
        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        try (InputStream in = new FileInputStream(original)) {
            BitmapFactory.decodeStream(in, null, bounds);
        }
        if (bounds.outWidth < 2 || bounds.outHeight < 2)
            throw new IOException("Invalid private JPEG");
        BitmapFactory.Options opt = new BitmapFactory.Options();
        opt.inSampleSize = 1;
        while (Math.max(bounds.outWidth, bounds.outHeight) /
                opt.inSampleSize > MAX_AI_EDGE) opt.inSampleSize *= 2;
        opt.inPreferredConfig = Bitmap.Config.ARGB_8888;
        Bitmap raw;
        try (InputStream in = new FileInputStream(original)) {
            raw = BitmapFactory.decodeStream(in, null, opt);
        }
        if (raw == null) throw new IOException("AI input decode failed");
        ExifInterface exif = new ExifInterface(original);
        Matrix matrix = new Matrix();
        matrix.postRotate(exif.getRotationDegrees());
        if (exif.isFlipped()) matrix.postScale(-1f, 1f);
        Bitmap oriented = Bitmap.createBitmap(raw, 0, 0, raw.getWidth(),
                raw.getHeight(), matrix, true);
        if (oriented != raw) raw.recycle();
        return oriented;
    }
    private void runModel() {
        if (working) return;
        working = true;
        save.setEnabled(false);
        state.setText(local("Running on-device portrait model…",
                "جارٍ تشغيل نموذج عزل الأشخاص على الجهاز…"));
        try {
            worker.execute(() -> {
                final Bitmap input;
                try {
                    input = decodeOriented();
                } catch (Exception | OutOfMemoryError failure) {
                    failed("Could not load photo for AI processing",
                            "تعذر تحميل الصورة للمعالجة الذكية");
                    return;
                }
                if (destroyed) { input.recycle(); return; }
                Segmenter segmenter;
                try {
                    // Bundled 4.5 MB model, no network/download prerequisite.
                    SelfieSegmenterOptions opts = new SelfieSegmenterOptions.Builder()
                            .setDetectorMode(SelfieSegmenterOptions.SINGLE_IMAGE_MODE)
                            .enableRawSizeMask()
                            .build();
                    segmenter = Segmentation.getClient(opts);
                    segmenter.process(InputImage.fromBitmap(input, 0))
                            .addOnSuccessListener(mask -> {
                                try {
                                    worker.execute(() -> {
                                        try {
                                            Bitmap edited = portraitBlur(input, mask);
                                            runOnUiThread(() -> {
                                                if (destroyed) {
                                                    edited.recycle(); return;
                                                }
                                                if (resultBitmap != null) resultBitmap.recycle();
                                                resultBitmap = edited;
                                                preview.setImageBitmap(resultBitmap);
                                                working = false;
                                                save.setEnabled(true);
                                                state.setText(local("On-device AI edit ready. Save a copy.",
                                                        "اكتمل تعديل الذكاء المحلي. احفظ نسخة."));
                                            });
                                        } catch (Exception | OutOfMemoryError error) {
                                            failed("Could not apply portrait mask",
                                                    "تعذر تطبيق قناع عزل الشخص");
                                        } finally {
                                            input.recycle();
                                            segmenter.close();
                                        }
                                    });
                                } catch (RejectedExecutionException unavailable) {
                                    input.recycle();
                                    segmenter.close();
                                    failed("AI editor was closed", "أُغلق المحرر الذكي");
                                }
                            })
                            .addOnFailureListener(failure -> {
                                input.recycle();
                                segmenter.close();
                                failed("Local portrait segmentation unavailable",
                                        "نموذج عزل الأشخاص المحلي غير متاح");
                            });
                } catch (Exception | LinkageError failure) {
                    input.recycle();
                    failed("Local AI model could not start", "تعذر تشغيل نموذج الصور المحلي");
                }
            });
        } catch (RejectedExecutionException unavailable) {
            failed("Image editor is busy", "محرر الصور مشغول");
        }
    }
    /** Efficient row-by-row mask compositing, keeping bitmap memory bounded. */
    private static Bitmap portraitBlur(Bitmap source, SegmentationMask mask)
            throws IOException {
        int w=source.getWidth(),h=source.getHeight();
        if (w < 256 || h < 256 || (long) w*h > 6_000_000L)
            throw new IOException("Unsupported AI image size");
        int mw=mask.getWidth(),mh=mask.getHeight();
        if (mw < 1 || mh < 1 || (long) mw*mh > 12_000_000L)
            throw new IOException("Invalid model mask dimensions");
        ByteBuffer bytes=mask.getBuffer().duplicate().order(ByteOrder.nativeOrder());
        FloatBuffer confidence=bytes.asFloatBuffer();
        if (confidence.remaining() < (long) mw*mh)
            throw new IOException("Incomplete portrait mask");
        int smallW=Math.max(1,w/24),smallH=Math.max(1,h/24);
        Bitmap tiny=Bitmap.createScaledBitmap(source,smallW,smallH,true);
        Bitmap background=Bitmap.createScaledBitmap(tiny,w,h,true);
        if (tiny!=background) tiny.recycle();
        Bitmap out=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
        try {
            final int blockHeight=64;
            int[] fg=new int[w*blockHeight];
            int[] bg=new int[w*blockHeight];
            for(int y=0;y<h;y+=blockHeight) {
                int rows=Math.min(blockHeight,h-y);
                source.getPixels(fg,0,w,0,y,w,rows);
                background.getPixels(bg,0,w,0,y,w,rows);
                for(int row=0;row<rows;row++) {
                    int my=Math.min(mh-1,(y+row)*mh/h);
                    for(int x=0;x<w;x++) {
                        int mx=Math.min(mw-1,x*mw/w);
                        float p=confidence.get(my*mw+mx);
                        float alpha=Math.max(0,Math.min(1,(p-.30f)/.42f));
                        int idx=row*w+x;
                        int a=fg[idx],b=bg[idx];
                        int rr=(int)(((a>>>16)&255)*alpha+((b>>>16)&255)*(1-alpha));
                        int gg=(int)(((a>>>8)&255)*alpha+((b>>>8)&255)*(1-alpha));
                        int bb=(int)((a&255)*alpha+(b&255)*(1-alpha));
                        fg[idx]=0xff000000|(rr<<16)|(gg<<8)|bb;
                    }
                }
                out.setPixels(fg,0,w,0,y,w,rows);
            }
            return out;
        } catch (RuntimeException failure) {
            out.recycle();
            throw failure;
        } finally {
            background.recycle();
        }
    }
    private void saveCopy() {
        if (resultBitmap == null || working) return;
        working = true;
        save.setEnabled(false);
        state.setText(local("Saving AI-edited private copy…",
                "جارٍ حفظ نسخة الصورة المحسنة…"));
        final Bitmap bitmap = resultBitmap;
        try {
            worker.execute(() -> {
                File file = null;
                try {
                    file = NabdhCameraFiles.newPhoto(this);
                    try (FileOutputStream out = new FileOutputStream(file)) {
                        if (!bitmap.compress(Bitmap.CompressFormat.JPEG, 95, out))
                            throw new IOException("AI JPEG encode failed");
                    }
                    if (file.length() < 100) throw new IOException("Empty AI image");
                    runOnUiThread(() -> {
                        if (destroyed) return;
                        working=false;
                        save.setEnabled(true);
                        state.setText(local("AI portrait copy saved in private gallery",
                                "حُفظت نسخة AI في المعرض الخاص"));
                    });
                } catch (Exception | OutOfMemoryError problem) {
                    if (file != null) file.delete();
                    failed("Could not save AI edit; original untouched",
                            "تعذر حفظ تعديل AI؛ بقيت الصورة الأصلية دون تغيير");
                }
            });
        } catch (RejectedExecutionException busy) {
            failed("AI save queue busy", "طابور حفظ الصور الذكية مشغول");
        }
    }
    private void failed(String en, String ar) {
        runOnUiThread(() -> {
            if (!destroyed) {
                working=false;
                save.setEnabled(resultBitmap != null);
                state.setText(local(en,ar));
            }
        });
    }
    @Override protected void onDestroy() {
        destroyed=true;
        worker.shutdownNow();
        if (resultBitmap != null) { resultBitmap.recycle();resultBitmap=null; }
        super.onDestroy();
    }
}
