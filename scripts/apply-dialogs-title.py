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

    # Telegram separately shows an image wordmark inside the EXISTING stories
    # header view on collapse, and fades/scales it using its own animation.
    # Replace that specific view in-place with a TextView; DO NOT change the
    # native alpha, x/y translation, scale, status/proxy, or transition curves.
    stories = ui / "Stories/DialogStoriesCell.java"
    s = stories.read_text(encoding="utf-8")
    s = once(s, "    ImageView telegramLogoView;",
             "    TextView telegramLogoView;", "native stories wordmark type")
    s = once(s,
         """        telegramLogoView = new ImageView(context);
        telegramLogoView.setContentDescription(getString(R.string.AppName));
        telegramLogoView.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        telegramLogoView.setImageResource(R.drawable.telegram_logo_2);
        telegramLogoView.setColorFilter(getTextLogoColor(), PorterDuff.Mode.MULTIPLY);
        telegramLogoView.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
        telegramLogoView.setFocusableInTouchMode(true);
        addView(telegramLogoView, LayoutHelper.createFrame(90, 22));""",
         """        // Replace artwork inside the original animated Telegram view slot.
        telegramLogoView = new TextView(context);
        telegramLogoView.setContentDescription("NabdhGram");
        telegramLogoView.setText("NabdhGram");
        telegramLogoView.setSingleLine(true);
        telegramLogoView.setEllipsize(TextUtils.TruncateAt.END);
        telegramLogoView.setTextSize(20);
        telegramLogoView.setTypeface(AndroidUtilities.bold());
        telegramLogoView.setGravity(Gravity.CENTER_VERTICAL);
        telegramLogoView.setTextColor(getTextLogoColor());
        telegramLogoView.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
        telegramLogoView.setFocusableInTouchMode(true);
        addView(telegramLogoView, LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, 28));""",
         "native stories wordmark view")
    s = once(s,
         "        telegramLogoView.setColorFilter(getTextLogoColor(), PorterDuff.Mode.MULTIPLY);",
         "        telegramLogoView.setTextColor(getTextLogoColor());",
         "native stories wordmark theme tint")
    # Native original uses titleView positions and logoVisibility*progress
    # alpha; these must remain unmodified. Ensure no third label is created.
    for native in (
        "telegramLogoView.setTranslationX(titleView.getTranslationX() + dp(1));",
        "final float logoAlpha = logoVisibility * progress;",
        "telegramLogoView.setTranslationY(bottomY - barOffset",
    ):
        if native not in s:
            raise SystemExit(f"Pinned stories animation anchor missing: {native}")
    stories.write_text(s, encoding="utf-8")
    print("PASS: native ActionBar and native stories title slots branded without animation overrides")

if __name__ == "__main__":
    main()
