#!/usr/bin/env python3
"""Generated-native appearance acceptance checks; no fake packs or emoji choices."""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-appearance-pack.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main"
java = root / "java/org/telegram"
ui = java / "ui"
page = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
picker = (ui / "NabdhAppearancePickerActivity.java").read_text(encoding="utf-8")
prefs = (ui / "Components/NabdhAppearancePrefs.java").read_text(encoding="utf-8")
renderer = (ui / "Components/NabdhCompactSettings.java").read_text(encoding="utf-8")
notifications = (java / "messenger/NotificationsController.java").read_text(encoding="utf-8")
manifest = (root / "AndroidManifest.xml").read_text(encoding="utf-8")

def check(condition, description):
    if not condition: raise SystemExit("FAIL: appearance " + description)

check('android:name="org.telegram.ui.NabdhAppearancePickerActivity"' in manifest and
      'android:exported="false"' in
      manifest.split('android:name="org.telegram.ui.NabdhAppearancePickerActivity"')[1].split("/>")[0],
      "native picker must remain an unexported internal screen")
check("nabdhAppearanceLanguageMenu(context, content);" in page and
      "titleRes == R.string.NabdhLanguageTitle" in page and
      "nabdhFeatureRow(context, content, 601);" in page and
      "nabdhFeatureRow(context, content, 602);" in page and
      "nabdhFeatureRow(context, content, 603);" in page,
      "Appearance/Language must group existing live fonts, themes and backup")
check("new ThemeActivity(ThemeActivity.THEME_TYPE_BASIC)" in page and
      "new LanguageSelectActivity()" in page,
      "app icon and language must reuse actual Telegram native destinations")
check("NabdhAppearancePickerActivity.ICON_PACKS" in page and
      "NabdhAppearancePickerActivity.EMOJI_SETS" in page and
      "NabdhAppearancePickerActivity.NOTIFICATION_ICON" in page,
      "all three new selection screens must be reachable")
check("NabdhCompactSettings.header(context, content," in page and
      "NabdhAppearanceTextIcons" in page and "NabdhAppearanceThemesGroup" in page and
      "NabdhAppearanceLanguageGroup" in page and
      "NabdhAppearanceBackupGroup" in page,
      "visual section grouping is incomplete")
check("SharedConfig.useSystemEmoji = system;" in picker and
      "SharedConfig.saveConfig();" in picker and
      "if (SharedConfig.useSystemEmoji == system) return;" in picker,
      "emoji selection must change Telegram's real persisted engine")
check("NabdhAppearancePrefs.isDuotone(this)" in picker and
      "NabdhAppearancePrefs.setDuotone(this, true)" in picker and
      "NabdhAppearancePrefs.setDuotone(this, false)" in picker and
      "NabdhAppearancePrefs.icon(context, icon)" in renderer,
      "appearance icon pack must actually change owned interface icons")
check("nbdh_" not in picker and "nabdh_appearance_packs_v1" in prefs,
      "appearance options must use local scoped persistence")
check("NabdhAppearancePrefs.notificationIcon(" in notifications and
      notifications.count("NabdhAppearancePrefs.notificationIcon(") == 3 and
      ".setSmallIcon(R.drawable.notification)" not in notifications and
      "nabdhRefreshLockedNotifications()" in picker,
      "status icon selection must modify all native builders without read receipts")
check("return useNabdhNotification(context)" in prefs and
      "R.drawable.notification;" in prefs,
      "default existing notification icon must remain unchanged")
check("Telegram's own navigation icons remain unchanged" in picker,
      "scope of first-party icon pack must be disclosed")
for name in ("shield","privacy","productivity","language","network","ai",
             "browser","camera","feed","lock","swipe"):
    icon = root / "res/drawable" / ("nabdh_alt_" + name + ".xml")
    check(icon.exists(), "missing original alternative vector " + name)
    check(ET.parse(icon).getroot().tag == "vector", "invalid icon " + name)
notification_icon = root / "res/drawable/nabdh_notification_symbol.xml"
check(notification_icon.exists() and ET.parse(notification_icon).getroot().tag == "vector",
      "no valid local status-bar icon")
for language in ("values","values-ar"):
    f = root / "res" / language / "nabdh_appearance_pack.xml"
    check(f.exists(), "appearance strings absent in " + language)
    labels = {node.get("name"): node.text for node in ET.parse(f).getroot()}
    check(len(labels) == 14 and len(set(labels)) == 14 and
          all(value for value in labels.values()), "incomplete " + language + " label list")
check("AlarmManager" not in picker and "READ_CONTACTS" not in picker and
      "sendMessage(" not in picker,
      "appearance screen cannot monitor chats or trigger send operations")
print("PASS: grouped native Appearance/Language, 2 real original icon styles, "
      "Telegram/system emojis, existing launcher icons and dynamic status icons")
