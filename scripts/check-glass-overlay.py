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
checks = {
    "dialog card paint created once": cell.count("private final android.graphics.Paint nabdhCardPaint") == 1,
    "dialog card canvas drawing present": cell.count("canvas.drawRoundRect(nabdhCardBounds") == 2,
    "dialog card excludes swipe/archive": "!drawArchive" in cell and "currentRevealProgress == 0.0f" in cell,
    "dialog selection feedback": "isPressed() || isSelected || isSelected()" in cell,
    "decoration section headings": "NabdhGlassPinnedChats" in dialogs and "NabdhGlassOtherChats" in dialogs,
    "decoration not adapter mutation": "new RecyclerView.ItemDecoration()" in dialogs
        and "itemInternals.add(regularFirst" not in dialogs,
    "main chats only": "viewPage.dialogsType == DIALOGS_TYPE_DEFAULT && folderId == 0 && communityId == 0" in dialogs,
}

for lang in ("values", "values-ar"):
    xml = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    strings = ET.parse(xml).getroot()
    for name in ("NabdhGlassPinnedChats", "NabdhGlassOtherChats"):
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
