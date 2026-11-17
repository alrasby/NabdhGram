package org.telegram.messenger;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.util.LruCache;
import android.os.SystemClock;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Locale;
import java.util.Set;
import java.lang.ref.WeakReference;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * Actual independent PNG emoji rendering for Telegram text spans.
 * Privacy: only an emoji codepoint sequence, never a message, is requested.
 * Defaults to Telegram and performs no network work until a user selects a pack.
 * Copyright: Noto Emoji Apache-2.0, Twemoji CC-BY-4.0, OpenMoji CC-BY-SA-4.0.
 */
public final class NabdhEmojiPacks {
    public static final String TELEGRAM = "telegram";
    public static final String SYSTEM = "system";
    public static final String NOTO = "noto";
    public static final String TWEMOJI = "twemoji";
    public static final String OPENMOJI = "openmoji";

    // Pin exact upstream Git revisions so an upstream asset replacement does
    // not silently change an installed user's rendered glyphs.
    private static final String NOTO_BASE =
            "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@99701e07d3d1fe1bdbcdb14964547f0fd592966f/2D/png/72/";
    private static final String TWEMOJI_BASE =
            "https://cdn.jsdelivr.net/gh/jdecked/twemoji@b6b55fef1e8636b540a6d016a4729ca8cdf2e60b/assets/72x72/";
    private static final String OPENMOJI_BASE =
            "https://cdn.jsdelivr.net/gh/hfg-gmuend/openmoji@3e01de523ddefe9c5e46a7765b15efef04bf9002/color/72x72/";

    private static final String PREFS = "nabdhgram_emoji_packs_v1";
    private static final int MAX_IMAGE_BYTES = 180 * 1024;
    private static final long MAX_DISK_BYTES = 64L * 1024L * 1024L;
    // Bound pending downloads so a chat with many distinct emojis cannot grow
    // an unbounded executor queue or consume unlimited memory.
    // Parallel, bounded first-load fetches. Two workers caused long waves of
    // Telegram/selected-pack mixing as each individual PNG completed.
    private static final ThreadPoolExecutor EXECUTOR = new ThreadPoolExecutor(
            6, 6, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(256));
    private static final LruCache<String, Bitmap> MEMORY = new LruCache<String, Bitmap>(6 * 1024 * 1024) {
        @Override protected int sizeOf(String key, Bitmap bitmap) {
            return bitmap.getByteCount();
        }
    };
    private static final Set<String> PENDING = new HashSet<>();
    private static final long TEMPORARY_RETRY_MS = 90_000L;
    private static final long MISSING_GLYPH_RETRY_MS = 24L * 60L * 60L * 1000L;
    private static final Map<String, Long> RETRY_AFTER = new LinkedHashMap<String, Long>(128, .75f, true) {
        @Override protected boolean removeEldestEntry(Map.Entry<String, Long> eldest) {
            return size() > 1024;
        }
    };
    private static final Paint PAINT = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private static volatile String selected;

    // A cache populated per-scrolled-page is never a complete pack. It made
    // each new row visibly switch from Telegram to Noto/Twemoji/OpenMoji.
    // Do NOT activate external artwork until the whole supported picker set
    // has been installed. Later pages read the verified private cache directly.
    private static final String READY_MARKER = ".nabdh_pack_complete_v2";
    private static boolean redrawQueued;
    private static volatile int selectionVersion;

    public interface InstallListener {
        void onProgress(int done, int total);
        void onComplete(boolean success, int unsupportedCount);
    }

    private static File packFolder(Context context, String pack) {
        return new File(context.getNoBackupFilesDir(), "nabdh_emoji_" + pack);
    }

    public static boolean isReady(String pack) {
        if (TELEGRAM.equals(pack) || SYSTEM.equals(pack)) return true;
        if (!isSupported(pack)) return false;
        Context context = ApplicationLoader.applicationContext;
        return context != null && new File(packFolder(context, pack), READY_MARKER).isFile();
    }

    public static void cancelInstall() {
        ++selectionVersion; // Workers stop at their next codepoint boundary.
    }

