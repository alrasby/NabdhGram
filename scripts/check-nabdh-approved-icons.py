#!/usr/bin/env python3
"""Fail before Gradle if the six approved launcher variants are incomplete."""
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
    ("original", "NabdhOriginalIcon", "NabdhIconOriginal"),
    ("circular", "NabdhCircularIcon", "NabdhIconCircular"),
]
retired = ("NabdhDarkIcon", "NabdhLightIcon", "NabdhTealIcon", "NabdhHexIcon")
for legacy in retired:
    assert ('android:name="org.telegram.messenger.' + legacy + '"') in manifest, "Legacy alias migration must preserve installed launchers"
    assert ('"' + legacy + '"') not in java[java.index("public enum LauncherIcon"):], "Retired launcher must not remain selectable"
assert "nabdhRetireOldAliases();" in java, "Missing old launcher alias recovery"

# Sources must come from the two images attached by the owner, not
# regenerated from the older transparent emblem on each CI run.
approved = {
    "original": ("nabdh-icon-iphone.webp", "761ce91a05bfabde67b4e6d3548b1191236386b4a703e81fbf2bf6b3e0e92f54"),
    "circular": ("nabdh-icon-circular.webp", "4825e302f7c4945503f4f6ec97ef8ae05d626aae839b4bc13c5d23b2d8c71b8c"),
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
    # Four removed legacy aliases temporarily use the surviving iPhone
    # artwork to recover launchers on existing installations during upgrade.
    expected = 1 + len(retired) if slug == "original" else 1
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
assert "NABDH_CIRCULAR" in java and "NOX" in java, "Native icon choices accidentally replaced"
assert java.index('NABDH_ORIGINAL("NabdhOriginalIcon"') > java.index('DEFAULT("DefaultIcon"'), "Original choice should follow default"
assert java.index('NABDH_CIRCULAR("NabdhCircularIcon"') < java.index('VINTAGE("VintageIcon"'), "Approved art must be visible before optional Telegram icons"
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
print("PASS: two selectable launcher aliases, resource labels and every Android density")
