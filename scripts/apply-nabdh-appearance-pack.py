#!/usr/bin/env python3
"""Install functional Appearance/Language groups and licensed original icon variants.

This late overlay reuses Telegram theme, locale, launcher-icon and emoji paths;
the only new native integration is a safe notification smallIcon drawable swap.
"""
from pathlib import Path
import sys
from xml.sax.saxutils import escape

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-appearance-pack.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
source = Path(__file__).resolve().parents[1] / "overlay/java"

def once(body, old, replacement, label):
    if body.count(old) != 1:
        raise SystemExit(f"Appearance {label}: expected exactly one anchor, got {body.count(old)}")
    return body.replace(old, replacement, 1)

for src, dest in (
    ("NabdhAppearancePrefs.java", "Components/NabdhAppearancePrefs.java"),
    ("NabdhAppearancePickerActivity.java", "NabdhAppearancePickerActivity.java"),
):
    target = ui / dest
    if target.exists():
        raise SystemExit("Appearance overlay class collision: " + str(target))
    target.write_bytes((source / src).read_bytes())

manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
anchor = '        <activity android:name="org.telegram.ui.NabdhBrowserActivity"'
m = once(m, anchor,
    '''        <activity android:name="org.telegram.ui.NabdhAppearancePickerActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
''' + anchor, "private appearance picker activity")
manifest.write_text(m, encoding="utf-8")

vectors = {
    # Original filled + stroke artwork; no external/restricted icon pack assets.
    "shield": ("M12,2 L21,6 L20,14 L12,22 L4,14 L3,6 Z", "M8,12 L11,15 L16,9"),
    "privacy": ("M12,3 C7,3 4,6 4,11 L4,17 L8,21 L16,21 L20,17 L20,11 C20,6 17,3 12,3 Z", "M9,12 L12,15 L16,10"),
    "productivity": ("M3,5 L10,5 L12,8 L21,8 L21,20 L3,20 Z", "M6,12 L18,12 M6,16 L15,16"),
    "language": ("M4,4 L20,4 L20,20 L4,20 Z", "M7,9 L17,9 M12,6 L12,18 M8,15 L16,15"),
    "network": ("M3,5 C8,2 16,2 21,5 L21,19 C16,22 8,22 3,19 Z", "M6,10 L18,10 M6,14 L18,14 M12,6 L12,18"),
    "ai": ("M12,2 L17,5 L20,10 L20,15 L16,20 L8,20 L4,15 L4,10 L7,5 Z", "M9,10 L15,10 M9,14 L15,14"),
    "browser": ("M12,2 C6,2 2,6 2,12 C2,18 6,22 12,22 C18,22 22,18 22,12 C22,6 18,2 12,2 Z", "M3,12 L21,12 M12,3 L12,21 M6,6 L18,18"),
    "camera": ("M4,7 L7,7 L9,4 L15,4 L17,7 L20,7 L20,20 L4,20 Z", "M8,13 C8,7 16,7 16,13 C16,19 8,19 8,13 Z"),
    "feed": ("M5,3 L19,3 L19,21 L5,21 Z", "M8,7 L16,7 M8,11 L16,11 M8,15 L16,15"),
    "lock": ("M5,11 L19,11 L19,21 L5,21 Z", "M8,11 L8,8 C8,1 16,1 16,8 L16,11 M12,14 L12,18"),
    "swipe": ("M3,9 L20,9 L16,5 M20,9 L16,13", "M21,16 L4,16 L8,12 M4,16 L8,20"),
}
drawables = root / "TMessagesProj/src/main/res/drawable"
for name, (filled, stroke) in vectors.items():
    file = drawables / ("nabdh_alt_" + name + ".xml")
    if file.exists():
        raise SystemExit("Appearance vector conflict: " + str(file))
    file.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android" '
        'android:width="24dp" android:height="24dp" '
        'android:viewportWidth="24" android:viewportHeight="24">\n'
        '  <path android:pathData="' + filled + '" '
        'android:fillColor="#FFFFFFFF" android:fillAlpha="0.22" '
        'android:strokeColor="#FFFFFFFF" android:strokeWidth="1.2" '
        'android:strokeLineCap="round" android:strokeLineJoin="round"/>\n'
        '  <path android:pathData="' + stroke + '" '
        'android:fillColor="@android:color/transparent" '
        'android:strokeColor="#FFFFFFFF" android:strokeWidth="1.8" '
        'android:strokeLineCap="round" android:strokeLineJoin="round"/>\n'
        '</vector>\n', encoding="utf-8")

