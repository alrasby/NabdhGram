#!/usr/bin/env python3
"""Brand Telegram's OWN two mutually animated title slots, without overlays.

Keep upstream layout, alpha/scale/position, premium status and proxy handling.
No forced title visibility, resume rebinding or stories layout translations.
"""
from pathlib import Path
import sys

def once(src, old, new, label):
    actual = src.count(old)
    if actual != 1:
        raise SystemExit(f"Pinned Telegram {label} changed: expected 1, got {actual}")
    return src.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-dialogs-title.py TELEGRAM_SOURCE")
    ui = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram/ui"
    dialogs = ui / "DialogsActivity.java"
    d = dialogs.read_text(encoding="utf-8")
    # The native ActionBar has a text view and a Telegram-logo ImageSpan;
    # eliminate that span, keep the native title setter/status slot intact.
    d = once(d, """                SpannableStringBuilder ssb = new SpannableStringBuilder(getString(R.string.AppName));
                ssb.setSpan(new ImageSpan(logoDrawable), 0, ssb.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                actionBar.setTitle(ssb, statusDrawable);""",
             """                actionBar.setTitle("NabdhGram", statusDrawable);""",
             "native dialogs ActionBar title")
    # Keep the native main-header title at full text scale while preserving
    # upstream alpha, translation and visibility transitions. The original
    # native logo was artwork, but NabdhGram is legible text and must not
    # inherit its shrink-to-40%-size animation.
    # No extra View or independent overlay may compete for ownership.
    # Restrict the exception to the main chats title only.

    d = once(d,
         "            float s = 0.4f + 0.6f * containersAlpha;",
         """            float s = (initialDialogsType == DIALOGS_TYPE_DEFAULT && !onlySelect
                    && folderId == 0 && communityId == 0)
                    ? 1.0f
                    : 0.4f + 0.6f * containersAlpha;""",
         "native main header title scale floor")
    dialogs.write_text(d, encoding="utf-8")

    # Preserve Telegram's ORIGINAL ImageView type, native
    # translation, visibility, alpha and scale. The previous TextView with
    # WRAP_CONTENT changed its geometry and was clipped during transitions.
    # Only substitute the image's *content*, with a drawable that renders
    # the wordmark in the same animated slot at its text-appropriate width.
    stories = ui / "Stories/DialogStoriesCell.java"
    s = stories.read_text(encoding="utf-8")
    # The original logo ImageView was allowed to shrink into a tiny emblem.
    # The text replacement must stay readable even when Telegram changes
    # scaleX/scaleY during a stories-to-toolbar transition. Keep this within
    # the same native slot rather than creating a competing overlay.
    s = once(s,
         "telegramLogoView = new ImageView(context);",
         "telegramLogoView = new NabdhStableWordmarkView(context);",
         "native stories logo view constructor")
    s = once(s,
         "        telegramLogoView.setImageResource(R.drawable.telegram_logo_2);",
         "        telegramLogoView.setImageDrawable(new NabdhNativeWordmarkDrawable());",
         "native ImageView image source")
    # Telegram's 90dp logo was artwork, not a ten-letter word. The old code
    # compressed 19sp NabdhGram into 90dp, then native stories animation could
    # shrink its container to 40%, producing the microscopic title on screen.
    # Give the SAME native ImageView enough intrinsic width (no new view).
    s = once(s,
         "addView(telegramLogoView, LayoutHelper.createFrame(90, 22));",
         "addView(telegramLogoView, LayoutHelper.createFrame(132, 22));",
         "native wordmark width for longer app name")
    # The layout still owns the ImageView and all visibility/translation.
    # Only protect the text glyphs against native logo-only shrink animation.
    # The native logo Drawable is scaled a second time by ImageView's image
    # matrix (CENTER_INSIDE), and can collapse to a microscopic glyph when the
    # title slots switch. Draw the wordmark directly in the existing measured
    # view: no intrinsic-size matrix, no duplicate overlay or extra animation.
    logo_view_impl = """    private final class NabdhStableWordmarkView extends ImageView {
        private final android.graphics.Paint wordmarkPaint =
                new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        NabdhStableWordmarkView(android.content.Context context) {
            super(context);
            wordmarkPaint.setTypeface(android.graphics.Typeface.create(
                    "sans-serif", android.graphics.Typeface.BOLD));
            wordmarkPaint.setTextSize(AndroidUtilities.dp(19));
            wordmarkPaint.setColor(android.graphics.Color.WHITE);
            setScaleType(ImageView.ScaleType.FIT_XY);
        }
        @Override protected void onDraw(android.graphics.Canvas canvas) {
            if (getWidth() <= 0 || getHeight() <= 0) return;
            wordmarkPaint.setTextSize(AndroidUtilities.dp(19));
            wordmarkPaint.setColor(getTextLogoColor());
            android.graphics.Paint.FontMetrics fm = wordmarkPaint.getFontMetrics();
            float baseline = (getHeight() - fm.ascent - fm.descent) / 2f;
            canvas.drawText("NabdhGram", 0f, baseline, wordmarkPaint);
        }
        @Override public void setScaleX(float value) {
            super.setScaleX(1f);
        }
        @Override public void setScaleY(float value) {
            super.setScaleY(1f);
        }
    }

"""
    marker = "    ImageView telegramLogoView;"
    if s.count(marker) != 1:
        raise SystemExit("Pinned stories logo field changed")
    impl = """    // Exact native Telegram image slot; no extra View, no separate animation.
    private static final class NabdhNativeWordmarkDrawable extends android.graphics.drawable.Drawable {
        private final android.graphics.Paint textPaint =
                new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        private final String wordmark = "NabdhGram";
        NabdhNativeWordmarkDrawable() {
            textPaint.setTypeface(android.graphics.Typeface.create(
                    "sans-serif", android.graphics.Typeface.BOLD));
            textPaint.setTextSize(AndroidUtilities.dp(19));
            textPaint.setColor(android.graphics.Color.WHITE);
        }
        @Override public void draw(android.graphics.Canvas canvas) {
            android.graphics.Rect bounds = getBounds();
            float naturalWidth = textPaint.measureText(wordmark);
            if (naturalWidth <= 0 || bounds.width() <= 0 || bounds.height() <= 0) return;
            // Fit the word inside the existing animated ImageView so it
            // never draws over the stories avatars, action buttons or status.
            float fitScale = Math.min(1f, bounds.width() / naturalWidth);
            float baseline = -0.5f * (textPaint.ascent() + textPaint.descent());
            canvas.save();
            canvas.translate(bounds.left, bounds.centerY());
            canvas.scale(fitScale, fitScale);
            canvas.drawText(wordmark, 0, baseline, textPaint);
            canvas.restore();
        }
        @Override public void setAlpha(int alpha) {
            textPaint.setAlpha(alpha);
            invalidateSelf();
        }
        @Override public void setColorFilter(android.graphics.ColorFilter filter) {
            textPaint.setColorFilter(filter);
            invalidateSelf();
        }
        @Override public int getOpacity() {
            return android.graphics.PixelFormat.TRANSLUCENT;
        }
        @Override public int getIntrinsicWidth() { return AndroidUtilities.dp(132); }
        @Override public int getIntrinsicHeight() { return AndroidUtilities.dp(22); }
    }

"""
    s = s.replace(marker, impl + logo_view_impl + marker, 1)
    for native in (
        "    ImageView telegramLogoView;",
        "telegramLogoView.setTranslationX(titleView.getTranslationX() + dp(1));",
        "final float logoAlpha = logoVisibility * progress;",
        "telegramLogoView.setTranslationY(bottomY - barOffset",
        "addView(telegramLogoView, LayoutHelper.createFrame(132, 22));",
    ):
        if native not in s:
            raise SystemExit(f"Pinned stories native layout/animation changed: {native}")
    stories.write_text(s, encoding="utf-8")
    print("PASS: native ActionBar and native stories title slots branded without animation overrides")

if __name__ == "__main__":
    main()
