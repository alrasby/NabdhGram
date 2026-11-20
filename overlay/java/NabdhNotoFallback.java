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

    // Both user choices now share one mixed-script family. Its Arabic
    // glyphs are controlled by the 'wdth' axis; Latin text keeps Latin metrics.
    public static Typeface createArabic(Context context, boolean bold, boolean italic) {
        return create(context, bold, italic);
    }

    // A single process-wide face per weight/slant. Do not allocate a new
    // CustomFallbackBuilder for every Settings label or chat row.
    private static final Typeface[] cachedFaces = new Typeface[4];

    public static synchronized Typeface create(Context context, boolean bold, boolean italic) {
        if (context == null) return Typeface.DEFAULT;
        final int index = (bold ? 1 : 0) | (italic ? 2 : 0);
        if (cachedFaces[index] != null) return cachedFaces[index];
        final int weight = bold ? 700 : 400;
        final int style = (bold ? Typeface.BOLD : Typeface.NORMAL)
                | (italic ? Typeface.ITALIC : Typeface.NORMAL);
        Typeface result;
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
                result = new Typeface.CustomFallbackBuilder(
                        new android.graphics.fonts.FontFamily.Builder(latin).build())
                        .addCustomFallback(new android.graphics.fonts.FontFamily.Builder(arabic).build())
                        .setSystemFallback("sans-serif")
                        .setStyle(new android.graphics.fonts.FontStyle(weight,
                                italic ? android.graphics.fonts.FontStyle.FONT_SLANT_ITALIC
                                        : android.graphics.fonts.FontStyle.FONT_SLANT_UPRIGHT))
                        .build();
            } else {
                // API 21-28 cannot build native multi-family fallbacks.
                Typeface latin = Typeface.createFromAsset(
                        context.getAssets(), "fonts/NotoSans.ttf");
                result = Typeface.create(latin, style);
            }
        } catch (java.io.IOException | RuntimeException failure) {
            result = Typeface.create("sans-serif", style);
        }
        cachedFaces[index] = result;
        return result;
    }

}
