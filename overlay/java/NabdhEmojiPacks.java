package org.telegram.messenger;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.util.LruCache;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashSet;
import java.util.Set;

/**
 * Built-in Twemoji 17.0.3 artwork (CC BY 4.0), pinned to jdecked/twemoji
 * b6b55fef1e8636b540a6d016a4729ca8cdf2e60b.
 *
 * All assets ship inside the APK; NO runtime network, asynchronous icon
 * substitution, per-page downloads or extra storage permissions. Original
 * Telegram and platform emoji remain independent selectable modes.
 */
public final class NabdhEmojiPacks {
    public static final String TELEGRAM = "telegram";
    public static final String SYSTEM = "system";
    public static final String TWEMOJI = "twemoji";

    private static final String PREFS = "nabdhgram_emoji_packs_v1";
    private static final String ASSET_ROOT = "nabdh_twemoji/72x72/";
    private static final LruCache<String, Bitmap> MEMORY = new LruCache<String, Bitmap>(6 * 1024 * 1024) {
        @Override protected int sizeOf(String key, Bitmap bitmap) {
            return bitmap.getByteCount();
        }
    };
    private static final Set<String> ABSENT = new HashSet<>();
    private static final Paint PAINT = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private static volatile String selected;

    private NabdhEmojiPacks() {}

    public static boolean isSupported(String pack) {
        return TELEGRAM.equals(pack) || SYSTEM.equals(pack) || TWEMOJI.equals(pack);
    }

    public static boolean isReady(String pack) {
        if (TELEGRAM.equals(pack) || SYSTEM.equals(pack)) return true;
        if (!TWEMOJI.equals(pack)) return false;
        Context context = ApplicationLoader.applicationContext;
        if (context == null) return false;
        try (InputStream input = context.getAssets().open(ASSET_ROOT + "1f600.png")) {
            return input.read() >= 0;
        } catch (IOException error) {
            return false;
        }
    }

    public static String selected() {
        String pack = selected;
        if (pack == null) {
            synchronized (NabdhEmojiPacks.class) {
                pack = selected;
                if (pack == null) {
                    Context context = ApplicationLoader.applicationContext;
                    pack = context == null ? TELEGRAM
                            : context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                                     .getString("pack", TELEGRAM);
                    // Migrate discontinued Noto/OpenMoji preferences safely.
                    if (!isSupported(pack) || !isReady(pack)) pack = TELEGRAM;
                    selected = pack;
                }
            }
        }
        return pack;
    }

    public static void choose(Context context, String pack) {
        if (!isSupported(pack)) throw new IllegalArgumentException("Unknown emoji pack");
        if (!isReady(pack)) throw new IllegalStateException("Bundled Twemoji assets missing");
        if (pack.equals(selected())) return;
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString("pack", pack).apply();
        selected = pack;
        SharedConfig.useSystemEmoji = SYSTEM.equals(pack);
        SharedConfig.saveConfig();
        AndroidUtilities.runOnUIThread(() -> {
            Emoji.invalidateUiRunnable.run();
            NotificationCenter.getGlobalInstance().postNotificationName(
                    NotificationCenter.didSetNewTheme, false, false);
        });
    }

    private static String filename(CharSequence code) {
        if (code == null || code.length() == 0 || code.length() > 50) return null;
        StringBuilder file = new StringBuilder();
        int count = 0;
        for (int i = 0; i < code.length();) {
            int cp = Character.codePointAt(code, i);
            i += Character.charCount(cp);
            if (cp == 0xFE0F || cp == 0xFE0E) continue; // Twemoji filename convention.
            if (++count > 16) return null;
            if (file.length() > 0) file.append('-');
            file.append(Integer.toHexString(cp));
        }
        return count == 0 ? null : file.append(".png").toString();
    }

    private static Bitmap getBundled(CharSequence code) {
        String file = filename(code);
        if (file == null) return null;
        synchronized (MEMORY) {
            Bitmap bitmap = MEMORY.get(file);
            if (bitmap != null) return bitmap;
        }
        synchronized (ABSENT) {
            if (ABSENT.contains(file)) return null;
        }
        Context context = ApplicationLoader.applicationContext;
        if (context == null) return null;
        Bitmap bitmap;
        try (InputStream input = context.getAssets().open(ASSET_ROOT + file)) {
            bitmap = BitmapFactory.decodeStream(input);
        } catch (IOException error) {
            bitmap = null;
        }
        if (bitmap == null) {
            synchronized (ABSENT) {
                if (ABSENT.size() >= 4096) ABSENT.clear();
                ABSENT.add(file);
            }
            return null;
        }
        synchronized (MEMORY) {
            MEMORY.put(file, bitmap);
        }
        return bitmap;
    }

    /** Wrap static Telegram emoji without interfering with custom/animated emoji. */
    public static Emoji.EmojiDrawable wrap(CharSequence sequence, Emoji.EmojiDrawable nativeDrawable) {
        return new BundledEmoji(sequence.toString(), nativeDrawable);
    }

    private static final class BundledEmoji extends Emoji.EmojiDrawable {
        private final String code;
        private final Emoji.EmojiDrawable nativeDrawable;
        private int alpha = 255;
        private ColorFilter filter;

        BundledEmoji(String code, Emoji.EmojiDrawable original) {
            this.code = code;
            this.nativeDrawable = original;
        }

        @Override public void draw(Canvas canvas) {
            nativeDrawable.setBounds(getBounds());
            nativeDrawable.fullSize = fullSize;
            if (!TWEMOJI.equals(selected())) {
                nativeDrawable.draw(canvas);
                return;
            }
            Bitmap bitmap = getBundled(code);
            if (bitmap == null) {
                // Unavailable composite glyphs retain a stable native fallback.
                nativeDrawable.draw(canvas);
                return;
            }
            Rect bounds = getBounds();
            synchronized (PAINT) {
                PAINT.setAlpha(alpha);
                PAINT.setColorFilter(filter);
                canvas.drawBitmap(bitmap, null, bounds, PAINT);
            }
        }

        @Override public boolean isLoaded() {
            return TWEMOJI.equals(selected()) ? getBundled(code) != null
                    || nativeDrawable.isLoaded() : nativeDrawable.isLoaded();
        }

        @Override public void preload() { nativeDrawable.preload(); }
        @Override public void setAlpha(int value) {
            alpha = value;
            nativeDrawable.setAlpha(value);
        }
        @Override public void setColorFilter(ColorFilter value) {
            filter = value;
            nativeDrawable.setColorFilter(value);
        }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
