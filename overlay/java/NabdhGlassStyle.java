package org.telegram.ui.Components;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.ApplicationLoader;

/**
 * Single lightweight, opt-in visual preference for Telegram's native
 * MessageDrawable; no Compose hierarchy, network, timers or GPU readback.
 */
public final class NabdhGlassStyle {
    public static final int SOFT = 0;
    public static final int LIQUID = 1;
    public static final int CRYSTAL = 2;
    private static volatile int cachedStyle = -1;

    private NabdhGlassStyle() {}

    public static int current() {
        int style = cachedStyle;
        if (style < 0) {
            Context app = ApplicationLoader.applicationContext;
            style = app == null ? LIQUID :
                app.getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
                   .getInt("bubble_glass_style", LIQUID);
            style = Math.max(SOFT, Math.min(CRYSTAL, style));
            cachedStyle = style;
        }
        return style;
    }

    public static void choose(Context context, int requested) {
        int style = Math.max(SOFT, Math.min(CRYSTAL, requested));
        context.getApplicationContext()
            .getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
            .edit().putInt("bubble_glass_style", style).apply();
        cachedStyle = style;
    }

    public static boolean lensEnabled(Context context) {
        return context.getApplicationContext()
            .getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
            .getBoolean("lens_enabled", true);
    }

    public static void setLensEnabled(Context context, boolean enabled) {
        context.getApplicationContext()
            .getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
            .edit().putBoolean("lens_enabled", enabled).apply();
    }
}
