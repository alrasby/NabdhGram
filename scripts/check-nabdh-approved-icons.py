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
assert "NABDH_HEX" in java and "NOX" in java, "Native icon choices accidentally replaced"
assert java.index('NABDH_ORIGINAL("NabdhOriginalIcon"') > java.index('DEFAULT("DefaultIcon"'), "Original choice should follow default"
assert java.index('NABDH_HEXAGONAL("NabdhHexIcon"') < java.index('VINTAGE("VintageIcon"'), "Approved art must be visible before optional Telegram icons"
# The Android 12+ OS startup animation uses Theme.TMessages.Start from
# TMessagesProj/res/values-v31/styles.xml, not a launcher alias. Keep it
# branded even on cold start after the app icon picker changes alias.
styles = (res / "values-v31/styles.xml").read_text(encoding="utf-8")
assert '<item name="android:windowSplashScreenAnimatedIcon">@drawable/nabdhgram_launcher_foreground</item>' in styles, "Native Android 12 splash still references Telegram logo"
assert '<item name="android:windowSplashScreenAnimatedIcon">@drawable/tg_splash_320</item>' not in styles, "Official Telegram launch splash must not return"
assert '<item name="android:windowSplashScreenBackground">#04252A</item>' in styles, "Native Android 12 splash background mismatches NabdhGram brand"
native_splash = res / "drawable-nodpi/nabdhgram_launcher_foreground.png"
app_splash = root / "TMessagesProj_App/src/main/res/drawable-nodpi/nabdhgram_launcher_foreground.png"
assert native_splash.is_file() and app_splash.is_file(), "Approved splash foreground missing from native or app module"
import hashlib
assert hashlib.sha256(native_splash.read_bytes()).digest() == hashlib.sha256(app_splash.read_bytes()).digest(), "Native and app startup foreground art must match"
with Image.open(native_splash) as image:
    image.load()
    assert image.size == (1080, 1080) and image.mode in ("RGBA", "P"), "Splash foreground must be centered transparent approved PNG"
    rgba = image.convert("RGBA")
    assert rgba.getpixel((0, 0))[3] == 0 and rgba.getpixel((540, 540))[3] > 0, "Splash emblem must be visible and within Android mask"
manifest_start = 'android:theme="@style/Theme.TMessages.Start"'
assert manifest_start in manifest, "Native Telegram launch theme no longer applied"
app_style = (root / "TMessagesProj_App/src/main/res/values-v31/nabdhgram_splash.xml").read_text(encoding="utf-8")
assert '@drawable/nabdhgram_launcher_foreground' in app_style, "App-level Android 12 style reverts startup icon"
print("PASS: six selectable launcher aliases, resource labels and every Android density")
