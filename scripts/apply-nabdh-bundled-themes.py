#!/usr/bin/env python3
"""Register four user-approved NabdhGram .attheme assets as bundled Telegram themes.

Never decode/re-encode theme bytes: embedded WPS JPEG wallpapers must survive.
Optional until the binary assets are added to branding/themes in the GitHub repo.
"""
from pathlib import Path
import hashlib
import shutil
import sys
import zipfile

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-bundled-themes.py TELEGRAM_SOURCE")

root = Path(sys.argv[1])
themes = [
    ("nabdh_siri_refined.attheme", "NabdhGram • Siri Glass Refined", 0xFFEDEFF0, 0xFFDFE0E4, 0xFFDBDCD8,
     "75f9d70c9714d3a87c2531cf664627d60994caf2f3366663a3351c3edfac6497"),
    ("nabdh_soft_mint.attheme", "NabdhGram • Soft Mint", 0xFFE5F3F2, 0xFFD8EDEA, 0xFFB6E9D5,
     "2e1d755c59c640b1dd191ac4eda18e8232dc75347b6bef66dc1f80f094dfd011"),
    ("nabdh_dark.attheme", "NabdhGram • Dark Glass", 0xFF101B24, 0xFF203740, 0xFF24454A,
     "fc06d71577698ae0cf6b8879e5175274d5d0def85de1a1369dbaa0ca0627a617"),
    ("nabdh_sand.attheme", "NabdhGram • Gray Avalanche Sand", 0xFFD4C4AE, 0xFFE4D7C6, 0xFFD7C8B7,
     "b32ed42b89ac7375e7fddbe6833a506e89fe25436651696af5ff4346a5c46f7f"),
]
asset_dir = Path(__file__).resolve().parents[1] / "branding" / "themes"
archive = asset_dir / "NabdhGram_Bundled_Themes.zip"
available = [asset_dir / spec[0] for spec in themes]
if archive.is_file():
    # The approved ZIP keeps the four original binary files under branding/themes/.
    # Read only expected members: never extract arbitrary paths from a ZIP.
    with zipfile.ZipFile(archive) as bundled:
        expected = {"branding/themes/" + spec[0] for spec in themes}
        actual = {name for name in bundled.namelist() if name.endswith(".attheme")}
        if actual != expected:
            raise SystemExit("Theme archive has unexpected or missing .attheme members")
        for filename, name, background, incoming, outgoing, checksum in themes:
            entry = bundled.getinfo("branding/themes/" + filename)
            if entry.file_size > 5 * 1024 * 1024:
                raise SystemExit(f"Theme asset is unexpectedly large: {filename}")
            data = bundled.read(entry)
            if hashlib.sha256(data).hexdigest() != checksum:
                raise SystemExit(f"Theme integrity mismatch: {filename}")
            destination = root / "TMessagesProj/src/main/assets" / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
elif all(p.is_file() for p in available):
    for spec, original in zip(themes, available):
        if hashlib.sha256(original.read_bytes()).hexdigest() != spec[5]:
            raise SystemExit(f"Theme integrity mismatch: {original.name}")
        destination = root / "TMessagesProj/src/main/assets" / original.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, destination)
elif any(p.is_file() for p in available):
    raise SystemExit("Incomplete theme bundle: all four .attheme assets are required")
else:
    raise SystemExit("Missing NabdhGram theme ZIP or individual approved .attheme assets")

target = root / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/Theme.java"
source = target.read_text(encoding="utf-8")
anchor = """        sortThemes();

        ThemeInfo applyingTheme = null;"""
if source.count(anchor) != 1:
    raise SystemExit("Built-in Theme registration anchor changed; inspect upstream before patching")

lines = [
    "        // NabdhGram: bundled original .attheme files with wallpaper bytes intact.",
]
for filename, name, background, incoming, outgoing, sha in themes:
    lines.extend([
        "        themeInfo = new ThemeInfo();",
        f'        themeInfo.name = "{name}";',
        f'        themeInfo.assetName = "{filename}";',
        f"        themeInfo.previewBackgroundColor = 0x{background:08X};",
        f"        themeInfo.previewInColor = 0x{incoming:08X};",
        f"        themeInfo.previewOutColor = 0x{outgoing:08X};",
        "        themes.add(themeInfo);",
        "        themesDict.put(themeInfo.getKey(), themeInfo);",
    ])
source = source.replace(anchor, "\n".join(lines) + "\n\n" + anchor, 1)
target.write_text(source, encoding="utf-8")
print("Registered 4 bundled NabdhGram theme assets in native Telegram selector.")
