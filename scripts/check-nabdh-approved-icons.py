#!/usr/bin/env python3
"""Fail before Gradle unless all three owner-supplied circular icons are exact."""
from pathlib import Path
import sys
from PIL import Image, ImageChops
import hashlib

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-approved-icons.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
res = root / "TMessagesProj/src/main/res"
java = (root / "TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java").read_text(encoding="utf-8")
manifest = (root / "TMessagesProj/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
names = [
    ("silver", "NabdhSilverCircleIcon", "NabdhIconSilverCircle"),
    ("dark", "NabdhDarkCircleIcon", "NabdhIconDarkCircle"),
    ("glass", "NabdhGlassCircleIcon", "NabdhIconGlassCircle"),
]
retired = ("NabdhDarkIcon", "NabdhLightIcon", "NabdhTealIcon", "NabdhHexIcon",
           "NabdhOriginalIcon", "NabdhCircularIcon")
for legacy in retired:
    assert ('android:name="org.telegram.messenger.' + legacy + '"') in manifest, "Legacy alias migration must preserve installed launchers"
    assert ('"' + legacy + '"') not in java[java.index("public enum LauncherIcon"):], "Retired launcher must not remain selectable"
assert "nabdhRetireOldAliases();" in java, "Missing old launcher alias recovery"

# Default MUST be NabdhGram as well, not Telegram's native paper-plane.
# The chooser thumbnail and enabled DefaultIcon launcher must refer to the
# same approved artwork; all Android densities must have matching pixels.
assert ('DEFAULT("DefaultIcon", R.drawable.nabdh_icon_preview_background, '
        'R.mipmap.nabdh_icon_default, R.string.AppIconDefault)') in java, (
        "Default icon picker is still showing Telegram")
assert ('DEFAULT("DefaultIcon", R.drawable.icon_background_sa, '
        'R.mipmap.icon_foreground_sa') not in java, (
        "Official Telegram Default preview unexpectedly returned")
default_start = manifest.index('android:name="org.telegram.messenger.DefaultIcon"')
default_element = manifest[manifest.rfind("<activity-alias", 0, default_start):
                           manifest.index(">", default_start) + 1]
assert 'android:icon="@mipmap/nabdhgram_launcher"' in default_element, (
    "Default launcher alias is not branded")
assert 'android:roundIcon="@mipmap/nabdhgram_launcher_round"' in default_element, (
    "Default round launcher alias is not branded")
app_res = root / "TMessagesProj_App/src/main/res"
for density, pixels in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96),
                        ("xxhdpi", 144), ("xxxhdpi", 192)):
    preview = res / ("mipmap-" + density) / "nabdh_icon_default.png"
    launcher = app_res / ("mipmap-" + density) / "nabdhgram_launcher.png"
    with Image.open(preview) as a, Image.open(launcher) as b:
        a.load()
        b.load()
        assert a.size == b.size == (pixels, pixels)
        assert ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getbbox() is None, (
            "Default picker differs from the actual NabdhGram launcher: " + density)
        # Legacy installer/launcher fallback must already display our rounded
        # logo even before the user ever opens Settings -> App Icon.
        fallback = app_res / ("mipmap-" + density) / "ic_launcher.png"
        with Image.open(fallback) as first_install:
            assert ImageChops.difference(
                first_install.convert("RGBA"), b.convert("RGBA")).getbbox() is None, (
                "Initial launcher still uses Telegram artwork: " + density)
        assert b.convert("RGBA").getpixel((0, 0))[3] == 0, (
            "Legacy icon has opaque square corners: " + density)
adaptive = app_res / "mipmap-anydpi-v26/nabdhgram_launcher.xml"
assert adaptive.is_file(), "Default adaptive launcher resource missing"
assert "<adaptive-icon" in adaptive.read_text(encoding="utf-8"), (
    "Default launcher lost Android adaptive behavior")
