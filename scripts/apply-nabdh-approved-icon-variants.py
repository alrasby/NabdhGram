#!/usr/bin/env python3
"""Install exactly three owner-selected circular launcher variants.

Only the outside of the original circular disks is transparency-masked;
the internal NabdhGram monogram and artwork are never repainted or recolored.
Old launcher aliases remain for safe upgrades but are hidden from the picker.
"""
from pathlib import Path
import re
import sys
from PIL import Image

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-approved-icon-variants.py TELEGRAM_SOURCE")

repository = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1]).resolve()
res = root / "TMessagesProj/src/main/res"
manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
controller = root / "TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java"
if not manifest.is_file() or not controller.is_file():
    raise SystemExit("Pinned Telegram icon sources are missing")

# All three circles were provided by the owner: 44.png, 55.png, 33.png.
# Older Samsung/translucent/square/turquoise choices are retired, not offered.
VARIANTS = (
    ("silver", "NabdhSilverCircleIcon", "NabdhIconSilverCircle", "Silver Circle", "الدائرية الفضية"),
    ("dark", "NabdhDarkCircleIcon", "NabdhIconDarkCircle", "Dark Circle", "الدائرية الداكنة"),
    ("glass", "NabdhGlassCircleIcon", "NabdhIconGlassCircle", "Glass Circle", "الدائرية الزجاجية"),
)
RETIRED = ("NabdhDarkIcon", "NabdhLightIcon", "NabdhTealIcon", "NabdhHexIcon",
           "NabdhOriginalIcon", "NabdhCircularIcon")
USER_SOURCES = {
    "silver": repository / "branding/approved/nabdh-icon-silver-circle.webp",
    "dark": repository / "branding/approved/nabdh-icon-dark-circle.webp",
    "glass": repository / "branding/approved/nabdh-icon-glass-circle.webp",
}
# These WebP sources are 192px owner artwork with transparent exterior only.
def compose_icon(slug):
    selected = USER_SOURCES[slug]
    if not selected.is_file():
        raise SystemExit("Missing user-supplied icon: " + str(selected))
    with Image.open(selected) as icon:
        icon.load()
        if icon.format != "WEBP" or icon.width != 192 or icon.height != 192:
            raise SystemExit("User-approved launcher source must be square WebP 192px")
        image = icon.convert("RGBA")
    if image.getchannel("A").getextrema() != (0, 255):
        raise SystemExit("User icon must have fully transparent outer pixels")
    return image

for slug, _, _, _, _ in VARIANTS:
    icon = compose_icon(slug)
    for density, pixels in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96),
                            ("xxhdpi", 144), ("xxxhdpi", 192)):
        directory = res / ("mipmap-" + density)
        directory.mkdir(parents=True, exist_ok=True)
        icon.resize((pixels, pixels), Image.Resampling.LANCZOS).save(
            directory / ("nabdh_icon_" + slug + ".png"),
            format="PNG", optimize=True)

# Use the original Telegram launcher mechanism; three additional, FREE choices
# are added without replacing DefaultIcon or the pre-existing variants.
java = controller.read_text(encoding="utf-8")
# Keep the approved default first, then immediately show both NabdhGram
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
# Some Android launchers immediately terminate an app when its currently
# enabled launcher alias is disabled, even with DONT_KILL_APP. First enable
# the target component, then disable old aliases; leave the selected one
# enabled throughout. Validate the component exists before mutating any.
old_switch = """        for (LauncherIcon i : LauncherIcon.values()) {
            pm.setComponentEnabledSetting(i.getComponentName(ctx), i == icon ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED :
                    PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
        }"""
new_switch = """        // Preserve the original void method for every upstream caller.
        nabdhSetIconVerified(icon);"""
if java.count(old_switch) != 1:
    raise SystemExit("Pinned launcher component switching changed")
java = java.replace(old_switch, new_switch, 1)
# When the user upgrades from an old icon alias, keep that launcher entry
# available long enough to enable DefaultIcon before retiring the old alias.
recovery = "    public static void tryFixLauncherIconIfNeeded() {"
if java.count(recovery) != 1:
    raise SystemExit("Upstream launcher recovery method changed")
migration = """
    private static void nabdhRetireOldAliases() {
        Context ctx = ApplicationLoader.applicationContext;
        if (ctx == null) return;
        PackageManager pm = ctx.getPackageManager();
        String[] retired = {"NabdhDarkIcon", "NabdhLightIcon",
                "NabdhTealIcon", "NabdhHexIcon",
                "NabdhOriginalIcon", "NabdhCircularIcon"};
        boolean needsMigration = false;
        for (String alias : retired) {
            ComponentName component = new ComponentName(ctx.getPackageName(),
                    "org.telegram.messenger." + alias);
            if (pm.getComponentEnabledSetting(component) ==
                    PackageManager.COMPONENT_ENABLED_STATE_ENABLED) {
                needsMigration = true;
                break;
            }
        }
        if (!needsMigration) return;
        boolean validLauncher = false;
        for (LauncherIcon icon : LauncherIcon.values()) {
            if (isEnabled(icon)) {
                validLauncher = true;
                break;
            }
        }
        if (!validLauncher) {
            pm.setComponentEnabledSetting(LauncherIcon.DEFAULT.getComponentName(ctx),
                    PackageManager.COMPONENT_ENABLED_STATE_ENABLED,
                    PackageManager.DONT_KILL_APP);
        }
        for (String alias : retired) {
            ComponentName component = new ComponentName(ctx.getPackageName(),
                    "org.telegram.messenger." + alias);
            pm.setComponentEnabledSetting(component,
                    PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                    PackageManager.DONT_KILL_APP);
        }
    }

"""
java = java.replace(recovery,
                    migration + recovery + """
        nabdhRetireOldAliases();""", 1)
