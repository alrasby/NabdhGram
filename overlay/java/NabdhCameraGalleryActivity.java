package org.telegram.ui;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import androidx.exifinterface.media.ExifInterface;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.util.LruCache;
import android.view.Gravity;
import android.view.View;
import android.widget.BaseAdapter;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Button;
import org.telegram.ui.Components.NabdhToolUi;
import java.io.File;
import java.io.FileInputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Nabdh Camera's app-private photo gallery. No public gallery permission. */
public final class NabdhCameraGalleryActivity extends Activity {
    private final ArrayList<File> photos = new ArrayList<>();
    private final LruCache<String, Bitmap> cache = new LruCache<String, Bitmap>(8 * 1024 * 1024) {
        @Override protected int sizeOf(String k, Bitmap b) { return b.getByteCount(); }
    };
    private final ThreadPoolExecutor io = new ThreadPoolExecutor(
            2, 2, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(50));
    private GridView grid;
    private TextView count;
    private volatile boolean destroyed;
    private int scanGeneration, previewGeneration;
    private final BaseAdapter adapter = new BaseAdapter() {
        @Override public int getCount() { return photos.size(); }
        @Override public Object getItem(int pos) { return photos.get(pos); }
        @Override public long getItemId(int pos) { return pos; }
        @Override public View getView(int pos, View old, android.view.ViewGroup parent) {
            ImageView view = old instanceof ImageView ? (ImageView) old :
                    new ImageView(NabdhCameraGalleryActivity.this);
            view.setScaleType(ImageView.ScaleType.CENTER_CROP);
            view.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp(116)));
            File file = photos.get(pos);
            String key = file.getName() + ":" + file.lastModified();
            view.setTag(key);
            Bitmap bitmap;
            synchronized (cache) { bitmap = cache.get(key); }
            view.setImageBitmap(bitmap);
            if (bitmap == null) {
                try {
                    io.execute(() -> {
                        Bitmap loaded = decode(file, 260);
                        if (loaded == null || destroyed) return;
                        synchronized (cache) { cache.put(key, loaded); }
                        runOnUiThread(() -> {
                            if (!destroyed && key.equals(view.getTag())) view.setImageBitmap(loaded);
                        });
                    });
                } catch (RejectedExecutionException ignored) { }
            }
            return view;
        }
    };
    private int dp(int d) { return Math.round(d * getResources().getDisplayMetrics().density); }
    private String local(String en, String ar) {
        return org.telegram.messenger.LocaleController.isRTL ? ar : en;
    }
    private Button action(String en, String ar, Runnable click) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(local(en, ar));
        NabdhToolUi.styleButton(this, b);
        b.setOnClickListener(v -> click.run());
        return b;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(10), dp(6), dp(10), dp(6));
        page.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundGray));
        count = new TextView(this);
        count.setTextSize(14);
        count.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        count.setGravity(Gravity.CENTER);
        count.setText(local("Loading private photos", "جارٍ تحميل الصور الخاصة"));
        page.addView(count, new LinearLayout.LayoutParams(-1, dp(44)));
        page.addView(action("Refresh", "تحديث", this::refresh));
        grid = new GridView(this);
        grid.setNumColumns(3);
        grid.setHorizontalSpacing(dp(5));
        grid.setVerticalSpacing(dp(5));
        grid.setAdapter(adapter);
        grid.setOnItemClickListener((parent, view, pos, id) -> showPhoto(pos));
        page.addView(grid, new LinearLayout.LayoutParams(-1, 0, 1));
        NabdhToolUi.install(this, page, local("Private Nabdh Camera Gallery",
                "معرض كاميرا نبض الخاص"));
    }
    @Override protected void onResume() {
        super.onResume();
        refresh();
    }
    private void refresh() {
        final int version = ++scanGeneration;
        try {
            io.execute(() -> {
                File[] files;
                try { files = NabdhCameraFiles.recent(this); }
                catch (Exception e) { files = new File[0]; }
                final File[] result = files;
                runOnUiThread(() -> {
                    if (destroyed || version != scanGeneration) return;
                    photos.clear();
                    photos.addAll(Arrays.asList(result));
                    adapter.notifyDataSetChanged();
                    count.setText(local("Private Nabdh photos: ", "صور نبض الخاصة: ") + photos.size());
                });
            });
        } catch (RejectedExecutionException busy) {
            count.setText(local("Gallery is busy. Try again.", "المعرض مشغول، أعد المحاولة."));
        }
    }
    private Bitmap decode(File file, int target) {
        try {
            BitmapFactory.Options bounds = new BitmapFactory.Options();
            bounds.inJustDecodeBounds = true;
            try (FileInputStream in = new FileInputStream(file)) {
                BitmapFactory.decodeStream(in, null, bounds);
            }
            if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null;
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inPreferredConfig = Bitmap.Config.RGB_565;
            options.inSampleSize = 1;
            while (Math.max(bounds.outWidth, bounds.outHeight) /
                    options.inSampleSize > target * 2) options.inSampleSize *= 2;
            Bitmap raw;
            try (FileInputStream in = new FileInputStream(file)) {
                raw = BitmapFactory.decodeStream(in, null, options);
            }
            if (raw == null) return null;
            try {
                ExifInterface exif = new ExifInterface(file);
                int degrees = exif.getRotationDegrees();
                boolean mirror = exif.isFlipped();
                if (degrees == 0 && !mirror) return raw;
                Matrix matrix = new Matrix();
                matrix.postRotate(degrees);
                if (mirror) matrix.postScale(-1f, 1f);
                Bitmap corrected = Bitmap.createBitmap(raw, 0, 0,
                        raw.getWidth(), raw.getHeight(), matrix, true);
                if (corrected != raw) raw.recycle();
                return corrected;
            } catch (Exception | OutOfMemoryError error) {
                return raw;
            }
        } catch (Exception | OutOfMemoryError ignored) {
            return null;
        }
    }
    private void showPhoto(int position) {
        if (position < 0 || position >= photos.size()) return;
        final int[] current = {position};
        ImageView image = new ImageView(this);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        image.setBackgroundColor(Color.BLACK);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.addView(image, new LinearLayout.LayoutParams(-1,
                (int) (getResources().getDisplayMetrics().heightPixels * .58f)));
        LinearLayout navigation = new LinearLayout(this);
        Button prev = action("Previous", "السابقة", () -> {
            current[0] = (current[0] - 1 + photos.size()) % photos.size();
            loadPreview(photos.get(current[0]), image);
        });
        Button next = action("Next", "التالية", () -> {
            current[0] = (current[0] + 1) % photos.size();
            loadPreview(photos.get(current[0]), image);
        });
        navigation.addView(prev, new LinearLayout.LayoutParams(0, dp(46), 1));
        navigation.addView(next, new LinearLayout.LayoutParams(0, dp(46), 1));
        page.addView(navigation);
        page.addView(action("Crop / rotate (save separate copy)",
                "اقتصاص / تدوير (حفظ نسخة منفصلة)", () -> {
            Intent editor = new Intent(this, NabdhPhotoEditorActivity.class);
            editor.putExtra(NabdhPhotoEditorActivity.EXTRA_NAME,
                    photos.get(current[0]).getName());
            startActivity(editor);
        }));
        page.addView(action("AI portrait editor — on-device person detection",
                "محرر صور AI — عزل الشخص محليًا", () -> {
            Intent ai = new Intent(this, NabdhAiPhotoEditorActivity.class);
            ai.putExtra(NabdhAiPhotoEditorActivity.EXTRA_NAME,
                    photos.get(current[0]).getName());
            startActivity(ai);
        }));
        page.addView(action("Share without location metadata",
                "مشاركة دون بيانات الموقع", () -> share(photos.get(current[0]))));
        AlertDialog dialog = new AlertDialog.Builder(this).setView(page)
                .setNegativeButton(local("Close", "إغلاق"), null).create();
        dialog.setOnDismissListener(x -> ++previewGeneration);
        dialog.show();
        loadPreview(photos.get(position), image);
    }
    private void loadPreview(File file, ImageView image) {
        final int version = ++previewGeneration;
        image.setImageDrawable(null);
        try {
            io.execute(() -> {
                Bitmap b = decode(file, 1700);
                runOnUiThread(() -> {
                    if (!destroyed && version == previewGeneration) image.setImageBitmap(b);
                });
            });
        } catch (RejectedExecutionException busy) { }
    }
    private void share(File file) {
        count.setText(local("Removing location metadata…", "جارٍ حذف بيانات الموقع من نسخة المشاركة…"));
        try {
            io.execute(() -> {
                try {
                    Uri safe = NabdhCameraFiles.sanitizedShare(this, file);
                    runOnUiThread(() -> {
                        if (destroyed) return;
                        try {
                            Intent send = new Intent(this, LaunchActivity.class);
                            send.setAction(Intent.ACTION_SEND);
                            send.setType("image/jpeg");
                            send.putExtra(Intent.EXTRA_STREAM, safe);
                            send.setClipData(ClipData.newUri(getContentResolver(), "Nabdh photo", safe));
                            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                            startActivity(send);
                        } catch (RuntimeException fail) {
                            count.setText(local("Sharing failed", "تعذرت المشاركة"));
                        }
                    });
                } catch (Exception failure) {
                    runOnUiThread(() -> {
                        if (!destroyed) count.setText(local(
                                "Could not scrub metadata; original NOT shared",
                                "تعذر تنظيف البيانات؛ لم تُشارك الصورة الأصلية"));
                    });
                }
            });
        } catch (RejectedExecutionException busy) {
            count.setText(local("Image processor busy", "معالج الصور مشغول"));
        }
    }
    @Override protected void onDestroy() {
        destroyed = true;
        ++previewGeneration;
        ++scanGeneration;
        io.shutdownNow();
        synchronized (cache) { cache.evictAll(); }
        super.onDestroy();
    }
}
