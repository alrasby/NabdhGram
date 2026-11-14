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
    # The reply TextPaint is initialized in both resource initialization
    # paths. Apply the family to each one, not only the first occurrence.
    expected = 2 if name == "chat_replyTextPaint" else 1
    if source.count(anchor) != expected:
        raise SystemExit(
            f"Telegram chat text paint anchor changed: {name} (expected {expected}, found {source.count(anchor)})"
        )
    source = source.replace(anchor,
                            anchor + "\n                " + name
                            + '.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));',
                            expected)
# Source-verified against pinned Telegram 13.2.2: createCommonChatResources
# initializes both message and metadata TextPaint instances. One central
# manager updates canvas-drawn typography after those native initializers.
anchor = """        }
    }

    public static void createChatResources(Context context, boolean fontsOnly) {"""
if source.count(anchor) != 1:
    raise SystemExit("NabdhTypefaceManager: pinned chat resource boundary changed")
source = source.replace(anchor, """        }
        org.telegram.ui.Components.NabdhTypefaceManager.applyChatPaints();
    }

    public static void createChatResources(Context context, boolean fontsOnly) {""", 1)
manager_source = Path(__file__).resolve().parents[1] / "overlay/java/NabdhTypefaceManager.java"
manager_target = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Components/NabdhTypefaceManager.java"
if manager_target.exists():
    raise SystemExit("Native typography manager already present; avoid duplicate integration")
manager_target.write_text(manager_source.read_text(encoding="utf-8"), encoding="utf-8")
path.write_text(source, encoding="utf-8")
print("Chat message/reply/quote paint now honors selected NabdhGram font.")
