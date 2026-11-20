package org.telegram.ui.Components;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.SharedConfig;

/** Local, presentation-only settings. Never mutates chat data or server filters. */
public final class NabdhHomePrefs {
    private static final String STORE = "nabdh_ui_personalization_v1";
    private NabdhHomePrefs() {}
    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(STORE, Context.MODE_PRIVATE);
    }
    public static boolean enabled(Context c, String key) {
        if (c == null) return false;
        // New installs prefer the native maximum JPEG resolution. A user's
        // explicit switch-off is still retained for faster 12 MP capture.
        return prefs(c).getBoolean(key, "camera_quality".equals(key));
    }
    public static void set(Context c, String key, boolean value) {
        prefs(c).edit().putBoolean(key, value).apply();
    }
    public static int folderMode(Context c) {
        return c == null ? 1 : Math.max(0, Math.min(2, prefs(c).getInt("folder_mode", 1)));
    }
    public static void setFolderMode(Context c, int mode) {
        if (mode < 0 || mode > 2) throw new IllegalArgumentException("Folder mode");
        prefs(c).edit().putInt("folder_mode", mode).apply();
    }
    /** 0: icon and name, 1: name alone (Telegram original), 2: icon alone. */
    public static String folderLabel(Context c, CharSequence original, boolean allChats, int id) {
        String name = original == null ? "" : original.toString();
        int mode = folderMode(c);
        if (mode == 1) return name;
        String[] symbols = {"📁", "💬", "⭐", "👥", "📣", "🗂"};
        String symbol = allChats ? "💬" :
                symbols[1 + ((id & Integer.MAX_VALUE) % (symbols.length - 1))];
        return mode == 2 ? symbol : symbol + " " + name;
    }
    /** Position the single main chats title outside the stories avatars. */
    public static void applyTitle(org.telegram.ui.ActionBar.ActionBar bar, Context context) {
        if (bar == null || context == null) return;
        final org.telegram.ui.ActionBar.SimpleTextView title = bar.getTitleTextView();
        if (title == null) return;
        if (bar.getWidth() <= 0 || title.getWidth() <= 0) {
            // Initial layout is asynchronous. This is only a one-off deferral:
            // do not post repeatedly on every stories animation frame.
            return;
        }
        final float dp = context.getResources().getDisplayMetrics().density;
        final boolean center = enabled(context, "center_title");
        final float safeStart = 72f * dp;
        final float safeEnd = 56f * dp;
        final float textWidth = title.getWidth();
        final float target = center
                ? Math.max(safeStart, Math.min((bar.getWidth() - textWidth) * 0.5f,
                        bar.getWidth() - textWidth - safeEnd))
                : safeStart;
        // Convert the desired ActionBar-local position into the title view's
        // own coordinates, accounting for parent layout and translations.
        // Resetting translation to zero exposed the first characters behind
        // the two stories avatars when their collapsed row was visible.
        float origin = title.getLeft();
        android.view.ViewParent parent = title.getParent();
        while (parent instanceof android.view.View && parent != bar) {
            android.view.View p = (android.view.View) parent;
            origin += p.getLeft() + p.getTranslationX();
            parent = p.getParent();
        }
        final float translation = target - origin;
        if (Math.abs(title.getTranslationX() - translation) > 0.5f) {
            title.setTranslationX(translation);
        }
    }
    /** Requested recording rate; Camera2 chooses a hardware-supported range. */
    public static int videoFps(Context c) {
        int fps = c.getSharedPreferences(STORE, Context.MODE_PRIVATE)
                .getInt("video_fps", 30);
        return fps == 24 || fps == 60 ? fps : 30;
    }
    public static void setVideoFps(Context c, int fps) {
        if (fps != 24 && fps != 30 && fps != 60)
            throw new IllegalArgumentException("Video FPS");
        prefs(c).edit().putInt("video_fps", fps).apply();
    }
    public static int bubbleRadius(Context c) {
        return Math.max(10, Math.min(25, prefs(c).getInt("bubble_radius", 19)));
    }
    public static void setBubbleRadius(Context c, int radius) {
        if (radius < 10 || radius > 25) throw new IllegalArgumentException("Bubble radius");
        prefs(c).edit().putInt("bubble_radius", radius).apply();
        SharedConfig.bubbleRadius = radius;
        // Telegram itself restores this preference from mainconfig.
        c.getSharedPreferences("mainconfig", Context.MODE_PRIVATE)
                .edit().putInt("bubbleRadius", radius).commit();
    }
}
