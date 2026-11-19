#!/usr/bin/env python3
"""Verify font options, fallback and legal asset installer in NabdhGram source."""
from pathlib import Path
import re
import sys

FAMILIES = (
    "system-default", "readex-pro", "vazirmatn", "noto-sans-arabic",
    "tajawal", "rubik", "dejavu-sans-condensed", "serif",
)


def check(root):
    root = Path(root)
    menu = (root / "scripts/apply-glass-settings.py").read_text(encoding="utf-8")
    bridge = (root / "scripts/apply-glass-global-font.py").read_text(encoding="utf-8")
    installer = (root / "scripts/install-dejavu-condensed.py").read_text(encoding="utf-8")
    match = re.search(r'String\[\] families = \{([^}]+)\};', menu)
    if not match:
        raise ValueError("Font family menu missing")
    labels = tuple(re.findall(r'"([^"]+)"', match.group(1)))
    if labels != FAMILIES or len(set(labels)) != len(labels):
        raise ValueError("Duplicate/missing catalog entries: " + str(labels))
    if 'if ("sans-serif".equals(selectedFont))' not in menu:
        raise ValueError("Previous generic sans preference not migrated")
    for item in (
        '"DejaVuSansCondensed.ttf"',
        '"DejaVuSansCondensed-Bold.ttf"',
        'DejaVu-LICENSE.txt',
    ):
        if item not in installer and item not in bridge and item not in menu:
            raise ValueError("Missing licensed DejaVu font asset: " + item)
    if '"dejavu-sans-condensed".equals(family)' not in bridge:
        raise ValueError("DejaVu family not linked to AndroidUtilities")
    if 'Typeface.create(bundled,' not in bridge:
        raise ValueError("Native Typeface fallback changed")
    if 'applicationContext' not in bridge or '"font_family"' not in bridge:
        raise ValueError("Font preferences bridge changed")
    print("PASS: distinct font catalog; DejaVu Regular/Bold, fallback and license present")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check-nabdh-font-catalog.py NABDHGRAM_REPO")
    check(sys.argv[1])
