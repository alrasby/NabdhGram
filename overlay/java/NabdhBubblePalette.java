package org.telegram.ui.Components;

/**
 * Shared, deterministic alpha/contrast policy for Telegram's native
 * MessageDrawable TYPE_TEXT and TYPE_MEDIA variants.
 *
 * No camera/image analysis, network, ML inference, allocations or shader
 * work in the draw path. Imported theme colors and native text contrast
 * remain authoritative; the policy only adjusts bubble translucency.
 */
public final class NabdhBubblePalette {
    private NabdhBubblePalette() {}

    private static int lightness(int color) {
        // Integer luma is fast enough to use while scrolling.
        return (299 * android.graphics.Color.red(color)
                + 587 * android.graphics.Color.green(color)
                + 114 * android.graphics.Color.blue(color)) / 1000;
    }

    public static int edgeAlpha(int style, int drawableAlpha) {
        int strength = style == NabdhGlassStyle.SOFT ? 85 :
                       style == NabdhGlassStyle.CRYSTAL ? 157 : 122;
        return Math.max(0, Math.min(255, strength * drawableAlpha / 255));
    }

    public static int backgroundAlpha(int style, int bubbleColor,
                                      int wallpaperColor, boolean media) {
        int opacity = style == NabdhGlassStyle.SOFT ? 226 :
                      style == NabdhGlassStyle.CRYSTAL ? 200 : 213;
        int separation = Math.abs(lightness(bubbleColor) - lightness(wallpaperColor));
        // Protect readable text on similar-toned themes; media often has
        // smaller file metadata, so apply the same or stronger minimum.
        if (separation < 34) opacity += 18;
        if (media) opacity = Math.max(opacity, 213);
        return Math.max(195, Math.min(245, opacity));
    }
}
