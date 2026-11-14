#!/usr/bin/env python3
"""Match NabdhGram resources and layout to Telegram's in-app locale.

Telegram's language choice may differ from Android's device language, so
Context.getString() on these custom resources can show English in Arabic UI.
This script runs after all generated feature screens and Glass overlays.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-locale-polish.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main"
java = root / "java/org/telegram/ui"
strings = java / "NabdhStrings.java"
strings.write_text("""package org.telegram.ui;

import android.content.Context;
import android.content.res.Configuration;
import java.util.Locale;
import org.telegram.messenger.LocaleController;

/** Resources for the locale selected inside Telegram, not Android settings. */
public final class NabdhStrings {
    private NabdhStrings() {}

    public static String get(Context context, int resId) {
        Locale selected = LocaleController.getInstance().getCurrentLocale();
        // Android's resource locale may differ from Telegram's selected UI
        // language. For Arabic UI, force our own values-ar resources even
        // when the fragment's Activity still has an English configuration.
        if (LocaleController.isRTL && (selected == null
                || "en".equals(selected.getLanguage()))) {
            selected = new Locale("ar");
        }
        if (selected == null) return context.getString(resId);
        Configuration config = new Configuration(context.getResources().getConfiguration());
        config.setLocale(selected);
        config.setLayoutDirection(selected);
        return context.createConfigurationContext(config).getString(resId);
    }
}
""", encoding="utf-8")

for filename in ("NabdhGramSettingsActivity.java", "NabdhGramFeatureCategoryActivity.java"):
    p = java / filename
    s = p.read_text(encoding="utf-8")
    count = s.count("context.getString(")
    # Glass settings already resolves app locale through nabdhText(); the only
    # remaining direct lookup may be its fallback. One lookup is valid.
    if count < 1:
        raise SystemExit(f"Missing NabdhGram locale fallback in {filename}")
    # Route every NabdhGram-owned label through one explicit language
    # resolver, including page titles and nested headings.
    s = s.replace("nabdhText(context, ", "NabdhStrings.get(context, ")
    s = s.replace("context.getString(", "NabdhStrings.get(context, ")
    if filename == "NabdhGramSettingsActivity.java":
        title = "actionBar.setTitle(NabdhStrings.get(context, R.string.NabdhGramSettingsTitle));"
    else:
        title = "actionBar.setTitle(NabdhStrings.get(context, titleRes));"
    if s.count(title) != 1:
        raise SystemExit(f"Active-locale settings title missing: {filename}")
    if "heading.setText(NabdhStrings.get(context, titleRes));" not in s and filename == "NabdhGramSettingsActivity.java":
        raise SystemExit("NabdhGram card headings did not use the selected language")
    anchor = "        content.setOrientation(LinearLayout.VERTICAL);"
    if s.count(anchor) != 1:
        raise SystemExit(f"Missing RTL container anchor in {filename}")
    s = s.replace(anchor, anchor + """
        // In-app Telegram language, independent of Android's device locale.
        content.setLayoutDirection(org.telegram.messenger.LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);""", 1)
    p.write_text(s, encoding="utf-8")
    print(f"Localized {filename}: {count} resource lookups")

settings = java / "SettingsActivity.java"
s = settings.read_text(encoding="utf-8")
pattern = r"getParentActivity\(\)\.getString\(R\.string\.(NabdhGram\w+|NabdhShield\w+)\)"
s, replaced = re.subn(pattern, lambda m:
    "NabdhStrings.get(getParentActivity(), R.string." + m.group(1) + ")", s)
if replaced not in (0, 3):
    raise SystemExit(f"Partially localized NabdhGram settings entry labels: {replaced}")
if replaced == 0 and "NabdhStrings.get(getParentActivity()," not in s:
    raise SystemExit("NabdhGram settings entry labels were not localized")
# Keep upstream's experimental options, but give the heading the active UI language.
old = 'UItem.asHeader("Experimental")'
if s.count(old) == 1:
    s = s.replace(old, 'UItem.asHeader(org.telegram.messenger.LocaleController.isRTL ? "خيارات تجريبية" : "Experimental")', 1)
elif 'UItem.asHeader(getString(R.string.SettingsExperimental))' in s:
    # Telegram 13.2.2 already uses its own translated string resource.
    # Avoid replacing the native dynamic locale with a hard-coded title.
    pass
elif "خيارات تجريبية" not in s:
    raise SystemExit("Telegram Experimental header is neither original nor localized")
settings.write_text(s, encoding="utf-8")

dialogs = java / "DialogsActivity.java"
s = dialogs.read_text(encoding="utf-8")
old = "context.getString(section == 1"
if s.count(old) != 1:
    raise SystemExit("Pinned/other chat section locale anchor changed")
s = s.replace(old, "NabdhStrings.get(context, section == 1", 1)
dialogs.write_text(s, encoding="utf-8")

for lang, old, new in (
    ("values", "Planned: Glass themes, fonts and personalization. Not enabled yet.", "Choose the application font below. Lightweight Glass styling is active; additional personalization options are in development."),
    ("values-ar", "قيد التطوير: ثيمات Glass والخطوط وخيارات التخصيص. لم تُفعّل بعد.", "اختر خط التطبيق أدناه. تصميم Glass الخفيف مفعّل، وخيارات التخصيص الإضافية قيد التطوير."),
):
    p = root / "res" / lang / "nabdhgram_settings.xml"
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        raise SystemExit(f"Appearance description missing in {lang}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("Localized NabdhGram pages, section labels and Experimental heading.")
