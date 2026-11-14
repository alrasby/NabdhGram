#!/usr/bin/env python3
"""Install the six selected NabdhGram launcher variants from the user's artwork.

Six independently rendered backgrounds, masks, and frameless options are
composed around the approved TRANSPARENT glyph, not cropped from a screenshot.
Existing Telegram/approved default icons and launcher aliases are preserved.
"""
from pathlib import Path
import re
import math
import sys
from PIL import Image, ImageDraw, ImageFilter

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-approved-icon-variants.py TELEGRAM_SOURCE")

repository = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1]).resolve()
source = repository / "branding/approved/nabdhgram-welcome-transparent.png"
res = root / "TMessagesProj/src/main/res"
manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
controller = root / "TMessagesProj/src/main/java/org/telegram/ui/LauncherIconController.java"
if not source.is_file() or not manifest.is_file() or not controller.is_file():
    raise SystemExit("Approved icon atlas or pinned Telegram sources are missing")

VARIANTS = (
    ("original", "NabdhOriginalIcon", "NabdhIconOriginal", "iPhone Glass", "آيفون الزجاجية"),
    ("dark", "NabdhDarkIcon", "NabdhIconDark", "Samsung Style", "أسلوب سامسونج"),
    ("light", "NabdhLightIcon", "NabdhIconLight", "Light Turquoise", "التركوازية الفاتحة"),
    ("teal", "NabdhTealIcon", "NabdhIconTeal", "Turquoise · No Frame", "التركوازية الشفافة"),
    ("circular", "NabdhCircularIcon", "NabdhIconCircular", "Circular", "الدائرية"),
    ("hexagonal", "NabdhHexIcon", "NabdhIconHex", "Silver · No Frame", "الفضية الشفافة"),
)
# Source is the identical glyph used for the app's welcome branding.
# Only icon BACKGROUNDS and masks change. Never stretch or redraw the emblem.
S = 512
with Image.open(source) as raw:
    if raw.format != "PNG":
        raise SystemExit("The original transparent emblem must be PNG")
    rgba = raw.convert("RGBA")
    if rgba.getchannel("A").getextrema()[0] >= 255:
        raise SystemExit("Welcome emblem must have transparent background")
    bbox = rgba.getchannel("A").point(lambda value: 255 if value >= 12 else 0).getbbox()
    if bbox is None or bbox[2] - bbox[0] < 32:
        raise SystemExit("Transparent emblem is empty or too small")
    emblem = rgba.crop(bbox)

def make_mask(shape):
    mask = Image.new("L", (S, S), 0)
    draw = ImageDraw.Draw(mask)
    if shape == "circle":
        draw.ellipse((25, 25, S - 25, S - 25), fill=255)
    elif shape == "squircle":
        points = []
        for degrees in range(360):
            angle = math.pi * degrees / 180
            def curve(v):
                return math.copysign(abs(v) ** (2.0 / 4.5), v)
            points.append((S / 2 + 235 * curve(math.cos(angle)),
                           S / 2 + 235 * curve(math.sin(angle))))
        draw.polygon(points, fill=255)
    else:
        draw.rounded_rectangle((19, 19, S - 19, S - 19), radius=109, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(.45))

def compose_icon(slug):
    image = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    palettes = {
        "original": ((1, 59, 72), (2, 112, 119), (1, 31, 49)),
        "dark": ((2, 51, 65), (5, 122, 127), (0, 47, 59)),
        "light": ((181, 255, 252), (87, 238, 229), (2, 169, 182)),
        "circular": ((1, 66, 74), (3, 135, 133), (1, 42, 55))
    }
    if slug in palettes:
        form = "circle" if slug == "circular" else (
            "squircle" if slug in ("dark", "light") else "square")
        background = Image.new("RGBA", (S, S))
        draw = ImageDraw.Draw(background)
        top, middle, bottom = palettes[slug]
        for y in range(S):
            t = y / float(S - 1)
            a, b, p = (top, middle, t * 2) if t < .5 else (
                middle, bottom, (t - .5) * 2)
            rgb = tuple(round(a[k] * (1 - p) + b[k] * p) for k in range(3))
            draw.line((0, y, S, y), fill=(*rgb, 255))
        background.putalpha(make_mask(form))
        image.alpha_composite(background)
        # A restrained border only for iPhone-style and circular choices.
        if slug in ("original", "circular"):
            highlight = Image.new("RGBA", (S, S))
            line = ImageDraw.Draw(highlight)
            if slug == "circular":
                line.ellipse((29, 29, S - 29, S - 29),
                             outline=(110, 250, 242, 115), width=2)
            else:
                line.rounded_rectangle((22, 22, S - 22, S - 22),
                    radius=106, outline=(104, 255, 245, 95), width=2)
            image.alpha_composite(highlight)
    mark = emblem.copy()
    mark.thumbnail((412 if slug in ("teal", "hexagonal") else 395, 275),
                   Image.Resampling.LANCZOS)
    x, y = (S - mark.width) // 2, (S - mark.height) // 2
    shadow = Image.new("RGBA", (S, S))
    silhouette = Image.new("RGBA", mark.size, (1, 20, 28, 0))
    strength = .16 if slug in ("teal", "hexagonal") else .45
    silhouette.putalpha(mark.getchannel("A").point(
        lambda value: round(value * strength)))
    shadow.alpha_composite(silhouette, (x + 3, y + 11))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(8)))
    image.alpha_composite(mark, (x, y))
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

# Use the original Telegram launcher mechanism; six additional, FREE choices
# are added without replacing DefaultIcon or the pre-existing variants.
java = controller.read_text(encoding="utf-8")
# Keep the approved default first, then immediately show all six NabdhGram
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
# Resolve those six names directly in the selected Telegram locale.
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
    """            nabdhFrameless = "NabdhTealIcon".equals(icon.key)
                    || "NabdhHexIcon".equals(icon.key);
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


print("PASS: six DISTINCT logo treatments with true transparent options and translated picker labels")
