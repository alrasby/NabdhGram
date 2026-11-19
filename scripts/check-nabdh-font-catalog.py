#!/usr/bin/env python3
"""Verify font options, fallback and legal asset installer in NabdhGram source."""
from pathlib import Path
import re
import sys

FAMILIES = (
    "system-default", "readex-pro", "vazirmatn", "noto-sans-arabic",
    "tajawal", "rubik", "noto-sans", "serif",
)


def check(root):
    root = Path(root)
    menu = (root / "scripts/apply-glass-settings.py").read_text(encoding="utf-8")
    bridge = (root / "scripts/apply-glass-global-font.py").read_text(encoding="utf-8")
    noto_installer = (root / "scripts/install-open-fonts.py").read_text(encoding="utf-8")
    noto_java = (root / "overlay/java/NabdhNotoFallback.java").read_text(encoding="utf-8")
    match = re.search(r'String\[\] families = \{([^}]+)\};', menu)
    if not match:
        raise ValueError("Font family menu missing")
    labels = tuple(re.findall(r'"([^"]+)"', match.group(1)))
    if labels != FAMILIES or len(set(labels)) != len(labels):
        raise ValueError("Duplicate/missing catalog entries: " + str(labels))
    if 'if ("sans-serif".equals(selectedFont))' not in menu:
        raise ValueError("Previous generic sans preference not migrated")
    if "dejavu-sans-condensed" not in menu or "dejavu-sans-condensed" not in bridge:
        raise ValueError("Legacy DejaVu setting migration missing")
    for filename, content in (
        ("scripts/apply-glass-settings.py", menu),
        ("scripts/apply-glass-global-font.py", bridge),
        ("scripts/apply-glass-v1-finishing.py", (root / "scripts/apply-glass-v1-finishing.py").read_text(encoding="utf-8")),
        (".github/workflows/nabdhgram-identity-build.yml", (root / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")),
    ):
        if "DejaVuSansCondensed" in content or "install-dejavu-condensed" in content:
            raise ValueError("Obsolete DejaVu runtime/build reference: " + filename)
    if (root / "scripts/install-dejavu-condensed.py").exists():
        raise ValueError("Obsolete DejaVu installer still present")
    if "NabdhNotoFallback.createArabic(" not in menu or "NabdhNotoFallback.createArabic(" not in bridge:
        raise ValueError("Arabic width-adjusted font is not used consistently")
    if "setFontVariationSettings" not in noto_java or "ARABIC_WIDTH" not in noto_java:
        raise ValueError("Arabic variable-font width configuration missing")
    if '"NotoSans": ("notosans", "NotoSans[wdth,wght].ttf")' not in noto_installer:
        raise ValueError("Pinned OFL Noto Sans asset not installed")
    for marker in (
        "Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q",
        "fonts/NotoSans.ttf",
        "fonts/NotoSansArabic.ttf",
        "new Typeface.CustomFallbackBuilder(primary)",
        ".addCustomFallback(arabicFallback)",
        '.setSystemFallback("sans-serif")',
        "Typeface.createFromAsset(",
    ):
        if marker not in noto_java:
            raise ValueError("Android multilingual fallback contract missing: " + marker)
    if '"noto-sans".equals(family)' not in bridge or "NabdhNotoFallback.create(" not in bridge:
        raise ValueError("Noto selected preference is not routed to native fallback")
    if 'Typeface.create(bundled,' not in bridge:
        raise ValueError("Native Typeface fallback changed")
    if 'applicationContext' not in bridge or '"font_family"' not in bridge:
        raise ValueError("Font preferences bridge changed")
    print("PASS: unique catalog; Noto Arabic width and fallback; DejaVu fully retired")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check-nabdh-font-catalog.py NABDHGRAM_REPO")
    check(sys.argv[1])