for alias in ("ic_launcher.xml", "ic_launcher_round.xml"):
    fallback = app_res / "mipmap-anydpi-v26" / alias
    assert fallback.is_file(), "Modern first-install fallback missing: " + alias
    assert fallback.read_bytes() == adaptive.read_bytes(), (
        "Modern default launcher fallback still differs from NabdhGram: " + alias)
# Both release and debug config manifests must use branded resources.
config_root = root / "TMessagesProj/config"
for config_manifest in config_root.rglob("AndroidManifest*.xml"):
    content = config_manifest.read_text(encoding="utf-8")
    assert 'android:icon="@mipmap/ic_launcher"' not in content, (
        "Unbranded launcher left in config manifest: " + str(config_manifest))
    assert 'android:roundIcon="@mipmap/ic_launcher_round"' not in content, (
        "Unbranded round launcher left in config manifest: " + str(config_manifest))


# Source hashes prevent future builds silently replacing the user's logos.
approved = {
    "silver": ("nabdh-icon-silver-circle.webp", "f0092210e0197f166ed5c63d9afdab52e63f2aadd074b59a432b5572da88d78b"),
    "dark": ("nabdh-icon-dark-circle.webp", "dff202b15e3c1ebebf793a9bfd780aee2c11e09a4e58929b9d4f975ae0271295"),
    "glass": ("nabdh-icon-glass-circle.webp", "56b17a8681c68f2f1941c929baeff085505ba5544cb304ed287ee7e4ea8c2657"),
}
for slug, (name, expected_hash) in approved.items():
    source = Path(__file__).resolve().parents[1] / "branding/approved" / name
    assert source.is_file(), "Missing uploaded icon " + name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_hash, "Icon source content changed " + name
    with Image.open(source) as image:
        image.load()
        assert image.size == (192, 192) and image.format == "WEBP"
        rgba = image.convert("RGBA")
        assert rgba.getchannel("A").getextrema() == (0, 255), "Icon transparency lost: " + name
        with Image.open(res / "mipmap-xxxhdpi" / ("nabdh_icon_" + slug + ".png")) as built:
            assert ImageChops.difference(rgba, built.convert("RGBA")).getbbox() is None, "Android icon changed from supplied source: " + name

for slug, alias, label in names:
    assert ('"' + alias + '"') in java, "Missing icon enum " + alias
    assert ('R.mipmap.nabdh_icon_' + slug) in java, "Missing picker image " + slug
    assert ('android:name="org.telegram.messenger.' + alias + '"') in manifest, "Missing launcher alias " + alias
    # Six retired aliases reference surviving silver artwork for safe migration.
    expected = 1 + len(retired) if slug == "silver" else 1
    assert manifest.count('android:icon="@mipmap/nabdh_icon_' + slug + '"') == expected, "Alias icon count mismatch " + slug
    for density, pixels in (("mdpi",48),("hdpi",72),("xhdpi",96),("xxhdpi",144),("xxxhdpi",192)):
        p = res / ("mipmap-" + density) / ("nabdh_icon_" + slug + ".png")
        with Image.open(p) as image:
            image.load()
            assert image.size == (pixels, pixels), "Wrong size for " + str(p)
    for locale in ("values", "values-ar"):
        text = (res / locale / "nabdhgram_icon_variants.xml").read_text(encoding="utf-8")
        assert ('name="' + label + '"') in text, "Missing label " + locale + " " + slug
assert "pm.getActivityInfo(target, PackageManager.MATCH_DISABLED_COMPONENTS);" in java, "Disabled aliases wrongly filtered from PackageManager"
assert "pm.getActivityInfo(target, 0)" not in java, "Old disabled-alias lookup must not be packaged"
assert "public static boolean nabdhSetIconVerified(LauncherIcon icon)" in java, "Launcher switch must return verified result"
assert "pm.getComponentEnabledSetting(target)" in java, "Launcher switch must verify target enabled state"
assert "PackageManager.COMPONENT_ENABLED_STATE_ENABLED" in java, "Selected launcher alias must be enabled"
assert "PackageManager.COMPONENT_ENABLED_STATE_DISABLED" in java, "Previous launcher aliases must be disabled"
selector = (root / "TMessagesProj/src/main/java/org/telegram/ui/Cells/AppIconsSelectorCell.java").read_text(encoding="utf-8")
assert "if (!LauncherIconController.nabdhSetIconVerified(icon))" in selector, "Chooser still reports success on a failed switch"
assert 'context.getString(R.string.NabdhIconApplyFailed)' in selector, "Chooser must disclose actual icon-switch failure"
for locale in ("values", "values-ar"):
    localized = (res / locale / "nabdhgram_icon_variants.xml").read_text(encoding="utf-8")
    assert 'name="NabdhIconApplyFailed"' in localized, "Missing localized icon change failure"
