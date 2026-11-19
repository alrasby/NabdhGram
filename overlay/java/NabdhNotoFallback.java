package org.telegram.messenger;

import android.content.Context;
import android.graphics.Typeface;
import android.os.Build;

/**
 * One cached typeface family for mixed-script messages when Noto Sans is selected.
 *
 * Android 10+ (API 29): explicit Noto Sans Latin/Greek/Cyrillic -> Noto Sans
 * Arabic -> platform family fallback (CJK, Indic, Thai, emoji, etc.).
 * On earlier Android versions, rely on the platform's native glyph fallback
 * instead of using spans that would corrupt Telegram entity/emoji styling.
 *
 * No network access, no global configuration changes and no text mutation.
 */
public final class NabdhNotoFallback {
    private NabdhNotoFallback() {}

    // Noto Sans Arabic is a variable-width font. A moderately condensed
    // native width avoids the excessively loose Arabic appearance while
    // retaining its OpenType shaping, ligatures and standard letter spacing.
    private static final float ARABIC_WIDTH = 87.5f;

    public static Typeface createArabic(Context context, boolean bold, boolean italic) {
        // A lone NotoSansArabic Typeface applies Arabic vertical metrics to
        // Latin UI copy as well, producing oversized line gaps in Settings.
        // Put Noto Sans Latin first and the user-selected compact Arabic face
        // second. This keeps Arabic shaping intact without changing text size.
        if (context == null) return Typeface.DEFAULT;
        final int weight = bold ? 700 : 400;
        final int style = (bold ? Typeface.BOLD : Typeface.NORMAL)
                | (italic ? Typeface.ITALIC : Typeface.NORMAL);
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                android.content.res.AssetManager assets = context.getAssets();
                android.graphics.fonts.Font latin = new android.graphics.fonts.Font.Builder(
                        assets, "fonts/NotoSans.ttf")
                        .setFontVariationSettings("'wght' " + weight)
                        .setWeight(weight).build();
                android.graphics.fonts.Font arabic = new android.graphics.fonts.Font.Builder(
                        assets, "fonts/NotoSansArabic.ttf")
                        .setFontVariationSettings("'wdth' " + ARABIC_WIDTH + ", 'wght' " + weight)
                        .setWeight(weight).build();
                return new Typeface.CustomFallbackBuilder(
                        new android.graphics.fonts.FontFamily.Builder(latin).build())
                        .addCustomFallback(new android.graphics.fonts.FontFamily.Builder(arabic).build())
                        .setSystemFallback("sans-serif")
                        .setStyle(new android.graphics.fonts.FontStyle(weight,
                                italic ? android.graphics.fonts.FontStyle.FONT_SLANT_ITALIC
                                        : android.graphics.fonts.FontStyle.FONT_SLANT_UPRIGHT))
                        .build();
            }
            // A custom multi-family fallback is unavailable before Android 10.
            // Prefer consistent Latin text metrics over the incorrect all-script
            // Arabic font metrics; Android supplies native Arabic fallback.
            Typeface latin = Typeface.createFromAsset(context.getAssets(), "fonts/NotoSans.ttf");
            return Typeface.create(latin, style);
        } catch (java.io.IOException | RuntimeException failure) {
            return Typeface.create("sans-serif", style);
        }
    }

    public static Typeface create(Context context, boolean bold, boolean italic) {
        if (context == null) {
            return Typeface.DEFAULT;
        }
        final int weight = bold ? 700 : 400;
        final int style = (bold ? Typeface.BOLD : Typeface.NORMAL)
                | (italic ? Typeface.ITALIC : Typeface.NORMAL);
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                android.content.res.AssetManager assets = context.getAssets();
                android.graphics.fonts.Font latin = new android.graphics.fonts.Font.Builder(
                        assets, "fonts/NotoSans.ttf")
                        .setFontVariationSettings("'wght' " + weight)
                        .setWeight(weight)
                        .build();
                android.graphics.fonts.Font arabic = new android.graphics.fonts.Font.Builder(
                        assets, "fonts/NotoSansArabic.ttf")
                        .setFontVariationSettings("'wdth' " + ARABIC_WIDTH + ", 'wght' " + weight)
                        .setWeight(weight)
                        .build();
                android.graphics.fonts.FontFamily primary =
                        new android.graphics.fonts.FontFamily.Builder(latin).build();
                android.graphics.fonts.FontFamily arabicFallback =
                        new android.graphics.fonts.FontFamily.Builder(arabic).build();
                return new Typeface.CustomFallbackBuilder(primary)
                        .addCustomFallback(arabicFallback)
                        .setSystemFallback("sans-serif")
                        .setStyle(new android.graphics.fonts.FontStyle(weight,
                                italic
                                        ? android.graphics.fonts.FontStyle.FONT_SLANT_ITALIC
                                        : android.graphics.fonts.FontStyle.FONT_SLANT_UPRIGHT))
                        .build();
            }
            // API 21-28: CustomFallbackBuilder is unavailable. Android's native
            // sans-serif fallback still displays Arabic and other unsupported
            // scripts, though it may not use the bundled Noto Arabic face.
            Typeface latin = Typeface.createFromAsset(
                    context.getAssets(), "fonts/NotoSans.ttf");
            return Typeface.create(latin, style);
        } catch (java.io.IOException | RuntimeException failure) {
            // An unavailable/corrupt asset must never crash the app or login UI.
            // Keep system script coverage intact with native Android fallback.
            return Typeface.create("sans-serif", style);
        }
    }
}
