#!/usr/bin/env python3
"""Use the native Telegram bubble geometry for theme-aware text and media edges.

This leaves selection, theme previews, media content and message grouping intact.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-bubble-outline.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/MessageDrawable.java"
s = p.read_text(encoding="utf-8")
field_anchor = "    private int currentBackgroundHeight;\n"
if s.count(field_anchor) != 1:
    raise SystemExit("MessageDrawable field anchor changed")
s = s.replace(field_anchor, field_anchor + """    private final Paint nabdhBubbleEdge = new Paint(Paint.ANTI_ALIAS_FLAG);
    // Cached brushes: no allocation of gradients or bitmaps per message draw.
    private final Paint nabdhCrystalTint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint nabdhCrystalRim = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF nabdhCrystalBounds = new RectF();
    private final Paint nabdhFrostPaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final Matrix nabdhFrostMatrix = new Matrix();
    private final float[] nabdhFrostValues = new float[9];
    private final RectF nabdhFrostDestination = new RectF();
    private static java.lang.ref.WeakReference<Drawable> nabdhLastWallpaper;
    private static Bitmap nabdhBlurredWallpaper;
    private static int nabdhBackdropWidth, nabdhBackdropHeight;
    private static int nabdhBackdropTheme, nabdhBackdropOrientation;
