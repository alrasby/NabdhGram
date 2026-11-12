#!/usr/bin/env python3
"""Install the six selected NabdhGram launcher variants from the user's artwork.

The repository's approved WEBP is a 3x2 atlas of individually cropped original
designs (256x256 each). Never create replacement logos or change auth/branding.
Existing Telegram/approved default icons and launcher aliases are preserved.
"""
from pathlib import Path
import re
import sys
from PIL import Image

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-approved-icon-variants.py TELEGRAM_SOURCE")

repository = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1]).resolve()
source = repository / "branding/approved/NabdhGram_approved_launcher_variants.webp"
res = root / "TMessagesProj/src/main/res"
manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
controller = root / "TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java"
if not source.is_file() or not manifest.is_file() or not controller.is_file():
    raise SystemExit("Approved icon atlas or pinned Telegram sources are missing")

VARIANTS = (
    ("original", "NabdhOriginalIcon", "NabdhIconOriginal", "Original", "الأصلية"),
    ("dark", "NabdhDarkIcon", "NabdhIconDark", "Dark frame", "الإطار الداكن"),
    ("light", "NabdhLightIcon", "NabdhIconLight", "Light frame", "الإطار الفاتح"),
    ("teal", "NabdhTealIcon", "NabdhIconTeal", "Teal frame", "الإطار التركوازي"),
    ("circular", "NabdhCircularIcon", "NabdhIconCircular", "Circular", "الدائرية"),
    ("hexagonal", "NabdhHexIcon", "NabdhIconHex", "Hexagonal", "السداسية"),
)
densities = (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96),
             ("xxhdpi", 144), ("xxxhdpi", 192))
with Image.open(source) as source_image:
    source_image.load()
    if source_image.format != "WEBP" or source_image.size != (768, 512):
        raise SystemExit("Six original tiles must be a 768x512 WEBP atlas")
    atlas = source_image.convert("RGB")
    for index, (slug, _, _, _, _) in enumerate(VARIANTS):
        left, top = (index % 3) * 256, (index // 3) * 256
        tile = atlas.crop((left, top, left + 256, top + 256))
        for density, pixels in densities:
            # Keep the full approved drawing inside native launcher masks.
            art_size = round(pixels * 0.88)
            scaled = tile.resize((art_size, art_size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (pixels, pixels), (4, 37, 42))
            canvas.paste(scaled, ((pixels - art_size) // 2,
                                  (pixels - art_size) // 2))
            out_dir = res / ("mipmap-" + density)
            out_dir.mkdir(parents=True, exist_ok=True)
            canvas.save(out_dir / ("nabdh_icon_" + slug + ".png"),
                        format="PNG", optimize=True)

# Use the original Telegram launcher mechanism; six additional, FREE choices
# are added without replacing DefaultIcon or the pre-existing variants.
java = controller.read_text(encoding="utf-8")
# Keep the approved default first, then immediately show all six NabdhGram
# designs in the horizontal picker instead of burying them after Telegram's
# optional premium icons where users would need to scroll to discover them.
anchor = '        DEFAULT("DefaultIcon", R.drawable.icon_background_sa, R.mipmap.icon_foreground_sa, R.string.AppIconDefault),'
if java.count(anchor) != 1:
    raise SystemExit("Pinned LauncherIconController enum anchor changed")
addition = ',\n'.join(
    '        NABDH_' + slug.upper() + '("' + alias + '", R.drawable.nabdh_icon_preview_background, '
    'R.mipmap.nabdh_icon_' + slug + ', R.string.' + string_name + ')'
    for slug, alias, string_name, _, _ in VARIANTS
)
java = java.replace(anchor, anchor + '\n' + addition + ',', 1)
controller.write_text(java, encoding="utf-8")

xml = manifest.read_text(encoding="utf-8")
alias_anchor = 'android:name="org.telegram.messenger.VintageIcon"'
if xml.count(alias_anchor) != 1:
    raise SystemExit("Pinned VintageIcon alias changed")
at = xml.index(alias_anchor)
start = xml.rfind("        <activity-alias", 0, at)
end = xml.find("</activity-alias>", at) + len("</activity-alias>")
if start < 0 or end < at:
    raise SystemExit("Could not isolate native activity-alias")
template = xml[start:end]
if ('android:enabled="false"' not in template
        or 'android:icon="@mipmap/icon_6_launcher"' not in template
        or 'android:roundIcon="@mipmap/icon_6_launcher_round"' not in template):
    raise SystemExit("VintageIcon alias shape changed; refusing unsafe manifest edit")
new_aliases = []
for slug, alias, _, _, _ in VARIANTS:
    replacement = template.replace("org.telegram.messenger.VintageIcon",
                                   "org.telegram.messenger." + alias)
    replacement = replacement.replace("@mipmap/icon_6_launcher_round",
                                      "@mipmap/nabdh_icon_" + slug)
    replacement = replacement.replace("@mipmap/icon_6_launcher",
                                      "@mipmap/nabdh_icon_" + slug)
    new_aliases.append(replacement)
xml = xml[:end] + "\n\n" + "\n\n".join(new_aliases) + xml[end:]
manifest.write_text(xml, encoding="utf-8")

preview = res / "drawable/nabdh_icon_preview_background.xml"
preview.parent.mkdir(parents=True, exist_ok=True)
preview.write_text(
    '<shape xmlns:android="http://schemas.android.com/apk/res/android" '
    'android:shape="rectangle"><solid android:color="#04252A"/></shape>\n',
    encoding="utf-8")

for folder, label_index in (("values", 3), ("values-ar", 4)):
    directory = res / folder
    directory.mkdir(parents=True, exist_ok=True)
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for _, _, name, en, ar in VARIANTS:
        lines.append('    <string name="' + name + '">' +
                     (en if label_index == 3 else ar) + '</string>')
    lines.append('</resources>')
    (directory / "nabdhgram_icon_variants.xml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
print("PASS: six original NabdhGram icon choices added to native launcher aliases and picker")
