#!/usr/bin/env python3
"""Round native Telegram settings and profile touch selectors (UI only)."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-native-settings-profile.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"
changes = [
    ("SettingsActivity.java",
     "        listView.setSections();\n",
     "        listView.setSections();\n        // NabdhGram Glass: rounded touch feedback on native settings rows.\n        listView.setSelectorRadius(17);\n"),
    ("ProfileActivity.java",
     "        listView.setSections();\n        listView.applyPaddingToSections = false;",
     "        listView.setSections();\n        // NabdhGram Glass: rounded profile action selection.\n        listView.setSelectorRadius(17);\n        listView.applyPaddingToSections = false;"),
]
for name, anchor, replacement in changes:
    p = root / name
    source = p.read_text(encoding="utf-8")
    if source.count(anchor) != 1:
        raise SystemExit(f"Unexpected native UI anchor: {name}")
    p.write_text(source.replace(anchor, replacement, 1), encoding="utf-8")
    print(f"Applied rounded native selector: {name}")