""" , 1)
# Use a low-resolution cached blur. The backing drawable may belong to the
# active chat (chat-specific theme), not to the global theme.
helper_anchor = "    protected int getColor(int key) {"
helper = """    // A quiet polished edge and translucent wash, clipped to Telegram's
    // exact native bubble path. Keep the original shape, tail and hit target.
    // Only regular text bubbles: media, selection and theme editor are native.
    private void nabdhDrawCrystalSurface(Canvas canvas, Path bubblePath) {
        if (currentType != TYPE_TEXT || themePreview || isSelected
                || crossfadeFromDrawable != null) return;
        final int accent = getColor(Theme.key_windowBackgroundWhiteBlueText);
        final int base = getColor(isOut
                ? Theme.key_chat_outBubble : Theme.key_chat_inBubble);
        final int tintedR = (Color.red(base) * 60 + Color.red(accent) * 40) / 100;
        final int tintedG = (Color.green(base) * 60 + Color.green(accent) * 40) / 100;
        final int tintedB = (Color.blue(base) * 60 + Color.blue(accent) * 40) / 100;
        nabdhCrystalTint.setStyle(Paint.Style.FILL);
        nabdhCrystalTint.setColor(Color.argb((isOut ? 22 : 16) * alpha / 255,
                tintedR, tintedG, tintedB));
        canvas.drawPath(bubblePath, nabdhCrystalTint);
        nabdhCrystalRim.setStyle(Paint.Style.STROKE);
        nabdhCrystalRim.setStrokeWidth(AndroidUtilities.dpf2(0.85f));
        nabdhCrystalRim.setColor(Color.argb(94 * alpha / 255,
                Math.max(tintedR, 90), Math.max(tintedG, 120), Math.max(tintedB, 120)));
        canvas.drawPath(bubblePath, nabdhCrystalRim);
        // Concentrate the specular highlight on the actual upper rim.
        // No offscreen layers or fresh Path/Bitmap objects in onDraw().
        bubblePath.computeBounds(nabdhCrystalBounds, true);
        canvas.save();
        canvas.clipRect(nabdhCrystalBounds.left, nabdhCrystalBounds.top,
                nabdhCrystalBounds.right,
                nabdhCrystalBounds.top + AndroidUtilities.dp(14));
        nabdhCrystalRim.setColor(Color.argb(64 * alpha / 255, 245, 255, 255));
        canvas.drawPath(bubblePath, nabdhCrystalRim);
        canvas.restore();
    }

    private static synchronized Bitmap nabdhGetBlurredWallpaper(Drawable wallpaper) {
        if (wallpaper == null || wallpaper instanceof MotionBackgroundDrawable
                || wallpaper instanceof android.graphics.drawable.ColorDrawable) {
            // Animated backgrounds need live capture; a stale bitmap is wrong.
            return null;
        }
        final int screenW = Math.max(1, AndroidUtilities.displaySize.x);
        final int screenH = Math.max(1, AndroidUtilities.displaySize.y);
        final int width = 96;
        final int height = Math.max(1, Math.round(width * (float) screenH / screenW));
        final int themeColor = Theme.getColor(Theme.key_chat_wallpaper);
        final int orientation = screenW > screenH ? 1 : 0;
        if (nabdhLastWallpaper != null && nabdhLastWallpaper.get() == wallpaper
                && nabdhBlurredWallpaper != null && !nabdhBlurredWallpaper.isRecycled()
                && nabdhBackdropWidth == width && nabdhBackdropHeight == height
                && nabdhBackdropTheme == themeColor
                && nabdhBackdropOrientation == orientation) {
            return nabdhBlurredWallpaper;
        }
        // Cache a genuinely blurred bitmap; NEVER blur each visible message.
        try {
            Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
            android.graphics.Rect original = new android.graphics.Rect(wallpaper.getBounds());
            try {
                wallpaper.setBounds(0, 0, width, height);
                wallpaper.draw(new Canvas(bitmap));
            } finally {
                wallpaper.setBounds(original);
            }
            org.telegram.messenger.Utilities.stackBlurBitmap(bitmap, 7);
            nabdhBlurredWallpaper = bitmap;
            nabdhLastWallpaper = new java.lang.ref.WeakReference<>(wallpaper);
            nabdhBackdropWidth = width;
            nabdhBackdropHeight = height;
            nabdhBackdropTheme = themeColor;
            nabdhBackdropOrientation = orientation;
            return bitmap;
        } catch (RuntimeException | OutOfMemoryError ignored) {
            // Preserve native bubbles if the wallpaper cannot be sampled.
            return null;
        }
    }

    private void nabdhDrawFrostedWallpaper(Canvas canvas, Path bubblePath) {
        Drawable wallpaper = resourcesProvider instanceof org.telegram.ui.ChatActivity.ThemeDelegate
                ? ((org.telegram.ui.ChatActivity.ThemeDelegate) resourcesProvider).getWallpaperDrawable()
                : Theme.getCachedWallpaperNonBlocking();
        if (wallpaper == null) {
            wallpaper = Theme.getCachedWallpaperNonBlocking();
        }
        Bitmap blurred = nabdhGetBlurredWallpaper(wallpaper);
        if (blurred == null) return;
        // Respect the current bubble canvas translation/scale so the same
        // wallpaper bitmap is sampled consistently across recycled cells.
        canvas.getMatrix(nabdhFrostMatrix);
        nabdhFrostMatrix.getValues(nabdhFrostValues);
        float scaleX = nabdhFrostValues[Matrix.MSCALE_X];
        float scaleY = nabdhFrostValues[Matrix.MSCALE_Y];
        if (Math.abs(scaleX) < 0.01f || Math.abs(scaleY) < 0.01f) return;
        float left = -nabdhFrostValues[Matrix.MTRANS_X] / scaleX;
        float top = -nabdhFrostValues[Matrix.MTRANS_Y] / scaleY;
        nabdhFrostDestination.set(left, top,
                left + AndroidUtilities.displaySize.x / Math.abs(scaleX),
                top + AndroidUtilities.displaySize.y / Math.abs(scaleY));
        canvas.save();
        canvas.clipPath(bubblePath);
        canvas.drawBitmap(blurred, null, nabdhFrostDestination, nabdhFrostPaint);
        canvas.restore();
    }

