#!/usr/bin/env python3
"""Use the chosen NabdhGram font in Telegram's custom-drawn message TextPaint.

The native chat renderer uses TextPaint rather than ordinary TextViews for
messages, replies and quotes. Merely replacing Roboto resources misses them.
Keep native text size, emoji fonts, spans, layouts and touch behavior.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-chat-typefaces.py TELEGRAM_SOURCE")
path = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/Theme.java"
source = path.read_text(encoding="utf-8")
for name, constructor in (
    ("chat_msgTextPaint", "Paint"),
    ("chat_replyTextPaint", "TextPaint"),
    ("chat_quoteTextPaint", "TextPaint"),
    ("chat_explanationTextPaint", "TextPaint"),
):
    anchor = f"{name} = new TextPaint({constructor}.ANTI_ALIAS_FLAG);"
    if source.count(anchor) != 1:
        raise SystemExit(f"Telegram chat text paint anchor changed: {name}")
    source = source.replace(anchor,
                            anchor + "\n                " + name
                            + '.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));',
                            1)
path.write_text(source, encoding="utf-8")
print("Chat message/reply/quote paint now honors selected NabdhGram font.")
