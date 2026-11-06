#!/usr/bin/env python3
"""Install the user-approved NabdhGram launcher artwork into a pinned Telegram checkout.

Usage: python3 scripts/apply-brand-icons.py TELEGRAM_SOURCE APPROVED_MASTER_PNG
The input is the original approved icon; this script does NOT redraw it.
"""
from pathlib import Path
import sys

SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: apply-brand-icons.py TELEGRAM_SOURCE APPROVED_MASTER_PNG")
    root = Path(sys.argv[1]).resolve()
    master = Path(sys.argv[2]).resolve()
    if not (root / "TMessagesProj_App" / "build.gradle").is_file():
        raise SystemExit("Invalid Telegram source checkout")
    if not master.is_file():
        raise SystemExit(f"Approved master PNG missing: {master}")
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow required: python3 -m pip install Pillow")
    with Image.open(master) as im:
        im.load()
        if im.format != "PNG" or im.width != im.height or im.width < 512:
            raise SystemExit("Approved master must be a square PNG >=512px")
        rgba = im.convert("RGBA")
        res = root / "TMessagesProj_App" / "src" / "main" / "res"
        for density, px in SIZES.items():
            folder = res / f"mipmap-{density}"
            folder.mkdir(parents=True, exist_ok=True)
            scaled = rgba.resize((px, px), Image.Resampling.LANCZOS)
            for name in ("nabdhgram_launcher.png", "nabdhgram_launcher_round.png"):
                scaled.save(folder / name, format="PNG", optimize=True)
        # App-module overlay supersedes Telegram library's adaptive-icon resources.
        # Use the exact approved image as the adaptive foreground without inventing new art.
        drawable = res / "drawable-nodpi"
        drawable.mkdir(parents=True, exist_ok=True)
        rgba.save(drawable / "nabdhgram_launcher_master.png", format="PNG", optimize=True)
        anydpi = res / "mipmap-anydpi-v26"
        anydpi.mkdir(parents=True, exist_ok=True)
        for name in ("nabdhgram_launcher.xml", "nabdhgram_launcher_round.xml"):
            (anydpi / name).write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <background android:drawable="@android:color/transparent" />\n'
                '    <foreground android:drawable="@drawable/nabdhgram_launcher_master" />\n'
                '</adaptive-icon>\n', encoding="utf-8"
            )
        # Point the manifest explicitly to NabdhGram-specific resource names.
        # The upstream Telegram resources are intentionally left intact.
        manifest = root / "TMessagesProj" / "config" / "debug" / "AndroidManifest_SDK23.xml"
        text = manifest.read_text(encoding="utf-8")
        before = 'android:icon="@mipmap/ic_launcher"'
        round_before = 'android:roundIcon="@mipmap/ic_launcher_round"'
        if text.count(before) != 1 or text.count(round_before) != 1:
            raise SystemExit("Expected upstream launcher icon references not found exactly once")
        text = text.replace(before, 'android:icon="@mipmap/nabdhgram_launcher"')
        text = text.replace(round_before, 'android:roundIcon="@mipmap/nabdhgram_launcher_round"')
        manifest.write_text(text, encoding="utf-8")
        print("Debug manifest launcher resources: nabdhgram_launcher / nabdhgram_launcher_round")
    print("Approved NabdhGram launcher artwork integrated; verify adaptive icon crop on device.")

if __name__ == "__main__":
    main()
