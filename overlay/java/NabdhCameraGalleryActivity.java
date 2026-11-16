package org.telegram.ui;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ContentUris;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.LruCache;
import android.util.Size;
import android.view.Gravity;
import android.view.View;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.core.content.FileProvider;
import org.telegram.ui.Components.NabdhToolUi;
import java.io.File;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Gallery limited to photos explicitly captured by Nabdh Camera2.
 * Never scans unrelated albums; no READ_MEDIA_IMAGES permission is needed.
 */
public final class NabdhCameraGalleryActivity extends Activity {
    private static final int MAX_ITEMS = 400;
    private static final String PREFIX = "NabdhCamera_";
    private final ArrayList<Uri> photos = new ArrayList<>();
    private final LruCache<String, Bitmap> thumbnails = new LruCache<String, Bitmap>(8 * 1024 * 1024) {
        @Override protected int sizeOf(String key, Bitmap bitmap) { return bitmap.getByteCount(); }
    };
    private final ThreadPoolExecutor thumbnailsWorker = new ThreadPoolExecutor(
            2, 2, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(70));
    private GridView grid;
    private TextView count;
    private boolean destroyed;
    private int scanGeneration;
    private int previewGeneration;
    private final BaseAdapter adapter = new BaseAdapter() {
        @Override public int getCount() { return photos.size(); }
        @Override public Object getItem(int pos) { return photos.get(pos); }
        @Override public long getItemId(int pos) { return pos; }
        @Override public View getView(int pos, View old, android.view.ViewGroup parent) {
            ImageView image = old instanceof ImageView ? (ImageView) old :
                    new ImageView(NabdhCameraGalleryActivity.this);
            image.setScaleType(ImageView.ScaleType.CENTER_CROP);
            image.setBackgroundColor(0x18000000);
            image.setLayoutParams(new android.widget.AbsListView.LayoutParams(-1, dp(116)));
            Uri uri = photos.get(pos);
            String key = uri.toString();
            image.setTag(key);
            Bitmap cached = thumbnails.get(key);
            image.setImageBitmap(cached);
            if (cached == null) {
                try {
                    thumbnailsWorker.execute(() -> {
                        Bitmap bitmap = decode(uri, 260);
                        if (bitmap == null) return;
                        synchronized (thumbnails) { thumbnails.put(key, bitmap); }
                        runOnUiThread(() -> {
                            if (!destroyed && key.equals(image.getTag())) {
                                image.setImageBitmap(bitmap);
                            }
                        });
                    });
                } catch (RejectedExecutionException busy) {
                    // On fast scrolling let RecyclerView/GridView rebind later.
                }
            }
            return image;
        }
    };

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private String local(String en, String ar) {
        return org.telegram.messenger.LocaleController.isRTL ? ar : en;
    }
    private Button button(String en, String ar, Runnable action) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(local(en, ar));
        NabdhToolUi.styleButton(this, b);
        b.setOnClickListener(v -> action.run());
        return b;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundGray));
        page.setPadding(dp(10), dp(6), dp(10), dp(6));
        count = new TextView(this);
        count.setTextSize(14);
        count.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        count.setText(local("Loading Nabdh photos…", "جارٍ تحميل صور كاميرا نبض…"));
        count.setGravity(Gravity.CENTER);
        page.addView(count, new LinearLayout.LayoutParams(-1, dp(44)));
        page.addView(button("Refresh gallery", "تحديث المعرض", this::refresh),
                new LinearLayout.LayoutParams(-1, dp(48)));
        grid = new GridView(this);
        grid.setNumColumns(3);
        grid.setHorizontalSpacing(dp(5));
        grid.setVerticalSpacing(dp(5));
        grid.setAdapter(adapter);
        grid.setOnItemClickListener((parent, view, pos, id) -> showPhoto(pos));
        page.addView(grid, new LinearLayout.LayoutParams(-1, 0, 1));
        NabdhToolUi.install(this, page, local("Nabdh Camera Gallery", "معرض صور كاميرا نبض"));
    }
    @Override protected void onResume() { super.onResume(); refresh(); }
    private void refresh() {
        final int generation = ++scanGeneration;
        count.setText(local("Loading Nabdh photos…", "جارٍ تحميل صور كاميرا نبض…"));
        try {
            thumbnailsWorker.execute(() -> {
                ArrayList<Uri> found = findOwnPhotos();
                runOnUiThread(() -> {
                    if (destroyed || generation != scanGeneration) return;
                    photos.clear();
                    photos.addAll(found);
                    adapter.notifyDataSetChanged();
                    count.setText(local("Nabdh Camera photos: ", "صور كاميرا نبض: ") + photos.size()
                            + (photos.size() == MAX_ITEMS ? local(" (most recent)", " (الأحدث)") : ""));
                });
            });
        } catch (RejectedExecutionException busy) {
            count.setText(local("Gallery is busy. Try refresh again.", "المعرض مشغول، أعد التحديث."));
        }
    }
    private ArrayList<Uri> findOwnPhotos() {
        ArrayList<Uri> found = new ArrayList<>();
        if (Build.VERSION.SDK_INT >= 29) {
            Uri collection = MediaStore.Images.Media.EXTERNAL_CONTENT_URI;
            String[] fields = {MediaStore.Images.Media._ID};
            String where = MediaStore.Images.Media.RELATIVE_PATH + "=? AND "
                    + MediaStore.Images.Media.DISPLAY_NAME + " LIKE ? AND "
                    + MediaStore.Images.Media.IS_PENDING + "=0";
            String[] args = {Environment.DIRECTORY_PICTURES + "/NabdhGram/",
                    PREFIX + "%.jpg"};
            try (Cursor c = getContentResolver().query(collection, fields, where, args,
                    MediaStore.Images.Media.DATE_ADDED + " DESC")) {
                if (c != null) {
                    while (c.moveToNext() && found.size() < MAX_ITEMS) {
                        found.add(ContentUris.withAppendedId(collection, c.getLong(0)));
                    }
                }
            } catch (RuntimeException inaccessible) {
                // Never request broad gallery access for a private camera album.
            }
        } else {
            File root = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
            File folder = root == null ? null : new File(root, "NabdhGram");
            File[] files = folder == null ? null : folder.listFiles();
            if (files != null) {
                Arrays.sort(files, Comparator.comparingLong(File::lastModified).reversed());
                for (File file : files) {
                    if (found.size() >= MAX_ITEMS) break;
                    if (file.isFile() && file.getName().startsWith(PREFIX)
                            && file.getName().endsWith(".jpg")) {
                        try {
                            found.add(FileProvider.getUriForFile(this,
                                    getPackageName() + ".provider", file));
                        } catch (IllegalArgumentException invalid) { /* skip invalid */ }
                    }
                }
            }
        }
        return found;
    }
    private Bitmap decode(Uri uri, int target) {
        try {
            if (Build.VERSION.SDK_INT >= 29 && target <= 300) {
                return getContentResolver().loadThumbnail(uri, new Size(target, target), null);
            }
            BitmapFactory.Options bounds = new BitmapFactory.Options();
            bounds.inJustDecodeBounds = true;
            try (InputStream in = getContentResolver().openInputStream(uri)) {
                if (in == null) return null;
                BitmapFactory.decodeStream(in, null, bounds);
            }
            if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null;
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inPreferredConfig = Bitmap.Config.RGB_565;
            options.inSampleSize = 1;
            while (Math.max(bounds.outWidth, bounds.outHeight) / options.inSampleSize > target * 2) {
                options.inSampleSize *= 2;
            }
            try (InputStream in = getContentResolver().openInputStream(uri)) {
                return in == null ? null : BitmapFactory.decodeStream(in, null, options);
            }
        } catch (Exception | OutOfMemoryError ignored) {
            return null;
        }
    }
    private void showPhoto(int position) {
        if (position < 0 || position >= photos.size()) return;
        final int[] index = {position};
        final ImageView image = new ImageView(this);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        image.setBackgroundColor(Color.BLACK);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(8), dp(8), dp(8), dp(8));
        panel.addView(image, new LinearLayout.LayoutParams(-1,
                (int) (getResources().getDisplayMetrics().heightPixels * .60f)));
        LinearLayout nav = new LinearLayout(this);
        nav.setOrientation(LinearLayout.HORIZONTAL);
        Button prev = button("Previous", "السابقة", () -> {
            index[0] = (index[0] - 1 + photos.size()) % photos.size();
            loadPreview(photos.get(index[0]), image);
        });
        Button next = button("Next", "التالية", () -> {
            index[0] = (index[0] + 1) % photos.size();
            loadPreview(photos.get(index[0]), image);
        });
        nav.addView(prev, new LinearLayout.LayoutParams(0, dp(48), 1));
        nav.addView(next, new LinearLayout.LayoutParams(0, dp(48), 1));
        panel.addView(nav);
        panel.addView(button("Share original photo in NabdhGram", "مشاركة الصورة الأصلية في نبض جرام",
                () -> share(photos.get(index[0]))));
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setView(panel).setNegativeButton(local("Close", "إغلاق"), null).create();
        dialog.setOnDismissListener(x -> previewGeneration++);
        dialog.show();
        loadPreview(photos.get(position), image);
    }
    private void loadPreview(Uri uri, ImageView display) {
        int generation = ++previewGeneration;
        display.setImageDrawable(null);
        try {
            thumbnailsWorker.execute(() -> {
                Bitmap bitmap = decode(uri, 1800);
                runOnUiThread(() -> {
                    if (!destroyed && generation == previewGeneration && bitmap != null) {
                        display.setImageBitmap(bitmap);
                    }
                });
            });
        } catch (RejectedExecutionException busy) { /* retry via navigation */ }
    }
    private void share(Uri uri) {
        try {
            Intent send = new Intent(this, LaunchActivity.class);
            send.setAction(Intent.ACTION_SEND);
            send.setType("image/jpeg");
            send.putExtra(Intent.EXTRA_STREAM, uri);
            send.setClipData(ClipData.newUri(getContentResolver(), "NabdhGram photo", uri));
            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(send);
        } catch (RuntimeException inaccessible) {
            count.setText(local("Could not share this image", "تعذرت مشاركة الصورة"));
        }
    }
    @Override protected void onDestroy() {
        destroyed = true;
        ++scanGeneration;
        ++previewGeneration;
        thumbnailsWorker.shutdownNow();
        thumbnails.evictAll();
        super.onDestroy();
    }
}
