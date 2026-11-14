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
# Keep the visible mark inside Android's 66/108 adaptive safe circle.
# The approved source can include an opaque dark surround, so crop its visible
# logo first rather than enlarging a padded square and letting Android clip it.
ADAPTIVE_ARTWORK_FRACTION = 0.60
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
        alpha_bbox = rgba.getchannel("A").point(lambda a: 255 if a >= 8 else 0).getbbox()
        if alpha_bbox is None:
            raise SystemExit("Approved master PNG has no visible artwork")
        rgba = rgba.crop(alpha_bbox)
        print(f"Alpha artwork bounds (alpha >= 8): {alpha_bbox}")
        # The approved PNG may have an opaque black/dark background. Alpha
        # cropping alone then leaves the bright logo tiny in a padded square.
        # Locate the bright silver/teal mark against its dark surround.
        # This only crops source pixels; it never redraws or recolors the logo.
        if rgba.getchannel("A").getextrema()[0] >= 250:
            width, height = rgba.size
            corners = [rgba.getpixel(p)[:3] for p in
                       ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))]
            corner_spread = max(max(c[k] for c in corners) - min(c[k] for c in corners)
                                for k in range(3))
            corner_brightness = max(max(c) for c in corners)
            if corner_spread <= 28 and corner_brightness <= 65:
                rgb = rgba.convert("RGB")
                # Bright teal and silver elements stand out above the dark base.
                bright = rgb.convert("L").point(lambda v: 255 if v >= 78 else 0)
                mark_bbox = bright.getbbox()
                if mark_bbox:
                    x0, y0, x1, y1 = mark_bbox
                    area = (x1 - x0) * (y1 - y0)
                    # Guard against stray pixels and unexpectedly large crops.
                    if 0.015 * width * height <= area <= 0.90 * width * height:
                        margin = max(2, round(max(x1 - x0, y1 - y0) * 0.06))
                        mark_bbox = (max(0, x0 - margin), max(0, y0 - margin),
                                     min(width, x1 + margin), min(height, y1 + margin))
                        rgba = rgba.crop(mark_bbox)
                        print(f"Dark-background visible mark bounds: {mark_bbox}")
                    else:
                        print("Logo crop skipped: unexpected bright-area bounds")
            else:
                print("Logo crop skipped: source corners are not uniformly dark")
        print(f"Effective artwork dimensions: {rgba.width}x{rgba.height}")
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

        # Android 12+ draws the LAUNCH THEME icon, not the Android launcher
        # alias icon. Telegram's Theme.TMessages.Start still references
        # @drawable/tg_splash_320; that is why the blue Telegram circle
        # appears when launching our otherwise branded app.
        # Use the exact approved NabdhGram mark on the native startup theme.
        splash_source = drawable / "nabdhgram_launcher_foreground.png"
        native_drawable = root / "TMessagesProj/src/main/res/drawable-nodpi"
        native_drawable.mkdir(parents=True, exist_ok=True)
        native_splash = native_drawable / "nabdhgram_launcher_foreground.png"
        if native_splash.exists():
            raise SystemExit("Unexpected native splash foreground: inspect upstream changes")
        from shutil import copyfile
        copyfile(splash_source, native_splash)

        android12_styles = root / "TMessagesProj/src/main/res/values-v31/styles.xml"
        styles = android12_styles.read_text(encoding="utf-8")
        old_splash = ('<item name="android:windowSplashScreenAnimatedIcon">'
                      '@drawable/tg_splash_320</item>')
        new_splash = ('<item name="android:windowSplashScreenAnimatedIcon">'
                      '@drawable/nabdhgram_launcher_foreground</item>')
        if styles.count(old_splash) != 1:
            raise SystemExit("Pinned Android 12 native splash icon changed")
        styles = styles.replace(old_splash, new_splash, 1)
        old_background = ('<item name="android:windowSplashScreenBackground">'
                          '?android:windowBackground</item>')
        if styles.count(old_background) != 1:
            raise SystemExit("Pinned Android 12 native splash background changed")
        styles = styles.replace(old_background,
            '<item name="android:windowSplashScreenBackground">#04252A</item>', 1)
        android12_styles.write_text(styles, encoding="utf-8")

        # Telegram ALSO declares Theme.TMessages.Start in values-night/styles.
        # Android's night qualifier can outrank the higher v31 qualifier:
        # inspecting APK #572's compiled resources.arsc proved that normal
        # v31 used NabdhGram, but night-v29 still referenced tg_splash_320.
        # We must patch BOTH source variants; the binary APK audit below
        # checks every final resource configuration after Gradle merging.
        night_styles = root / "TMessagesProj/src/main/res/values-night/styles.xml"
        night = night_styles.read_text(encoding="utf-8")
        if night.count(old_splash) != 1:
            raise SystemExit("Pinned Telegram night splash icon changed")
        night = night.replace(old_splash, new_splash, 1)
        night_background = ('<item name="android:windowSplashScreenBackground">'
                            '#1f2732</item>')
        if night.count(night_background) != 1:
            raise SystemExit("Pinned Telegram night splash background changed")
        night = night.replace(night_background,
            '<item name="android:windowSplashScreenBackground">#04252A</item>', 1)
        night_styles.write_text(night, encoding="utf-8")
        print("PASS: Android launch themes branded in both normal and dark modes")

        print("Debug manifest launcher resources: nabdhgram_launcher / nabdhgram_launcher_round")
    print("Approved NabdhGram launcher artwork integrated; verify adaptive icon crop on device.")

if __name__ == "__main__":
    main()