    /**
     * Fully prepare a selected art pack BEFORE switching the UI. The first
     * download is intentionally asynchronous and user-visible; after that,
     * switching between installed packs is immediate and network-free.
     */
    public static void installAndChoose(Context context, String pack, InstallListener listener) {
        if (!isSupported(pack)) throw new IllegalArgumentException("Unknown emoji pack");
        final Context app = context.getApplicationContext();
        final WeakReference<InstallListener> callback = new WeakReference<>(listener);
        final int version = ++selectionVersion;
        if (isReady(pack)) {
            choose(app, pack);
            AndroidUtilities.runOnUIThread(() -> {
                InstallListener cb = callback.get();
                if (cb != null) cb.onComplete(true, 0);
            });
            return;
        }

        new Thread(() -> {
            final Set<String> unique = new HashSet<>();
            for (String[] section : EmojiData.data) {
                if (section == null) continue;
                for (String emoji : section) {
                    String id = cacheKey(pack, emoji);
                    if (id != null) unique.add(id);
                }
            }
            for (String[] section : EmojiData.dataColored) {
                if (section == null) continue;
                for (String emoji : section) {
                    String id = cacheKey(pack, emoji);
                    if (id != null) unique.add(id);
                }
            }
            final ArrayList<String> ids = new ArrayList<>(unique);
            final int total = ids.size();
            final AtomicInteger next = new AtomicInteger();
            final AtomicInteger done = new AtomicInteger();
            final AtomicInteger errors = new AtomicInteger();
            final AtomicInteger unsupported = new AtomicInteger();
            final CountDownLatch workers = new CountDownLatch(6);
            for (int w = 0; w < 6; ++w) {
                EXECUTOR.execute(() -> {
                    try {
                        int i;
                        while (version == selectionVersion && errors.get() < 10 &&
                               (i = next.getAndIncrement()) < total) {
                            final String id = ids.get(i);
                            final String key = id.substring(pack.length() + 1);
                            try {
                                Bitmap downloaded = loadBitmap(pack, key);
                                if (downloaded == null) errors.incrementAndGet();
                            } catch (FileNotFoundException missing) {
                                unsupported.incrementAndGet();
                                // Missing art is stable fallback, not a reason
                                // to hold the user in an endless install loop.
                                File folder = packFolder(app, pack);
                                if (folder.isDirectory()) {
                                    try {
                                        new File(folder, filename(pack, key) + ".missing").createNewFile();
                                    } catch (Exception ignored) {}
                                }
                            } catch (Exception failed) {
                                errors.incrementAndGet();
                            }
                            int completed = done.incrementAndGet();
                            if (completed % 30 == 0 || completed == total) {
                                AndroidUtilities.runOnUIThread(() -> {
                                    InstallListener cb = callback.get();
                                    if (cb != null && version == selectionVersion) {
                                        cb.onProgress(completed, total);
                                    }
                                });
                            }
                        }
                    } finally {
                        workers.countDown();
                    }
                });
            }
            try {
                workers.await();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                errors.incrementAndGet();
            }
            boolean complete = version == selectionVersion && done.get() == total &&
                    errors.get() == 0;
            if (complete) {
                // Commit on-disk readiness last; a cancelled/failed install
                // can never make half a pack visible.
                File folder = packFolder(app, pack);
                try {
                    if (!folder.isDirectory() && !folder.mkdirs()) complete = false;
                    else {
                        File stamp = new File(folder, READY_MARKER);
                        File temp = new File(folder, READY_MARKER + ".tmp");
                        try (FileOutputStream output = new FileOutputStream(temp)) {
                            output.write(("complete:" + total).getBytes("UTF-8"));
                            output.getFD().sync();
                        }
                        if (!temp.renameTo(stamp)) complete = false;
                    }
                } catch (Exception e) {
                    complete = false;
                }
            }
            if (complete && version == selectionVersion) {
                choose(app, pack);
            }
            final boolean ok = complete && isReady(pack);
            AndroidUtilities.runOnUIThread(() -> {
                InstallListener cb = callback.get();
                if (cb != null && version <= selectionVersion) {
                    cb.onComplete(ok, unsupported.get());
                }
            });
        }, "NabdhEmojiPackInstaller").start();
    }

