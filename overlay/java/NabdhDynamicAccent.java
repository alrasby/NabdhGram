package org.telegram.ui.Components;

import android.content.Context;
import android.content.res.Resources;
import android.graphics.Color;
import android.os.Build;
import org.telegram.ui.ActionBar.Theme;

/** Android 12+ user-chosen wallpaper accent for NabdhGram Settings only. */
public final class NabdhDynamicAccent {
    private NabdhDynamicAccent() {}
    public static boolean available(Context ctx) {
        return Build.VERSION.SDK_INT >= 31
                && ctx.getResources().getIdentifier("system_accent1_600", "color", "android") != 0;
    }
    public static boolean enabled(Context ctx) {
        return available(ctx) && ctx.getApplicationContext()
                .getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
                .getBoolean("monet_enabled", false);
    }
    public static void setEnabled(Context ctx, boolean enabled) {
        ctx.getApplicationContext().getSharedPreferences(
                "nabdhgram_appearance", Context.MODE_PRIVATE).edit()
                .putBoolean("monet_enabled", enabled && available(ctx)).apply();
    }
    private static double channel(int x) {
        double c = x / 255.0;
        return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    }
    private static double luminance(int color) {
        return channel(Color.red(color)) * 0.2126
             + channel(Color.green(color)) * 0.7152
             + channel(Color.blue(color)) * 0.0722;
    }
    private static boolean readable(int color, int bg) {
        double a = luminance(color), b = luminance(bg);
        return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) >= 4.5;
    }
    public static int accent(Context ctx, int fallback) {
        if (!enabled(ctx)) return fallback;
        try {
            boolean dark = Theme.isCurrentThemeDark();
            String resName = dark ? "system_accent1_200" : "system_accent1_600";
            Resources res = ctx.getResources();
            int id = res.getIdentifier(resName, "color", "android");
            if (id == 0) return fallback;
            int candidate = ctx.getColor(id);
            int surface = Theme.getColor(Theme.key_windowBackgroundWhite);
            return readable(candidate, surface) ? candidate : fallback;
        } catch (Resources.NotFoundException error) {
            return fallback;
        }
    }
}
