#!/usr/bin/env python3
"""Consolidate Telegram chat bubble palette and all canvas-drawn text fonts."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-chat-consistency.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
templates = Path(__file__).resolve().parent.parent / "overlay/java"

def once(src, old, new, label):
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"{label}: pinned native anchor expected once, found {count}")
    return src.replace(old, new, 1)

for name in ("NabdhBubblePalette.java", "NabdhTypefaceManager.java"):
    destination = ui / "Components" / name
    if destination.exists():
        raise SystemExit(f"Cannot overwrite existing Telegram class: {name}")
    destination.write_text((templates / name).read_text(encoding="utf-8"),
                           encoding="utf-8")

theme = ui / "ActionBar/Theme.java"
s = theme.read_text(encoding="utf-8")
s = once(s,
    """            addChatPaint(key_paint_chatTimeBackground, chat_timeBackgroundPaint, key_chat_mediaTimeBackground);
        }
    }

    public static void createChatResources(Context context, boolean fontsOnly) {""",
    """            addChatPaint(key_paint_chatTimeBackground, chat_timeBackgroundPaint, key_chat_mediaTimeBackground);
        }
        // Includes file names, audio and forward labels, not only chat body.
        org.telegram.ui.Components.NabdhTypefaceManager.applyChatPaints();
    }

    public static void createChatResources(Context context, boolean fontsOnly) {""",
    "Theme chat-paint lifecycle")
theme.write_text(s, encoding="utf-8")

settings = ui / "NabdhGramFeatureCategoryActivity.java"
s = settings.read_text(encoding="utf-8")
s = once(s,
    """                if (Theme.chat_explanationTextPaint != null) Theme.chat_explanationTextPaint.setTypeface(regular);
                org.telegram.messenger.NotificationCenter.getGlobalInstance().postNotificationName(""",
    """                if (Theme.chat_explanationTextPaint != null) Theme.chat_explanationTextPaint.setTypeface(regular);
                org.telegram.ui.Components.NabdhTypefaceManager.applyChatPaints();
                org.telegram.messenger.NotificationCenter.getGlobalInstance().postNotificationName(""",
    "explicit selected font refresh")
settings.write_text(s, encoding="utf-8")

bubble = ui / "ActionBar/MessageDrawable.java"
s = bubble.read_text(encoding="utf-8")
s = once(s,
    "if (currentType != TYPE_TEXT || themePreview || isSelected",
    "if ((currentType != TYPE_TEXT && currentType != TYPE_MEDIA)\n                || themePreview || isSelected",
    "native liquid glass type guard")
s = once(s,
    "&& currentType == TYPE_TEXT && !themePreview && !isSelected",
    "&& (currentType == TYPE_TEXT || currentType == TYPE_MEDIA)\n                && !themePreview && !isSelected",
    "gradient bubble type guard")
s = once(s,
    """final boolean nabdhFrostedText = currentType == TYPE_TEXT
                        && !themePreview && !isSelected && crossfadeFromDrawable == null;""",
    """final boolean nabdhFrostedText =
                        (currentType == TYPE_TEXT || currentType == TYPE_MEDIA)
                        && !themePreview && !isSelected && crossfadeFromDrawable == null;""",
    "cached bubble type guard")
# Keep low-res wallpaper sampling text-only, never filter real media.
s = once(s, "nabdhDrawFrostedWallpaper(canvas, path);",
    "if (currentType == TYPE_TEXT) nabdhDrawFrostedWallpaper(canvas, path);",
    "gradient wallpaper guard")
s = once(s, "nabdhDrawFrostedWallpaper(canvas, makePath());",
    "if (currentType == TYPE_TEXT) nabdhDrawFrostedWallpaper(canvas, makePath());",
    "cached wallpaper guard")
s = once(s,
    "p.setAlpha(nabdhOriginalPaintAlpha * 136 / 255);",
    """p.setAlpha(nabdhOriginalPaintAlpha *
                    org.telegram.ui.Components.NabdhBubblePalette.backgroundAlpha(
                        org.telegram.ui.Components.NabdhGlassStyle.current(),
                        getColor(isOut ? Theme.key_chat_outBubble : Theme.key_chat_inBubble),
                        getColor(Theme.key_chat_wallpaper),
                        currentType == TYPE_MEDIA) / 255);""",
    "gradient normalized opacity")
s = once(s,
    "background.setAlpha(nabdhOriginalAlpha * 136 / 255);",
    """background.setAlpha(nabdhOriginalAlpha *
                            org.telegram.ui.Components.NabdhBubblePalette.backgroundAlpha(
                                org.telegram.ui.Components.NabdhGlassStyle.current(),
                                getColor(isOut ? Theme.key_chat_outBubble : Theme.key_chat_inBubble),
                                getColor(Theme.key_chat_wallpaper),
                                currentType == TYPE_MEDIA) / 255);""",
    "cached normalized opacity")
for old in ("nabdhBubbleEdge.setStrokeWidth(dp(1));",
            "nabdhBubbleEdge.setStrokeWidth(dp(0.8f));"):
    s = once(s, old, "nabdhBubbleEdge.setStrokeWidth(AndroidUtilities.dpf2(0.85f));",
             "consistent stroke geometry")
for old in ("nabdhBubbleEdge.setAlpha((int) (122f * alpha / 255f));",
            "nabdhBubbleEdge.setAlpha((int) (142f * alpha / 255f));"):
    s = once(s, old,
        """nabdhBubbleEdge.setAlpha(
                    org.telegram.ui.Components.NabdhBubblePalette.edgeAlpha(
                        org.telegram.ui.Components.NabdhGlassStyle.current(), alpha));""",
        "consistent stroke contrast")
bubble.write_text(s, encoding="utf-8")
print("PASS: chat fonts and text/media bubble colors now share native managers")
