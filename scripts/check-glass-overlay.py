#!/usr/bin/env python3
"""Fast no-Gradle smoke checks for NabdhGram Glass source overlays."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-glass-overlay.py TELEGRAM_SOURCE")

root = Path(sys.argv[1])
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
adapter = (ui / "Adapters/DialogsAdapter.java").read_text(encoding="utf-8")
cell = (ui / "Cells/DialogCell.java").read_text(encoding="utf-8")
checks = {
    "dialog card paint created once": cell.count("private final android.graphics.Paint nabdhCardPaint") == 1,
    "dialog card canvas drawing present": cell.count("canvas.drawRoundRect(nabdhCardBounds") == 2,
    "dialog card excludes swipe/archive": "!drawArchive" in cell and "currentRevealProgress == 0.0f" in cell,
    "dialog selection feedback": "isPressed() || isSelected || isSelected()" in cell,
    "pinned section markers": "NabdhGlassPinnedChats" in adapter,
}
# Generated adapter references the pinned title twice: during binding and insertion.
checks["pinned section inserted once"] = adapter.count("new ItemInternal(VIEW_TYPE_HEADER_3,\n                        mContext.getString(org.telegram.messenger.R.string.NabdhGlassPinnedChats)") == 1
checks["normal section inserted once"] = adapter.count("new ItemInternal(VIEW_TYPE_HEADER_3,\n                        mContext.getString(org.telegram.messenger.R.string.NabdhGlassAllChats)") == 1
checks["home list only"] = "dialogsType == DialogsActivity.DIALOGS_TYPE_DEFAULT && folderId == 0" in adapter
checks["out-of-order guard"] = "boolean ordered = pinnedFirst < 0" in adapter and "ordered = false;" in adapter

for lang in ("values", "values-ar"):
    xml = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    strings = ET.parse(xml).getroot()
    for name in ("NabdhGlassPinnedChats", "NabdhGlassAllChats"):
        checks[f"{lang}: {name} unique"] = sum(
            e.attrib.get("name") == name for e in strings.findall("string")
        ) == 1

for name, okay in checks.items():
    print(("PASS" if okay else "FAIL") + " " + name)
if not all(checks.values()):
    raise SystemExit("NabdhGram Glass source smoke checks failed")
print("NabdhGram Glass source smoke checks passed.")