status = drawables / "nabdh_notification_symbol.xml"
if status.exists():
    raise SystemExit("Appearance status icon conflict")
status.write_text(
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<vector xmlns:android="http://schemas.android.com/apk/res/android" '
    'android:width="24dp" android:height="24dp" '
    'android:viewportWidth="24" android:viewportHeight="24">\n'
    '  <path android:pathData="M3,5 L21,5 L21,16 L16,16 L12,21 L8,16 L3,16 Z" '
    'android:fillColor="@android:color/transparent" '
    'android:strokeColor="#FFFFFFFF" android:strokeWidth="1.8" '
    'android:strokeLineJoin="round"/>\n'
    '  <path android:pathData="M7,13 L7,8 L10,13 L10,8 '
    'M17,9 C15,7 13,9 13,11 C13,14 17,14 17,11 L15,11" '
    'android:fillColor="@android:color/transparent" '
    'android:strokeColor="#FFFFFFFF" android:strokeWidth="1.7" '
    'android:strokeLineCap="round" android:strokeLineJoin="round"/>\n'
    '</vector>\n', encoding="utf-8")

page = ui / "NabdhGramFeatureCategoryActivity.java"
s = page.read_text(encoding="utf-8")
entry = """        if (featureId == 0) {
            addNabdhFeatureMenu(context, content);
        }"""
replacement = """        if (featureId == 0 && titleRes == R.string.NabdhLanguageTitle) {
            nabdhAppearanceLanguageMenu(context, content);
        } else if (featureId == 0) {
            addNabdhFeatureMenu(context, content);
        }"""
s = once(s, entry, replacement, "appearance nested category routing")
anchor = "    private int nabdhCategoryDescription() {"
methods = r'''    private void nabdhAppearancePicker(Context context, String kind) {
        android.content.Intent intent = new android.content.Intent(context,
                NabdhAppearancePickerActivity.class);
        intent.putExtra(NabdhAppearancePickerActivity.EXTRA_KIND, kind);
        context.startActivity(intent);
    }

    private void nabdhAppearanceLanguageMenu(Context context, LinearLayout content) {
        org.telegram.ui.Components.NabdhCompactSettings.header(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceTextIcons));
        nabdhFeatureRow(context, content, 601);
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceIconPacks),
                NabdhStrings.get(context, R.string.NabdhAppearanceIconPacksInfo),
                R.drawable.nabdh_tool_browser,
                () -> nabdhAppearancePicker(context, NabdhAppearancePickerActivity.ICON_PACKS));
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceEmojis),
                NabdhStrings.get(context, R.string.NabdhAppearanceEmojisInfo),
                R.drawable.settings_chat,
                () -> nabdhAppearancePicker(context, NabdhAppearancePickerActivity.EMOJI_SETS));
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceLauncher),
                NabdhStrings.get(context, R.string.NabdhAppearanceLauncherInfo),
                R.drawable.settings_features,
                () -> presentFragment(new ThemeActivity(ThemeActivity.THEME_TYPE_BASIC)));
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceNotification),
                NabdhStrings.get(context, R.string.NabdhAppearanceNotificationInfo),
                R.drawable.nabdh_alt_ai,
                () -> nabdhAppearancePicker(context,
                        NabdhAppearancePickerActivity.NOTIFICATION_ICON));

        org.telegram.ui.Components.NabdhCompactSettings.header(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceThemesGroup));
        nabdhFeatureRow(context, content, 602);

        org.telegram.ui.Components.NabdhCompactSettings.header(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceLanguageGroup));
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceLanguage),
                NabdhStrings.get(context, R.string.NabdhAppearanceLanguageInfo),
                R.drawable.settings_language,
                () -> presentFragment(new LanguageSelectActivity()));
        nabdhFeatureRow(context, content, 401);
        nabdhFeatureRow(context, content, 402);

        org.telegram.ui.Components.NabdhCompactSettings.header(context, content,
                NabdhStrings.get(context, R.string.NabdhAppearanceBackupGroup));
        nabdhFeatureRow(context, content, 603);
    }

'''
s = once(s, anchor, methods + anchor, "grouped appearance layout")
page.write_text(s, encoding="utf-8")

