#!/usr/bin/env python3
"""Fail before Gradle if the six approved launcher variants are incomplete."""
from pathlib import Path
import sys
from PIL import Image

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-approved-icons.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
res = root / "TMessagesProj/src/main/res"
java = (root / "TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java").read_text(encoding="utf-8")
manifest = (root / "TMessagesProj/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
names = [
    ("original", "NabdhOriginalIcon", "NabdhIconOriginal"),
    ("dark", "NabdhDarkIcon", "NabdhIconDark"),
    ("light", "NabdhLightIcon", "NabdhIconLight"),
    ("teal", "NabdhTealIcon", "NabdhIconTeal"),
    ("circular", "NabdhCircularIcon", "NabdhIconCircular"),
    ("hexagonal", "NabdhHexIcon", "NabdhIconHex"),
]
for slug, alias, label in names:
    assert ('"' + alias + '"') in java, "Missing icon enum " + alias
    assert ('R.mipmap.nabdh_icon_' + slug) in java, "Missing picker image " + slug
    assert ('android:name="org.telegram.messenger.' + alias + '"') in manifest, "Missing launcher alias " + alias
    assert manifest.count('android:icon="@mipmap/nabdh_icon_' + slug + '"') == 1, "Alias icon mismatch " + slug
    for density, pixels in (("mdpi",48),("hdpi",72),("xhdpi",96),("xxhdpi",144),("xxxhdpi",192)):
        p = res / ("mipmap-" + density) / ("nabdh_icon_" + slug + ".png")
        with Image.open(p) as image:
            image.load()
            assert image.size == (pixels, pixels), "Wrong size for " + str(p)
    for locale in ("values", "values-ar"):
        text = (res / locale / "nabdhgram_icon_variants.xml").read_text(encoding="utf-8")
        assert ('name="' + label + '"') in text, "Missing label " + locale + " " + slug
assert "NABDH_HEX" in java and "NOX" in java, "Native icon choices accidentally replaced"
assert java.index('NABDH_ORIGINAL("NabdhOriginalIcon"') > java.index('DEFAULT("DefaultIcon"'), "Original choice should follow default"
assert java.index('NABDH_HEXAGONAL("NabdhHexIcon"') < java.index('VINTAGE("VintageIcon"'), "Approved art must be visible before optional Telegram icons"
print("PASS: six selectable launcher aliases, resource labels and every Android density")
