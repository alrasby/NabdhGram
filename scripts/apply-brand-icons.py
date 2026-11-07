#!/usr/bin/env python3
"""Install the user-approved NabdhGram launcher artwork into a pinned Telegram checkout.

Usage: python3 scripts/apply-brand-icons.py TELEGRAM_SOURCE APPROVED_MASTER_PNG
The input is the original approved icon; this script does NOT redraw it.
"""
from pathlib import Path
import sys

SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
# Android's adaptive-icon safe region is the central 66/108 of the canvas.
# Keep the complete approved artwork inside that region for all launcher masks.
ARTWORK_FRACTION = 0.60
# Android masks already crop the adaptive canvas. 0.60 caused the mark to
# occupy only a small portion of the final launcher circle on One UI.
ADAPTIVE_ARTWORK_FRACTION = 0.92
LEGACY_ARTWORK_FRACTION = 0.86

def safe_canvas(artwork, pixels, background):
    from PIL import Image
    canvas = Image.new("RGBA", (pixels, pixels), background)
    side = round(pixels * LEGACY_ARTWORK_FRACTION)
    resized = artwork.copy()
    resized.thumbnail((side, side), Image.Resampling.LANCZOS)
    canvas.alpha_composite(resized, ((pixels - resized.width) // 2, (pixels - resized.height) // 2))
    return canvas

def foreground_canvas(artwork, pixels):
    from PIL import Image
    canvas = Image.new("RGBA", (pixels, pixels), (0, 0, 0, 0))
    side = round(pixels * ADAPTIVE_ARTWORK_FRACTION)
    resized = artwork.copy()
    resized.thumbnail((side, side), Image.Resampling.LANCZOS)
    canvas.alpha_composite(resized, ((pixels - resized.width) // 2, (pixels - resized.height) // 2))
    return canvas


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
        # Remove transparent-only margins without altering the artwork.
        alpha_bbox = rgba.getchannel("A").getbbox()
        if alpha_bbox is None:
            raise SystemExit("Approved master PNG has no visible artwork")
        rgba = rgba.crop(alpha_bbox)
        print(f"Visible artwork bounds: {alpha_bbox}")
        res = root / "TMessagesProj_App" / "src" / "main" / "res"
        # Derive a neutral edge color from the approved source itself.
        # The full artwork is preserved, but inset to the Android safe zone.
        background = rgba.getpixel((0, 0))
        if background[3] != 255:
            background = (4, 37, 42, 255)
        for density, px in SIZES.items():
            folder = res / f"mipmap-{density}"
            folder.mkdir(parents=True, exist_ok=True)
            scaled = safe_canvas(rgba, px, background)
            for name in ("nabdhgram_launcher.png", "nabdhgram_launcher_round.png"):
                scaled.save(folder / name, format="PNG", optimize=True)
        splash_dir = res / "values-v31"
        splash_dir.mkdir(parents=True, exist_ok=True)
        (splash_dir / "nabdhgram_splash.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<resources><style name="Theme.TMessages.Start" parent="Theme.AppCompat.Light">'
            '<item name="android:windowActionBar">false</item>'
            '<item name="android:windowNoTitle">true</item>'
            '<item name="android:windowSplashScreenAnimatedIcon">@drawable/nabdhgram_launcher_foreground</item>'
            '<item name="android:windowSplashScreenBackground">#04252A</item>'
            '</style></resources>\n', encoding="utf-8"
        )
        drawable = res / "drawable-nodpi"
        drawable.mkdir(parents=True, exist_ok=True)
        foreground_canvas(rgba, 1080).save(
            drawable / "nabdhgram_launcher_foreground.png", format="PNG", optimize=True
        )
        values = res / "values"
        values.mkdir(parents=True, exist_ok=True)
        (values / "nabdhgram_launcher_colors.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<resources><color name="nabdhgram_launcher_background">#%02X%02X%02X</color></resources>\n'
            % background[:3], encoding="utf-8"
        )
        anydpi = res / "mipmap-anydpi-v26"
        anydpi.mkdir(parents=True, exist_ok=True)
        for name in ("nabdhgram_launcher.xml", "nabdhgram_launcher_round.xml"):
            (anydpi / name).write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <background android:drawable="@color/nabdhgram_launcher_background" />\n'
                '    <foreground android:drawable="@drawable/nabdhgram_launcher_foreground" />\n'
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
        # The launcher resolves an enabled activity-alias, not just the
        # application icon. Explicitly brand the enabled DefaultIcon alias.
        library_manifest = root / "TMessagesProj" / "src" / "main" / "AndroidManifest.xml"
        library_xml = library_manifest.read_text(encoding="utf-8")
        import re
        alias_pattern = r'<activity-alias\b[^>]*android:name="org\.telegram\.messenger\.DefaultIcon"[^>]*>'
        alias_match = re.search(alias_pattern, library_xml, re.DOTALL)
        if alias_match is None:
            raise SystemExit("Expected enabled DefaultIcon launcher alias not found")
        alias = alias_match.group(0)
        if 'android:icon=' in alias or 'android:roundIcon=' in alias:
            raise SystemExit("Unexpected existing DefaultIcon alias icon; inspect upstream changes")
        alias = alias[:-1] + (
            ' android:icon="@mipmap/nabdhgram_launcher"'
            ' android:roundIcon="@mipmap/nabdhgram_launcher_round">'
        )
        library_xml = library_xml[:alias_match.start()] + alias + library_xml[alias_match.end():]
        library_manifest.write_text(library_xml, encoding="utf-8")
        print("DefaultIcon launcher activity-alias now explicitly uses NabdhGram artwork.")

        print("Debug manifest launcher resources: nabdhgram_launcher / nabdhgram_launcher_round")
    print("Approved NabdhGram launcher artwork integrated; verify adaptive icon crop on device.")

if __name__ == "__main__":
    main()