messages = {
    "values": {
        "NabdhAppearanceTextIcons": "Text and icons",
        "NabdhAppearanceIconPacks": "Icon style",
        "NabdhAppearanceIconPacksInfo": "Classic or Nabdh Duotone for NabdhGram tools",
        "NabdhAppearanceEmojis": "Emoji set",
        "NabdhAppearanceEmojisInfo": "Telegram or Android system emojis",
        "NabdhAppearanceLauncher": "App icon",
        "NabdhAppearanceLauncherInfo": "Telegram's built-in launcher icon chooser",
        "NabdhAppearanceNotification": "Notification icon",
        "NabdhAppearanceNotificationInfo": "Independent monochrome status icon",
        "NabdhAppearanceThemesGroup": "Themes and colors",
        "NabdhAppearanceLanguageGroup": "Language and content",
        "NabdhAppearanceLanguage": "App language",
        "NabdhAppearanceLanguageInfo": "Change Telegram's in-app interface language",
        "NabdhAppearanceBackupGroup": "Settings backup",
    },
    "values-ar": {
        "NabdhAppearanceTextIcons": "النصوص والأيقونات",
        "NabdhAppearanceIconPacks": "حزم الأيقونات",
        "NabdhAppearanceIconPacksInfo": "الكلاسيكية أو نبض ثنائية اللون لأدوات نبض جرام",
        "NabdhAppearanceEmojis": "حزم الإيموجي",
        "NabdhAppearanceEmojisInfo": "إيموجي Telegram أو نظام Android",
        "NabdhAppearanceLauncher": "أيقونة التطبيق",
        "NabdhAppearanceLauncherInfo": "اختيار الأيقونة عبر واجهة Telegram الحالية",
        "NabdhAppearanceNotification": "أيقونة الإشعارات",
        "NabdhAppearanceNotificationInfo": "أيقونة مستقلة وأحادية اللون لشريط الحالة",
        "NabdhAppearanceThemesGroup": "الثيمات والألوان",
        "NabdhAppearanceLanguageGroup": "اللغة والمحتوى",
        "NabdhAppearanceLanguage": "لغة التطبيق",
        "NabdhAppearanceLanguageInfo": "تغيير لغة واجهة Telegram من داخل التطبيق",
        "NabdhAppearanceBackupGroup": "نسخ الإعدادات",
    }
}
for locale, names in messages.items():
    resource = root / "TMessagesProj/src/main/res" / locale / "nabdh_appearance_pack.xml"
    if resource.exists():
        raise SystemExit("Appearance resource already exists: " + str(resource))
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for name, value in names.items():
        # AAPT parses apostrophes/backslashes after XML parsing; xml.sax.escape
        # alone leaves Telegram's... invalid in Android string resources.
        android_value = value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        lines.append(f'    <string name="{name}">{escape(android_value)}</string>')
    resource.write_text("\n".join(lines + ["</resources>", ""]), encoding="utf-8")

notification = root / "TMessagesProj/src/main/java/org/telegram/messenger/NotificationsController.java"
n = notification.read_text(encoding="utf-8")
old = ".setSmallIcon(R.drawable.notification)"
if n.count(old) != 3:
    raise SystemExit(f"Appearance notification builders: expected 3, got {n.count(old)}")
n = n.replace(old,
    ".setSmallIcon(org.telegram.ui.Components.NabdhAppearancePrefs.notificationIcon("
    "ApplicationLoader.applicationContext))")
notification.write_text(n, encoding="utf-8")
print("PASS: functional grouped appearance choices, original packs, system emoji, "
      "built-in app icons and dynamic notification icon")
