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
    dialogs.write_text(d, encoding="utf-8")

    # Preserve Telegram's ORIGINAL ImageView type, 90x22dp layout, native
    # translation, visibility, alpha and scale. The previous TextView with
    # WRAP_CONTENT changed its geometry and was clipped during transitions.
    # Only substitute the image's *content*, with a drawable that renders
    # the wordmark within the unchanged bounds.
    stories = ui / "Stories/DialogStoriesCell.java"
    s = stories.read_text(encoding="utf-8")
    s = once(s,
         "        telegramLogoView.setImageResource(R.drawable.telegram_logo_2);",
         "        telegramLogoView.setImageDrawable(new NabdhNativeWordmarkDrawable());",
         "native ImageView image source")
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
            // Fit the word inside Telegram's original 90dp ImageView so it
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
        @Override public int getIntrinsicWidth() { return AndroidUtilities.dp(90); }
        @Override public int getIntrinsicHeight() { return AndroidUtilities.dp(22); }
    }

"""
    s = s.replace(marker, impl + marker, 1)
    for native in (
        "    ImageView telegramLogoView;",
        "telegramLogoView.setTranslationX(titleView.getTranslationX() + dp(1));",
        "final float logoAlpha = logoVisibility * progress;",
        "telegramLogoView.setTranslationY(bottomY - barOffset",
        "addView(telegramLogoView, LayoutHelper.createFrame(90, 22));",
    ):
        if native not in s:
            raise SystemExit(f"Pinned stories native layout/animation changed: {native}")
    stories.write_text(s, encoding="utf-8")
    print("PASS: native ActionBar and native stories title slots branded without animation overrides")

if __name__ == "__main__":
    main()