    private static void scheduleUiRedraw() {
        synchronized (PENDING) {
            if (redrawQueued) return;
            redrawQueued = true;
        }
        AndroidUtilities.runOnUIThread(() -> {
            synchronized (PENDING) { redrawQueued = false; }
            Emoji.invalidateUiRunnable.run();
        }, 100);
    }

    private NabdhEmojiPacks() {}

    public static boolean isSupported(String id) {
        return TELEGRAM.equals(id) || SYSTEM.equals(id) || NOTO.equals(id)
                || TWEMOJI.equals(id) || OPENMOJI.equals(id);
    }

    public static String selected() {
        String pack = selected;
        if (pack == null) {
            synchronized (NabdhEmojiPacks.class) {
                pack = selected;
                if (pack == null) {
                    Context context = ApplicationLoader.applicationContext;
                    pack = context == null ? TELEGRAM :
                            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                                    .getString("pack", TELEGRAM);
                    if (!isSupported(pack) || !isReady(pack)) pack = TELEGRAM;
                    selected = pack;
                }
            }
        }
        return pack;
    }

    public static void choose(Context context, String pack) {
        if (!isSupported(pack)) throw new IllegalArgumentException("Unknown emoji pack");
        if (!isReady(pack)) throw new IllegalStateException("Emoji pack is not fully installed");
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putString("pack", pack).apply();
        selected = pack;
        synchronized (PENDING) {
            ++selectionVersion;
            redrawQueued = false;
            RETRY_AFTER.clear();
        }
        // Preserve native Telegram's setting for system vs custom spans.
        SharedConfig.useSystemEmoji = SYSTEM.equals(pack);
        SharedConfig.saveConfig();
        AndroidUtilities.runOnUIThread(() -> {
            Emoji.invalidateUiRunnable.run();
            NotificationCenter.getGlobalInstance().postNotificationName(
                    NotificationCenter.didSetNewTheme, false, false);
        });
    }

    /** Existing spans consult the current pack on every draw, so switching is live. */
    public static Emoji.EmojiDrawable wrap(CharSequence sequence, Emoji.EmojiDrawable nativeDrawable) {
        return new SwappableEmoji(sequence.toString(), nativeDrawable);
    }

    private static final class SwappableEmoji extends Emoji.EmojiDrawable {
        private final String code;
        private final Emoji.EmojiDrawable nativeDrawable;

        SwappableEmoji(String code, Emoji.EmojiDrawable original) {
            this.code = code;
            nativeDrawable = original;
        }

        @Override public void draw(Canvas canvas) {
            nativeDrawable.setBounds(getBounds());
            nativeDrawable.fullSize = fullSize;
            if (!drawPack(code, canvas, getBounds())) {
                nativeDrawable.draw(canvas);
            }
        }

        @Override public boolean isLoaded() {
            return hasCachedPack(code) || nativeDrawable.isLoaded();
        }

        @Override public void preload() {
            // Installed packs must not fetch fresh PNGs as the user scrolls.
            // Unsupported glyphs consistently use the native fallback.
            nativeDrawable.preload();
        }

        @Override public void setAlpha(int alpha) { nativeDrawable.setAlpha(alpha); }
        @Override public void setColorFilter(ColorFilter filter) {
            nativeDrawable.setColorFilter(filter);
        }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }

    private static String idFor(String code) {
        if (code == null || code.length() == 0 || code.length() > 50) return null;
        StringBuilder b = new StringBuilder();
        int points = 0;
        for (int i = 0; i < code.length();) {
            int cp = Character.codePointAt(code, i);
            i += Character.charCount(cp);
            if (cp == 0xFE0F || cp == 0xFE0E) continue;
            if (++points > 16) return null;
            if (b.length() != 0) b.append('-');
            String hex = Integer.toHexString(cp);
            for (int pad = hex.length(); pad < 4; pad++) b.append('0');
            b.append(hex);
        }
        return points == 0 ? null : b.toString();
    }

