#!/usr/bin/env python3
"""Fast no-Gradle smoke checks for NabdhGram Glass source overlays."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-glass-overlay.py TELEGRAM_SOURCE")

root = Path(sys.argv[1])
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
dialogs = (ui / "DialogsActivity.java").read_text(encoding="utf-8")
cell = (ui / "Cells/DialogCell.java").read_text(encoding="utf-8")
settings = (ui / "NabdhGramSettingsActivity.java").read_text(encoding="utf-8")
selector = (ui / "Components/RecyclerListView.java").read_text(encoding="utf-8")
typefaces = (root / "TMessagesProj/src/main/java/org/telegram/messenger/AndroidUtilities.java").read_text(encoding="utf-8")
composer = (ui / "Components/ChatActivityEnterView.java").read_text(encoding="utf-8")
checks = {
    "chat composer rounded theme surface": "messageEditText.setBackground(nabdhInputGlass)" in composer
        and "nabdhInputGlass.setCornerRadius(dp(19))" in composer
        and "Theme.key_chat_messagePanelBackground" in composer,
    "dialog selector rounded clipping installed": "selectorView instanceof org.telegram.ui.Cells.DialogCell" in selector
        and "canvas.clipPath(nabdhDialogSelectorPath)" in selector
        and "selectorRect.left + 7f * density" in selector
        and "selectorRect.bottom - 3f * density" in selector,
    "selector canvas state restored": "if (nabdhDialog) {" in selector and "canvas.restore();" in selector in selector,
    "font preference consumed by Telegram typeface resolver": 'getString("font_family", "readex-pro")' in typefaces
        and 'getTypeface("fonts/ReadexPro.ttf")' in typefaces
        and '"sans-serif".equals(family)' in typefaces
        and '"serif".equals(family)' in typefaces,
    "appearance font preference persisted": 'getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)' in (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
        and 'putString("font_family", family).apply()' in (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8"),
    "settings card native ripple": "new android.graphics.drawable.RippleDrawable(" in settings
        and "card.setBackground(touchSurface)" in settings,
    "pinned outline avoids clipped groups": "hasFirstPinnedRow" in dialogs
        and "hasLastPinnedRow" in dialogs
        and "position + 1 < viewPage.dialogsAdapter.getItemCount()" in dialogs,
    "dialog card paint created once": cell.count("private final android.graphics.Paint nabdhCardPaint") == 1,
    "dialog card canvas drawing present": cell.count("canvas.drawRoundRect(nabdhCardBounds") == 2,
    "dialog card excludes swipe/archive": "!drawArchive" in cell and "currentRevealProgress == 0.0f" in cell,
    "dialog selection feedback": "isPressed() || isSelected || isSelected()" in cell,
    "regular section without pinned chats": "if (!pinned && position == 0) return 2;" in dialogs,
    "decoration section headings": "NabdhGlassPinnedChats" in dialogs and "NabdhGlassOtherChats" in dialogs,
    "pinned group outline above opaque cards": "public void onDrawOver(Canvas canvas, RecyclerView parent, RecyclerView.State state)" in dialogs
        and "pinnedGroupPaint.setStyle(Paint.Style.STROKE)" in dialogs,
    "pinned group drawing present": "pinnedGroupPaint.setColor(" in dialogs
        and "canvas.drawRoundRect(dp(4), groupTop + dp(2)" in dialogs,
    "pinned group does not alter adapter": "groupTop = Math.min(groupTop, child.getTop())" in dialogs
        and "groupBottom = Math.max(groupBottom, child.getBottom())" in dialogs,
    "decoration not adapter mutation": "new RecyclerView.ItemDecoration()" in dialogs
        and "itemInternals.add(regularFirst" not in dialogs,
    "main chats only": "viewPage.dialogsType == DIALOGS_TYPE_DEFAULT && folderId == 0 && communityId == 0" in dialogs,
}

for lang in ("values", "values-ar"):
    xml = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    strings = ET.parse(xml).getroot()
    for name in ("NabdhGlassPinnedChats", "NabdhGlassOtherChats", "NabdhFontTitle", "NabdhFontSans", "NabdhFontSerif", "NabdhFontScope"):
        found = sum(e.attrib.get("name") == name for e in strings.findall("string"))
        print(f"Resource count {lang}/{name}: {found}", flush=True)
        if found != 1:
            print("Nearby resource names: " + repr([e.attrib.get("name") for e in strings.findall("string") if "Glass" in e.attrib.get("name", "")]), flush=True)
        checks[f"{lang}: {name} unique"] = found == 1

for name, okay in checks.items():
    print(("PASS" if okay else "FAIL") + " " + name)
if not all(checks.values()):
    raise SystemExit("NabdhGram Glass source smoke checks failed")
print("NabdhGram Glass source smoke checks passed.")