# The selected alias is disabled in the manifest before its first use.
# PackageManager.getActivityInfo(component, 0) excludes disabled aliases:
# this formerly returned early without enabling the icon, while the picker
# still displayed an unconditional success bulletin. Use the correct query
# flags, and confirm the enabled state before reporting success.
method_anchor = "    public enum LauncherIcon {"
if java.count(method_anchor) != 1:
    raise SystemExit("Pinned launcher enum anchor changed")
verified_method = """    public static boolean nabdhSetIconVerified(LauncherIcon icon) {
        if (icon == null || ApplicationLoader.applicationContext == null) return false;
        Context ctx = ApplicationLoader.applicationContext;
        PackageManager pm = ctx.getPackageManager();
        ComponentName target = icon.getComponentName(ctx);
        try {
            // Every alternate activity-alias starts android:enabled=false.
            // 0 flags HID these aliases, so the old switch silently failed.
            pm.getActivityInfo(target, PackageManager.MATCH_DISABLED_COMPONENTS);
            // Make the replacement launchable BEFORE disabling the old alias.
            pm.setComponentEnabledSetting(target,
                    PackageManager.COMPONENT_ENABLED_STATE_ENABLED,
                    PackageManager.DONT_KILL_APP);
            if (pm.getComponentEnabledSetting(target)
                    != PackageManager.COMPONENT_ENABLED_STATE_ENABLED) return false;
            for (LauncherIcon other : LauncherIcon.values()) {
                if (other != icon && isEnabled(other)) {
                    pm.setComponentEnabledSetting(other.getComponentName(ctx),
                            PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                            PackageManager.DONT_KILL_APP);
                }
            }
            return isEnabled(icon);
        } catch (PackageManager.NameNotFoundException missing) {
            org.telegram.messenger.FileLog.e(missing);
            return false;
        } catch (RuntimeException failure) {
            org.telegram.messenger.FileLog.e(failure);
            // A previously enabled launcher is never disabled before the
            // new alias has been enabled; preserve recoverability.
            return false;
        }
    }

"""
java = java.replace(method_anchor, verified_method + method_anchor, 1)
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
# Compatibility-only aliases: hidden from picker, all branded using
# the surviving silver circle. Retire enabled legacy choice at startup.
for legacy in RETIRED:
    old_alias = template.replace("org.telegram.messenger.VintageIcon",
                                 "org.telegram.messenger." + legacy)
    old_alias = old_alias.replace("@mipmap/icon_6_launcher_round",
                                  "@mipmap/nabdh_icon_silver")
    old_alias = old_alias.replace("@mipmap/icon_6_launcher",
                                  "@mipmap/nabdh_icon_silver")
    new_aliases.append(old_alias)
xml = xml[:end] + "\n\n" + "\n\n".join(new_aliases) + xml[end:]
manifest.write_text(xml, encoding="utf-8")

preview = res / "drawable/nabdh_icon_preview_background.xml"
preview.parent.mkdir(parents=True, exist_ok=True)
preview.write_text(
    '<shape xmlns:android="http://schemas.android.com/apk/res/android" '
    'android:shape="rectangle"><solid android:color="#00000000"/></shape>\n',
    encoding="utf-8")

