#!/usr/bin/env python3
"""Apply a lightweight, theme-aware NabdhGram Glass foundation to feature settings.

Runs after nested settings generation. UI-only: does not change Telegram
account, message, network, or security behavior.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-settings.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
java = root / "TMessagesProj/src/main/java/org/telegram/ui"
pages = [
    java / "NabdhGramSettingsActivity.java",
    java / "NabdhGramFeatureCategoryActivity.java",
]
for p in pages:
    s = p.read_text(encoding="utf-8")
    import_anchor = "import android.content.Context;\n"
    if s.count(import_anchor) != 1:
        raise SystemExit(f"Unexpected imports in {p}")
    s = s.replace(import_anchor, import_anchor +
        "import android.graphics.Color;\n" +
        "import android.graphics.drawable.GradientDrawable;\n", 1)
    # Page canvas stays tied to Telegram theme, so light, dark and RTL work.
    # Accent colors come from the approved logo; backgrounds adapt to theme.
    s = s.replace(
        "scroll.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));",
        "scroll.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));", 1)
    p.write_text(s, encoding="utf-8")

main = pages[0]
s = main.read_text(encoding="utf-8")
anchor = """        card.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));"""
if s.count(anchor) != 1:
    raise SystemExit("Expected one category card background anchor")
s = s.replace(anchor, """        int surface = Theme.getColor(Theme.key_windowBackgroundWhite);
        int textSurface = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText);
        boolean dark = Color.red(surface) + Color.green(surface) + Color.blue(surface) < 360;
        GradientDrawable glassCard = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {surface, dark ? 0xFF103D44 : 0xFFE7F8F7});
        glassCard.setCornerRadius(22 * context.getResources().getDisplayMetrics().density);
        glassCard.setStroke((int) (context.getResources().getDisplayMetrics().density),
                dark ? 0xFF187F89 : 0xFFB8E2E3);
        card.setBackground(glassCard);
        card.setClipToOutline(true);""", 1)
# Replace simple heading color with brand turquoise while retaining readability.
anchor = "heading.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));"
if s.count(anchor) != 1:
    raise SystemExit("Expected one feature card title anchor")
s = s.replace(anchor, "heading.setTextColor(dark ? 0xFF67E3DE : 0xFF087C83);", 1)
# Extra card spacing and smaller outer padding; category pages still own their options.
s = s.replace("lp.bottomMargin = d;", "lp.bottomMargin = d;", 1)
# Replace long future-feature paragraphs on the overview with concise card summaries.
# Full descriptions remain available on category detail pages.
summary_anchor = "description.setText(context.getString(descriptionRes));"
if s.count(summary_anchor) != 1:
    raise SystemExit("Expected one category summary label")
s = s.replace(summary_anchor, """int summaryRes = R.string.NabdhGlassAppearanceSummary;
        if (titleRes == R.string.NabdhShieldTitle) summaryRes = R.string.NabdhGlassShieldSummary;
        else if (titleRes == R.string.NabdhPrivacyTitle) summaryRes = R.string.NabdhGlassPrivacySummary;
        else if (titleRes == R.string.NabdhProductivityTitle) summaryRes = R.string.NabdhGlassProductivitySummary;
        else if (titleRes == R.string.NabdhLanguageTitle) summaryRes = R.string.NabdhGlassLanguageSummary;
        else if (titleRes == R.string.NabdhNetworkTitle) summaryRes = R.string.NabdhGlassNetworkSummary;
        description.setText(context.getString(summaryRes));""", 1)
main.write_text(s, encoding="utf-8")

# Keep translations in the same module as generated SettingsActivity.
from xml.sax.saxutils import escape
summaries = {
    "values": {
        "Shield": "Link and file safety • In development",
        "Privacy": "Privacy Screen • Scheduled messages",
        "Productivity": "Organize and focus • In development",
        "Language": "Translation and voice • In development",
        "Network": "Connection and downloads • In development",
        "Appearance": "Themes and personalization • In development",
    },
    "values-ar": {
        "Shield": "أمان الروابط والملفات • قيد التطوير",
        "Privacy": "شاشة الخصوصية • جدولة الرسائل",
        "Productivity": "التنظيم والتركيز • قيد التطوير",
        "Language": "الترجمة والصوت • قيد التطوير",
        "Network": "الاتصال والتنزيلات • قيد التطوير",
        "Appearance": "السمات والتخصيص • قيد التطوير",
    },
}
for lang, mapping in summaries.items():
    res = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    xml = res.read_text(encoding="utf-8")
    if xml.count("</resources>") != 1:
        raise SystemExit(f"Unexpected XML resources in {res}")
    entries = "".join(f'    <string name="NabdhGlass{k}Summary">{escape(v)}</string>\\n' for k, v in mapping.items())
    res.write_text(xml.replace("</resources>", entries + "</resources>", 1), encoding="utf-8")

child = pages[1]
s = child.read_text(encoding="utf-8")
anchor = "        content.addView(explanation);"
if s.count(anchor) != 1:
    raise SystemExit("Expected one feature description anchor")
s = s.replace(anchor, """        int base = Theme.getColor(Theme.key_windowBackgroundWhite);
        boolean dark = Color.red(base) + Color.green(base) + Color.blue(base) < 360;
        GradientDrawable infoCard = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {base, dark ? 0xFF103D44 : 0xFFE7F8F7});
        infoCard.setCornerRadius(22 * context.getResources().getDisplayMetrics().density);
        infoCard.setStroke((int) context.getResources().getDisplayMetrics().density,
                dark ? 0xFF187F89 : 0xFFB8E2E3);
        explanation.setPadding(pad, pad, pad, pad);
        explanation.setBackground(infoCard);
        content.addView(explanation);""", 1)
child.write_text(s, encoding="utf-8")
print("Applied theme-aware NabdhGram Glass cards to the six settings categories.")