"""
if s.count(helper_anchor) != 1:
    raise SystemExit("Native MessageDrawable color helper anchor changed")
s = s.replace(helper_anchor, helper + helper_anchor, 1)
anchor = """        canvas.drawPath(path, p);
        if (gradientShader != null && isSelected && paintToUse == null) {"""
replacement = """        // Draw the native bubble path with a bounded translucent fill for
        // unselected text. Preserve the original theme hue, wallpaper, native
        // geometry, selected states and media bubbles.
        final boolean nabdhFrostedText = paintToUse == null
                && currentType == TYPE_TEXT && !themePreview && !isSelected
                && crossfadeFromDrawable == null;
        final int nabdhOriginalPaintAlpha = p.getAlpha();
        if (nabdhFrostedText) {
            nabdhDrawFrostedWallpaper(canvas, path);
            p.setAlpha(nabdhOriginalPaintAlpha * 184 / 255);
        }
        canvas.drawPath(path, p);
        if (nabdhFrostedText) {
            p.setAlpha(nabdhOriginalPaintAlpha);
        }
        // NabdhGram Glass: outline gradient text and media bubbles using the
        // existing Telegram shape, preserving grouping and tail geometry.
        if (paintToUse == null && gradientShader != null
                && (currentType == TYPE_TEXT || currentType == TYPE_MEDIA) && !themePreview && !isSelected) {
            nabdhBubbleEdge.setStyle(Paint.Style.STROKE);
            nabdhBubbleEdge.setStrokeWidth(dp(1));
            // Respect the active theme's in/out shadow hue, including user
            // imported .attheme files. Avoid fixed turquoise or white.
            int stroke = getColor(isOut
                    ? Theme.key_chat_outBubbleShadow : Theme.key_chat_inBubbleShadow);
            if (Color.alpha(stroke) < 30) {
                stroke = getColor(Theme.key_chat_messagePanelText);
            }
            nabdhBubbleEdge.setColor(stroke);
            nabdhBubbleEdge.setAlpha((int) (122f * alpha / 255f));
            canvas.drawPath(path, nabdhBubbleEdge);
        }
        if (nabdhFrostedText) {
            nabdhDrawCrystalSurface(canvas, path);
        }
        if (gradientShader != null && isSelected && paintToUse == null) {"""
if s.count(anchor) != 1:
    raise SystemExit("MessageDrawable gradient draw anchor changed")
s = s.replace(anchor, replacement, 1)
# The upstream renderer returns early for ordinary solid-color text bubbles.
# Without this branch, only gradient bubbles ever show a Glass outline.
cached = """                background.setBounds(bounds);
                background.draw(canvas);
                return;"""
if s.count(cached) != 1:
    raise SystemExit("Cached Telegram bubble drawing branch changed")
cached_stroke = """                background.setBounds(bounds);
                // The normal solid-text path uses a cached NinePatch rather
                // than canvas.drawPath. Apply the same bounded translucency
                // here, then restore the shared drawable alpha immediately.
                // Do not alter selected, preview or media backgrounds.
                final boolean nabdhFrostedText = currentType == TYPE_TEXT
                        && !themePreview && !isSelected && crossfadeFromDrawable == null;
                final int nabdhOriginalAlpha = background.getAlpha();
                if (nabdhFrostedText) {
                    nabdhDrawFrostedWallpaper(canvas, makePath());
                    background.setAlpha(nabdhOriginalAlpha * 184 / 255);
                }
                background.draw(canvas);
                if (nabdhFrostedText) {
                    background.setAlpha(nabdhOriginalAlpha);
                }
                if ((currentType == TYPE_TEXT || currentType == TYPE_MEDIA) && !themePreview && !isSelected) {
                    int stroke = getColor(isOut
                            ? Theme.key_chat_outBubbleShadow : Theme.key_chat_inBubbleShadow);
                    if (Color.alpha(stroke) < 30) {
                        stroke = getColor(Theme.key_chat_messagePanelText);
                    }
                    nabdhBubbleEdge.setStyle(Paint.Style.STROKE);
                    nabdhBubbleEdge.setStrokeWidth(dp(0.8f));
                    nabdhBubbleEdge.setColor(stroke);
                    nabdhBubbleEdge.setAlpha((int) (53f * alpha / 255f));
                    canvas.drawPath(makePath(), nabdhBubbleEdge);
                }
                if (nabdhFrostedText) {
                    nabdhDrawCrystalSurface(canvas, makePath());
                }
                return;"""
s = s.replace(cached, cached_stroke, 1)
p.write_text(s, encoding="utf-8")
print("Glass text/media bubble outlines applied using native Telegram paths.")