assert all(("NABDH_" + slug.upper()) in java for slug in ("silver", "dark", "glass")) and "NOX" in java, "Three owner choices and Telegram originals must remain"
assert java.index('NABDH_SILVER("NabdhSilverCircleIcon"') > java.index('DEFAULT("DefaultIcon"'), "First circular choice should follow default"
assert java.index('NABDH_GLASS("NabdhGlassCircleIcon"') < java.index('VINTAGE("VintageIcon"'), "Three circular choices must be visible before Telegram icons"
# The Android 12+ OS startup animation uses Theme.TMessages.Start from
# TMessagesProj/res/values-v31/styles.xml, not a launcher alias. Keep it
# branded even on cold start after the app icon picker changes alias.
styles = (res / "values-v31/styles.xml").read_text(encoding="utf-8")
assert '<item name="android:windowSplashScreenAnimatedIcon">@drawable/nabdhgram_launcher_foreground</item>' in styles, "Native Android 12 splash still references Telegram logo"
assert '<item name="android:windowSplashScreenAnimatedIcon">@drawable/tg_splash_320</item>' not in styles, "Official Telegram launch splash must not return"
assert '<item name="android:windowSplashScreenBackground">#04252A</item>' in styles, "Native Android 12 splash background mismatches NabdhGram brand"
night = (res / "values-night/styles.xml").read_text(encoding="utf-8")
assert '<item name="android:windowSplashScreenAnimatedIcon">@drawable/nabdhgram_launcher_foreground</item>' in night, "Native night startup still renders official Telegram mark"
assert '<item name="android:windowSplashScreenAnimatedIcon">@drawable/tg_splash_320</item>' not in night, "Unbranded Telegram startup persists in night qualifier"
assert '<item name="android:windowSplashScreenBackground">#04252A</item>' in night, "Night splash background differs from approved palette"

native_splash = res / "drawable-nodpi/nabdhgram_launcher_foreground.png"
app_splash = root / "TMessagesProj_App/src/main/res/drawable-nodpi/nabdhgram_launcher_foreground.png"
assert native_splash.is_file() and app_splash.is_file(), "Approved splash foreground missing from native or app module"
import hashlib
assert hashlib.sha256(native_splash.read_bytes()).digest() == hashlib.sha256(app_splash.read_bytes()).digest(), "Native and app startup foreground art must match"
with Image.open(native_splash) as image:
    image.load()
    assert image.size == (1080, 1080) and image.mode in ("RGBA", "P"), "Splash foreground must be centered transparent approved PNG"
    rgba = image.convert("RGBA")
    bounds = rgba.getchannel("A").getbbox()
    assert rgba.getpixel((0, 0))[3] == 0 and bounds is not None, "Splash mark must be nonempty and transparent outside"
    assert 100 < bounds[0] < bounds[2] < 980 and 100 < bounds[1] < bounds[3] < 980, "Splash logo exceeds Android safe region"
manifest_start = 'android:theme="@style/Theme.TMessages.Start"'
assert manifest_start in manifest, "Native Telegram launch theme no longer applied"
app_style = (root / "TMessagesProj_App/src/main/res/values-v31/nabdhgram_splash.xml").read_text(encoding="utf-8")
assert '@drawable/nabdhgram_launcher_foreground' in app_style, "App-level Android 12 style reverts startup icon"
print("PASS: NabdhGram Default picker matches adaptive launcher and three approved variants retain their artwork")