    private static String filename(String pack, String key) {
        if (NOTO.equals(pack)) return "emoji_u" + key.replace('-', '_') + ".png";
        if (TWEMOJI.equals(pack)) {
            // Twemoji uses unpadded single-byte keycaps such as 31-20e3.png.
            String[] values = key.split("-");
            StringBuilder b = new StringBuilder();
            for (String value : values) {
                if (b.length() > 0) b.append('-');
                b.append(Integer.toHexString(Integer.parseInt(value, 16)));
            }
            return b + ".png";
        }
        return key.toUpperCase(Locale.ROOT) + ".png";
    }

    private static String base(String pack) {
        return NOTO.equals(pack) ? NOTO_BASE :
               TWEMOJI.equals(pack) ? TWEMOJI_BASE : OPENMOJI_BASE;
    }

    private static String cacheKey(String pack, String code) {
        String id = idFor(code);
        return id == null ? null : pack + "_" + id;
    }

    private static Bitmap getCached(String id) {
        synchronized (MEMORY) {
            Bitmap cached = MEMORY.get(id);
            if (cached != null) return cached;
        }
        // All installed artwork is already local. Decoding a 72x72 file is
        // faster and less visually disruptive than showing a native emoji
        // followed by asynchronously replacing it as the user scrolls.
        int separator = id.indexOf('_');
        if (separator < 1) return null;
        String pack = id.substring(0, separator);
        if (!isReady(pack)) return null;
        Context context = ApplicationLoader.applicationContext;
        if (context == null) return null;
        File file = new File(packFolder(context, pack),
                filename(pack, id.substring(separator + 1)));
        if (!file.isFile()) return null;
        Bitmap bitmap = decode(file);
        if (bitmap != null) {
            synchronized (MEMORY) { MEMORY.put(id, bitmap); }
        }
        return bitmap;
    }

    private static boolean hasCachedPack(String code) {
        String pack = selected();
        if (TELEGRAM.equals(pack) || SYSTEM.equals(pack)) return false;
        String id = cacheKey(pack, code);
        return id != null && getCached(id) != null;
    }

    private static boolean drawPack(String code, Canvas canvas, Rect bounds) {
        String pack = selected();
        if (TELEGRAM.equals(pack) || SYSTEM.equals(pack)) return false;
        String id = cacheKey(pack, code);
        if (id == null) return false;
        Bitmap bitmap = getCached(id);
        if (bitmap == null) {
            // An unsupported glyph stays native. Do not start a late
            // per-glyph network request after atomic pack activation.
            return false; // Keep Telegram's native emoji visible while fetching.
        }
        synchronized (PAINT) {
            canvas.drawBitmap(bitmap, null, bounds, PAINT);
        }
        return true;
    }

    private static void requestBitmap(String code) {
        String pack = selected();
        if (TELEGRAM.equals(pack) || SYSTEM.equals(pack)) return;
        String id = cacheKey(pack, code);
        if (id == null || getCached(id) != null || !isReady(pack)) return;
        Context context = ApplicationLoader.applicationContext;
        if (context != null && new File(packFolder(context, pack),
                filename(pack, id.substring(pack.length() + 1)) + ".missing").isFile()) return;
        synchronized (PENDING) {
            Long retryAt = RETRY_AFTER.get(id);
            if (PENDING.contains(id) || (retryAt != null &&
                    SystemClock.elapsedRealtime() < retryAt)) return;
            RETRY_AFTER.remove(id);
            PENDING.add(id);
        }
        try {
            EXECUTOR.execute(() -> {
                Bitmap bitmap = null;
                boolean absent = false;
                try {
                    // Switching to Telegram must not start queued CDN work.
                    if (!pack.equals(selected())) return;
                    bitmap = loadBitmap(pack, id.substring(pack.length() + 1));
                } catch (FileNotFoundException missing) {
                    absent = true;
                } catch (Exception ignored) {
                    // Temporary network/offline errors can retry after a cooldown.
                } finally {
                    synchronized (PENDING) {
                        PENDING.remove(id);
                        if (bitmap == null) {
                            RETRY_AFTER.put(id, SystemClock.elapsedRealtime() +
                                    (absent ? MISSING_GLYPH_RETRY_MS : TEMPORARY_RETRY_MS));
                        } else {
                            RETRY_AFTER.remove(id);
                        }
                    }
                }
                if (bitmap != null && pack.equals(selected())) {
                    synchronized (MEMORY) { MEMORY.put(id, bitmap); }
                    scheduleUiRedraw();
                }
            });
        } catch (RejectedExecutionException busy) {
            synchronized (PENDING) {
                PENDING.remove(id);
                RETRY_AFTER.put(id, SystemClock.elapsedRealtime() + 3000L);
            }
        }
    }

