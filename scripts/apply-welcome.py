#!/usr/bin/env python3
"""Brand Telegram's first welcome page without changing authentication flows."""
from pathlib import Path
import sys

def replace_once(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit(f"Expected exactly one {label}; found {text.count(old)}")
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-welcome.py TELEGRAM_SOURCE")
    root = Path(sys.argv[1]).resolve()
    source = root / "TMessagesProj/src/main/java/org/telegram/ui/IntroActivity.java"
    content = source.read_text(encoding="utf-8")
    content = replace_once(content,
        'LocaleController.getString(R.string.Page1Message),',
        'LocaleController.isRTL ? "تواصل بحرية، بخصوصية وذكاء." : "Connect freely, with privacy and intelligence.",',
        "first welcome page description")
    content = replace_once(content,
        'startMessagingButton.setText(LocaleController.getString(R.string.StartMessaging));',
        'startMessagingButton.setText(LocaleController.isRTL ? "ابدأ مع نبض جرام" : "Start with NabdhGram");',
        "welcome button label")
    start = '        logoDrawable = context.getResources().getDrawable(R.drawable.telegram_logo).mutate();'
    end = '        titles[0] = ssb;'
    i = content.find(start)
    j = content.find(end, i)
    if i < 0 or j < 0 or content.count(start) != 1 or content.count(end) != 1:
        raise SystemExit("Unexpected upstream intro logo block; refusing unsafe edit")
    j += len(end)
    content = content[:i] + '        titles[0] = "NabdhGram";' + content[j:]
    # The branded text title intentionally removes the upstream telegram_logo ImageSpan.
    # IntroActivity.updateColors() still tints logoDrawable unconditionally in upstream,
    # which crashes the welcome screen with a NullPointerException on launch.
    # Keep the custom title and guard the obsolete drawable access.
    content = replace_once(content,
        '        logoDrawable.setColorFilter(Theme.multAlpha(getThemedColor(Theme.key_actionBarDefaultTitle), 0.9f), PorterDuff.Mode.MULTIPLY);',
        '        if (logoDrawable != null) {\n            logoDrawable.setColorFilter(Theme.multAlpha(getThemedColor(Theme.key_actionBarDefaultTitle), 0.9f), PorterDuff.Mode.MULTIPLY);\n        }'.replace('\n', '\n'),
        "nullable removed intro title drawable")
    source.write_text(content, encoding="utf-8")
    print("NabdhGram welcome title, description, and start button applied.")
    print("NOTE: visual intro animation/logo remains upstream until a separately approved transparent asset is integrated.")

if __name__ == "__main__":
    main()