for folder, label_index in (("values", 3), ("values-ar", 4)):
    directory = res / folder
    directory.mkdir(parents=True, exist_ok=True)
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for _, _, name, en, ar in VARIANTS:
        lines.append('    <string name="' + name + '">' +
                     (en if label_index == 3 else ar) + '</string>')
    lines.append('    <string name="NabdhIconApplyFailed">' +
                 ('Could not change the app icon. Please try again.' if label_index == 3
                  else 'تعذر تغيير أيقونة التطبيق، حاول مرة أخرى.') + '</string>')
    lines.append('</resources>')
    (directory / "nabdhgram_icon_variants.xml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
# AppIconsSelectorCell displays LOC_ERR:null for newly generated R.string IDs
# when using Telegram's legacy LocaleController.getString(int) mapping.
# Resolve their localized names directly in the selected Telegram locale.
selector = root / "TMessagesProj/src/main/java/org/telegram/ui/Cells/AppIconsSelectorCell.java"
selector_src = selector.read_text(encoding="utf-8")
def replace_selector(before, after, label):
    global selector_src
    if selector_src.count(before) != 1:
        raise SystemExit(f"{label}: upstream picker anchor changed")
    selector_src = selector_src.replace(before, after, 1)

replace_selector(
    "                titleView.setText(LocaleController.getString(icon.title));",
    """                titleView.setText(icon.key.startsWith("Nabdh")
                        ? nabdhLocalizedIconTitle(icon) : LocaleController.getString(icon.title));""",
    "New icon title binding")
replace_selector(
    "        private void bind(LauncherIconController.LauncherIcon icon) {",
    """        private String nabdhLocalizedIconTitle(LauncherIconController.LauncherIcon icon) {
            java.util.Locale selected = LocaleController.getInstance().getCurrentLocale();
            if (selected == null) return getContext().getString(icon.title);
            android.content.res.Configuration configuration = new android.content.res.Configuration(
                    getContext().getResources().getConfiguration());
            configuration.setLocale(selected);
            return getContext().createConfigurationContext(configuration).getString(icon.title);
        }

        private void bind(LauncherIconController.LauncherIcon icon) {""",
    "Locale-aware Nabdh icon labels")
replace_selector(
    "        private float progress;",
    "        private float progress;\n        private boolean nabdhFrameless;",
    "Icon preview framing flag")
replace_selector(
    "            canvas.drawRoundRect(AndroidUtilities.rectTmp, AndroidUtilities.dp(ICONS_ROUND_RADIUS), AndroidUtilities.dp(ICONS_ROUND_RADIUS), fillPaint);",
    """            if (!nabdhFrameless) {
                canvas.drawRoundRect(AndroidUtilities.rectTmp, AndroidUtilities.dp(ICONS_ROUND_RADIUS), AndroidUtilities.dp(ICONS_ROUND_RADIUS), fillPaint);
            }""",
    "Transparent preview backplate")
replace_selector(
    "            canvas.drawRoundRect(AndroidUtilities.rectTmp, AndroidUtilities.dp(ICONS_ROUND_RADIUS), AndroidUtilities.dp(ICONS_ROUND_RADIUS), outlinePaint);",
    """            if (!nabdhFrameless || progress > 0.01f) {
                canvas.drawRoundRect(AndroidUtilities.rectTmp, AndroidUtilities.dp(ICONS_ROUND_RADIUS), AndroidUtilities.dp(ICONS_ROUND_RADIUS), outlinePaint);
            }""",
    "Transparent preview outline")
replace_selector(
    "            iconView.setImageResource(icon.background);",
    """            nabdhFrameless = icon.key.startsWith("Nabdh");
            iconView.setOuterPadding(icon.key.startsWith("Nabdh") ? 0 : AndroidUtilities.dp(5));
            iconView.setImageResource(icon.background);""",
    "Native picker transparent drawing")
# Never tell the user "Icon changed" before PackageManager confirms
# the selected alias is enabled. Keep Telegram's original animated chooser.
on_click = "            LauncherIconController.setIcon(icon);"
if selector_src.count(on_click) != 1:
    raise SystemExit("Pinned icon chooser onClick anchor changed")
selector_src = selector_src.replace(on_click,
    """            if (!LauncherIconController.nabdhSetIconVerified(icon)) {
                android.widget.Toast.makeText(context,
                        context.getString(R.string.NabdhIconApplyFailed),
                        android.widget.Toast.LENGTH_LONG).show();
                return;
            }""", 1)
selector.write_text(selector_src, encoding="utf-8")
# The icon-change toast is rendered by AppIconBulletinLayout, not by
# AppIconsSelectorCell. LocaleController's legacy resource map does not
# recognize newly generated string IDs and prints LOC_ERR:null. Resolve
# Nabdh-only titles from the Android resources with selected Telegram locale.
bulletin = root / "TMessagesProj/src/main/java/org/telegram/ui/Components/AppIconBulletinLayout.java"
bulletin_src = bulletin.read_text(encoding="utf-8")
bulletin_old = "LocaleController.getString(icon.title)"
if bulletin_src.count(bulletin_old) != 1:
    raise SystemExit("App icon bulletin title anchor changed")
bulletin_src = bulletin_src.replace(bulletin_old,
    """(icon.key.startsWith("Nabdh") ? nabdhIconTitle(context, icon) : LocaleController.getString(icon.title))""", 1)
bulletin_method = "    public AppIconBulletinLayout(@NonNull Context context,"
if bulletin_src.count(bulletin_method) != 1:
    raise SystemExit("App icon bulletin constructor anchor changed")
bulletin_src = bulletin_src.replace(bulletin_method,
    """    private static String nabdhIconTitle(Context context, LauncherIconController.LauncherIcon icon) {
        java.util.Locale selected = LocaleController.getInstance().getCurrentLocale();
        if (selected == null) return context.getString(icon.title);
        android.content.res.Configuration configuration =
                new android.content.res.Configuration(context.getResources().getConfiguration());
        configuration.setLocale(selected);
        return context.createConfigurationContext(configuration).getString(icon.title);
    }

""" + bulletin_method, 1)
bulletin.write_text(bulletin_src, encoding="utf-8")


print("PASS: three circular owner icons, safe deprecated-alias migration and localized labels")