    private static Bitmap loadBitmap(String pack, String key) throws Exception {
        Context context = ApplicationLoader.applicationContext;
        if (context == null) return null;
        // getCacheDir() may be swept by Android between app launches,
        // repeatedly triggering the expensive network-first transition.
        // Use bounded, private no-backup persistent files: survive relaunches
        // without consuming the user's cloud-backup quota.
        File folder = new File(context.getNoBackupFilesDir(), "nabdh_emoji_" + pack);
        if (!folder.exists() && !folder.mkdirs()) return null;
        File file = new File(folder, filename(pack, key));
        if (!file.isFile()) {
            File legacy = new File(new File(context.getCacheDir(),
                    "nabdh_emoji_" + pack), file.getName());
            if (legacy.isFile()) legacy.renameTo(file);
        }
        if (file.isFile()) {
            Bitmap cached = decode(file);
            if (cached != null) {
                file.setLastModified(System.currentTimeMillis());
                return cached;
            }
            file.delete();
        }
        String url = base(pack) + file.getName();
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(5500);
        connection.setReadTimeout(7000);
        connection.setRequestProperty("Accept", "image/png");
        try {
            int status = connection.getResponseCode();
            if (status == HttpURLConnection.HTTP_NOT_FOUND || status == HttpURLConnection.HTTP_GONE)
                throw new FileNotFoundException("Emoji image unavailable");
            if (status != HttpURLConnection.HTTP_OK) return null;
            if (connection.getContentLength() > MAX_IMAGE_BYTES) return null;
            ByteArrayOutputStream bytes = new ByteArrayOutputStream(8192);
            try (InputStream input = connection.getInputStream()) {
                byte[] block = new byte[8192];
                int read;
                while ((read = input.read(block)) != -1) {
                    if (bytes.size() + read > MAX_IMAGE_BYTES) return null;
                    bytes.write(block, 0, read);
                }
            }
            byte[] data = bytes.toByteArray();
            if (data.length < 24 || data[0] != (byte) 137
                    || data[1] != 80 || data[2] != 78 || data[3] != 71) return null;
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inJustDecodeBounds = true;
            BitmapFactory.decodeByteArray(data, 0, data.length, options);
            if (options.outWidth < 16 || options.outHeight < 16
                    || options.outWidth > 256 || options.outHeight > 256) return null;
            Bitmap bitmap = BitmapFactory.decodeByteArray(data, 0, data.length);
            if (bitmap == null) return null;
            // A private cache permits offline reuse after the first download.
            File temp = new File(folder, file.getName() + ".tmp");
            try (FileOutputStream stream = new FileOutputStream(temp)) {
                stream.write(data);
            }
            if (!temp.renameTo(file)) temp.delete();
            trim(folder);
            return bitmap;
        } finally {
            connection.disconnect();
        }
    }

    private static Bitmap decode(File file) {
        BitmapFactory.Options opts = new BitmapFactory.Options();
        opts.inJustDecodeBounds = true;
        BitmapFactory.decodeFile(file.getPath(), opts);
        if (opts.outWidth < 16 || opts.outHeight < 16 ||
                opts.outWidth > 256 || opts.outHeight > 256) return null;
        return BitmapFactory.decodeFile(file.getPath());
    }

    private static void trim(File folder) {
        File[] files = folder.listFiles();
        if (files == null) return;
        long bytes = 0;
        for (File file : files) if (file.isFile()) bytes += file.length();
        while (bytes > MAX_DISK_BYTES) {
            File oldest = null;
            for (File file : files) {
                if (!file.isFile()) continue;
                if (oldest == null || file.lastModified() < oldest.lastModified()) oldest = file;
            }
            if (oldest == null) break;
            bytes -= oldest.length();
            oldest.delete();
            for (int i = 0; i < files.length; i++) {
                if (files[i] == oldest) { files[i] = folder; break; }
            }
        }
    }
}
