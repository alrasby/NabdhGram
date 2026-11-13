#!/usr/bin/env python3
"""Fail-closed QA for BubblePalette, selected Arabic fonts and cached layouts."""
from pathlib import Path
import sys

repo = Path(__file__).resolve().parent.parent
script = (repo / "scripts/apply-nabdh-chat-consistency.py").read_text(encoding="utf-8")
palette = (repo / "overlay/java/NabdhBubblePalette.java").read_text(encoding="utf-8")
fonts = (repo / "overlay/java/NabdhTypefaceManager.java").read_text(encoding="utf-8")
workflow = (repo / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")

def verify(test, reason):
    if not test:
        raise SystemExit("FAIL chat consistency: " + reason)

verify("NabdhBubblePalette.backgroundAlpha(" in script
       and "NabdhBubblePalette.edgeAlpha(" in script
       and "TYPE_TEXT || currentType == TYPE_MEDIA" in script,
       "text and media must share native draw policy")
verify("nabdhOriginalAlpha * 136 / 255" not in script
       and "nabdhOriginalPaintAlpha * 136 / 255" not in script,
       "old opaque/transparent split remains in the final overlay")
verify("currentType == TYPE_TEXT) nabdhDrawFrostedWallpaper" in script,
       "actual media photos must never be blurred")
verify("Math.abs(lightness(bubbleColor) - lightness(wallpaperColor))" in palette,
       "contrast-aware alpha policy absent")
verify("media) opacity = Math.max(opacity, 213)" in palette,
       "file metadata contrast minimum missing")
verify("private static int lightness(int color)" in palette,
       "palette must use allocation-free integer luminance")
verify("void applyChatPaints()" in fonts
       and all("Theme." + p in fonts for p in (
           "chat_msgTextPaint", "chat_docNamePaint", "chat_audioTitlePaint",
           "chat_audioPerformerPaint", "chat_replyTextPaint",
           "chat_quoteTextPaint", "chat_forwardNamePaint",
           "chat_locationTitlePaint", "chat_locationAddressPaint",
           "chat_contextResult_titleTextPaint", "chat_timePaint")),
       "not all native chat TextPaint categories use selected typeface")
verify("chat_msgTextCodePaint" in fonts and "stay MONOSPACE" in fonts
       and "chat_msgTextPaintEmoji" not in fonts.split("public static void applyChatPaints()")[1],
       "code and emoji paints must be preserved")
verify("NabdhTypefaceManager.applyChatPaints();" in script
       and "Theme native chat-paint lifecycle" in script
       and "explicit selected font refresh" in script,
       "chat paints not wired to creation and onChange")
verify("apply-nabdh-chat-consistency.py Telegram-upstream" in workflow
       and "check-nabdh-chat-consistency.py Telegram-upstream" in workflow,
       "real upstream preflight must gate overlay")
print("PASS: cached palette, media contrast and native font coverage source guards")

if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
    sys.exit(0)
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-chat-consistency.py --self-test | TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
def read(rel):
    f = ui / rel
    verify(f.exists(), "generated native file absent: " + rel)
    return f.read_text(encoding="utf-8")

bub = read("ActionBar/MessageDrawable.java")
theme = read("ActionBar/Theme.java")
settings = read("NabdhGramFeatureCategoryActivity.java")
nativePalette = read("Components/NabdhBubblePalette.java")
nativeFonts = read("Components/NabdhTypefaceManager.java")
verify(bub.count("NabdhBubblePalette.backgroundAlpha(") == 2,
       "text/media alpha not used in both native drawing paths")
verify(bub.count("NabdhBubblePalette.edgeAlpha(") == 2
       and bub.count("nabdhBubbleEdge.setStrokeWidth(AndroidUtilities.dpf2(0.85f));") == 2,
       "cached/gradient outlines remain inconsistent")
verify("(currentType == TYPE_TEXT || currentType == TYPE_MEDIA)" in bub
       and "(currentType != TYPE_TEXT && currentType != TYPE_MEDIA)" in bub,
       "media cards remain outside Liquid/Crystal style")
verify("if (currentType == TYPE_TEXT) nabdhDrawFrostedWallpaper" in bub,
       "media preview could be blurred")
verify("!themePreview && !isSelected" in bub and
       "crossfadeFromDrawable == null" in bub,
       "native selected/preview/crossfade semantics altered")
verify("NabdhTypefaceManager.applyChatPaints();" in theme
       and "NabdhTypefaceManager.applyChatPaints();" in settings,
       "selected Arabic typeface not updated at creation and selection")
verify("Theme.chat_docNamePaint" in nativeFonts
       and "Theme.chat_audioPerformerPaint" in nativeFonts
       and "chat_msgTextCodePaint" not in
           nativeFonts.split("public static void applyChatPaints()")[1].split("// Code:")[0],
       "file/audio font coverage incomplete or monospace overwritten")
verify("backgroundAlpha" in nativePalette and "edgeAlpha" in nativePalette,
       "generated palette class incomplete")
print("PASS: generated real Telegram Java chat bubble and font consistency")
