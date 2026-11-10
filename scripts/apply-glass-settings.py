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
        """scroll.setBackground(new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] {
                    Theme.getColor(Theme.key_windowBackgroundGray),
                    Theme.getColor(Theme.key_windowBackgroundWhite)
                }));""", 1)
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
                new int[] {surface, Theme.getColor(Theme.key_windowBackgroundGray)});
        glassCard.setCornerRadius(22 * context.getResources().getDisplayMetrics().density);
        glassCard.setStroke((int) (context.getResources().getDisplayMetrics().density),
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        // Preserve the rounded surface while giving every navigable category
        // a native pressed ripple, keyboard focus and accessibility feedback.
        android.graphics.drawable.RippleDrawable touchSurface =
                new android.graphics.drawable.RippleDrawable(
                        android.content.res.ColorStateList.valueOf(
                                dark ? 0x3346D9D2 : 0x2200878D),
                        glassCard, null);
        card.setBackground(touchSurface);
        card.setClipToOutline(true);""", 1)
# Replace simple heading color with brand turquoise while retaining readability.
anchor = "heading.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));"
if s.count(anchor) != 1:
    raise SystemExit("Expected one feature card title anchor")
s = s.replace(anchor, "heading.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));", 1)
# Extra card spacing and smaller outer padding; category pages still own their options.
# Compact the six navigation cards while keeping touch targets accessible.
layout_anchor = "        int d = (int) (16 * context.getResources().getDisplayMetrics().density);"
if s.count(layout_anchor) != 1:
    raise SystemExit("NabdhGram settings inner card spacing changed")
s = s.replace(layout_anchor,
              "        int d = (int) (12 * context.getResources().getDisplayMetrics().density);", 1)
card_init = "        LinearLayout card = new LinearLayout(context);"
if s.count(card_init) != 1:
    raise SystemExit("NabdhGram category card constructor changed")
s = s.replace(card_init,
    '        boolean gridCard = "nabdhGridRow".equals(parent.getTag());\n' + card_init, 1)
card_lp = "        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);"
if s.count(card_lp) != 1:
    raise SystemExit("NabdhGram category card layout changed")
s = s.replace(card_lp, """        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(gridCard ? 0 : -1, -2);
        if (gridCard) {
            lp.weight = 1f;
            int gap = (int) (4 * context.getResources().getDisplayMetrics().density);
            if (parent.getChildCount() == 0) lp.setMarginEnd(gap);
            else lp.setMarginStart(gap);
            card.setMinimumHeight((int) (148 * context.getResources().getDisplayMetrics().density));
        }""", 1)
for before, after in (
    ("        heading.setTextSize(18);",
     "        heading.setTextSize(gridCard ? 16 : 18);\\n        heading.setMaxLines(gridCard ? 2 : 3);\\n        heading.setEllipsize(android.text.TextUtils.TruncateAt.END);"),
    ("        description.setTextSize(14);",
     "        description.setTextSize(gridCard ? 12 : 14);\\n        description.setMaxLines(gridCard ? 2 : 3);\\n        description.setEllipsize(android.text.TextUtils.TruncateAt.END);"),
):
    if s.count(before) != 1:
        raise SystemExit("NabdhGram card text style anchor changed: " + before)
    s = s.replace(before, after.replace("\\n", "\n"), 1)

outer_anchor = "        int pad = (int) (20 * context.getResources().getDisplayMetrics().density);"
if s.count(outer_anchor) != 1:
    raise SystemExit("NabdhGram settings outer padding changed")
s = s.replace(outer_anchor,
              "        int pad = (int) (12 * context.getResources().getDisplayMetrics().density);", 1)
gap_anchor = "        lp.bottomMargin = d;"
if s.count(gap_anchor) != 1:
    raise SystemExit("NabdhGram settings card gap changed")
s = s.replace(gap_anchor, "        lp.bottomMargin = d / 2;", 1)
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
# Native icon-backed Glass category headers. Reuse Telegram artwork rather
# than inventing emoji/icon fonts, and preserve each card's action semantics.
header_anchor = "        card.addView(heading);"
if s.count(header_anchor) != 1:
    raise SystemExit("NabdhGram card heading anchor changed")
s = s.replace(header_anchor, """        // NabdhGram Glass: category icon + headline in one adaptive row.
        // Existing native icons follow the active .attheme accent.
        int iconRes = titleRes == R.string.NabdhShieldTitle ? R.drawable.settings_privacy
                : titleRes == R.string.NabdhPrivacyTitle ? R.drawable.settings_devices
                : titleRes == R.string.NabdhProductivityTitle ? R.drawable.settings_folders
                : titleRes == R.string.NabdhLanguageTitle ? R.drawable.settings_language
                : titleRes == R.string.NabdhNetworkTitle ? R.drawable.settings_data
                : R.drawable.settings_chat;
        int iconSize = (int) (44 * context.getResources().getDisplayMetrics().density);
        int innerSize = (int) (25 * context.getResources().getDisplayMetrics().density);
        LinearLayout titleRow = new LinearLayout(context);
        titleRow.setOrientation(gridCard ? LinearLayout.VERTICAL : LinearLayout.HORIZONTAL);
        titleRow.setGravity(android.view.Gravity.CENTER_VERTICAL);
        titleRow.setLayoutDirection(org.telegram.messenger.LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        android.widget.FrameLayout iconFrame = new android.widget.FrameLayout(context);
        GradientDrawable iconGlass = new GradientDrawable();
        iconGlass.setColor(Theme.getColor(Theme.key_windowBackgroundGray));
        iconGlass.setCornerRadius(iconSize * 0.30f);
        iconGlass.setStroke(Math.max(1, (int) context.getResources().getDisplayMetrics().density),
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        iconFrame.setBackground(iconGlass);
        android.widget.ImageView categoryIcon = new android.widget.ImageView(context);
        categoryIcon.setImageResource(iconRes);
        categoryIcon.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        iconFrame.addView(categoryIcon,
                new android.widget.FrameLayout.LayoutParams(innerSize, innerSize, android.view.Gravity.CENTER));
        titleRow.addView(iconFrame, new LinearLayout.LayoutParams(iconSize, iconSize));
        LinearLayout.LayoutParams titleParams = gridCard
                ? new LinearLayout.LayoutParams(-1, -2)
                : new LinearLayout.LayoutParams(0, -2, 1f);
        int titleGap = (int) (12 * context.getResources().getDisplayMetrics().density);
        if (gridCard) titleParams.topMargin = titleGap / 2;
        else if (org.telegram.messenger.LocaleController.isRTL) titleParams.rightMargin = titleGap;
        else titleParams.leftMargin = titleGap;
        titleRow.addView(heading, titleParams);
        // Consistent affordance on both Arabic and English cards; decorative
        // only so touch handling stays on the existing parent card.
        TextView chevron = new TextView(context);
        chevron.setText(org.telegram.messenger.LocaleController.isRTL ? "‹" : "›");
        chevron.setTextSize(25);
        chevron.setAlpha(0.62f);
        chevron.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        chevron.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        if (!gridCard) titleRow.addView(chevron,
                new LinearLayout.LayoutParams(-2, -2));
        card.addView(titleRow);""", 1)

# Build responsive rows without assuming the six category invocations are
# adjacent: the upstream NabdhGram page also contains privacy controls and
# other generated content between some sections.
calls = [
    ("NabdhShieldTitle", "NabdhShieldExplanation"),
    ("NabdhPrivacyTitle", "NabdhPrivacyExplanation"),
    ("NabdhProductivityTitle", "NabdhProductivityExplanation"),
    ("NabdhLanguageTitle", "NabdhLanguageExplanation"),
    ("NabdhNetworkTitle", "NabdhNetworkExplanation"),
    ("NabdhAppearanceTitle", "NabdhAppearanceExplanation"),
]
first = f"        section(context, content, R.string.{calls[0][0]}, R.string.{calls[0][1]});"
if s.count(first) != 1:
    raise SystemExit("NabdhGram first category entry changed")
grid_setup = """        boolean compactGrid = context.getResources().getConfiguration().screenWidthDp >= 360
                && context.getResources().getConfiguration().fontScale <= 1.15f;
        LinearLayout[] nabdhRows = null;
        if (compactGrid) {
            nabdhRows = new LinearLayout[3];
            for (int idx = 0; idx < nabdhRows.length; idx++) {
                LinearLayout row = new LinearLayout(context);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setLayoutDirection(org.telegram.messenger.LocaleController.isRTL
                        ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
                row.setTag("nabdhGridRow");
                content.addView(row, new LinearLayout.LayoutParams(-1, -2));
                nabdhRows[idx] = row;
            }
        }
"""
s = s.replace(first, grid_setup + first, 1)
for idx, (title, description) in enumerate(calls):
    old = f"section(context, content, R.string.{title}, R.string.{description});"
    new = f"section(context, compactGrid ? nabdhRows[{idx // 2}] : content, R.string.{title}, R.string.{description});"
    if s.count(old) != 1:
        raise SystemExit(f"NabdhGram category entry changed: {title}")
    s = s.replace(old, new, 1)

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
        "Appearance": "Glass appearance and application fonts • Available",
    },
    "values-ar": {
        "Shield": "أمان الروابط والملفات • قيد التطوير",
        "Privacy": "شاشة الخصوصية • جدولة الرسائل",
        "Productivity": "التنظيم والتركيز • قيد التطوير",
        "Language": "الترجمة والصوت • قيد التطوير",
        "Network": "الاتصال والتنزيلات • قيد التطوير",
        "Appearance": "مظهر Glass وخطوط التطبيق • متاحان",
    },
}
for lang, mapping in summaries.items():
    res = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    xml = res.read_text(encoding="utf-8")
    if xml.count("</resources>") != 1:
        raise SystemExit(f"Unexpected XML resources in {res}")
    entries = "".join(f'    <string name="NabdhGlass{k}Summary">{escape(v)}</string>\n' for k, v in mapping.items())
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
                new int[] {base, Theme.getColor(Theme.key_windowBackgroundGray)});
        infoCard.setCornerRadius(22 * context.getResources().getDisplayMetrics().density);
        infoCard.setStroke((int) context.getResources().getDisplayMetrics().density,
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        explanation.setPadding(pad, pad, pad, pad);
        explanation.setBackground(infoCard);
        content.addView(explanation);""", 1)
# Add a working, locally persisted typography preference to the Appearance page.
# This changes only NabdhGram-owned settings views, not Telegram chat text.
anchor = "        content.addView(explanation);"
if s.count(anchor) != 1:
    raise SystemExit("Expected category explanation insertion point")
s = s.replace(anchor, anchor + """
        if (titleRes == R.string.NabdhAppearanceTitle) {
            // Dedicated static Glass surface: no blur, no animated gradients.
            LinearLayout fontCard = new LinearLayout(context);
            fontCard.setOrientation(LinearLayout.VERTICAL);
            int fontPad = (int) (18 * context.getResources().getDisplayMetrics().density);
            fontCard.setPadding(fontPad, fontPad, fontPad, fontPad);
            GradientDrawable fontGlass = new GradientDrawable(
                    GradientDrawable.Orientation.TL_BR,
                    new int[] {Theme.getColor(Theme.key_windowBackgroundWhite),
                            Theme.getColor(Theme.key_windowBackgroundGray)});
            fontGlass.setCornerRadius(22 * context.getResources().getDisplayMetrics().density);
            fontGlass.setStroke((int) context.getResources().getDisplayMetrics().density,
                    Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
            fontCard.setBackground(fontGlass);
            TextView fontTitle = new TextView(context);
            fontTitle.setText(context.getString(R.string.NabdhFontTitle));
            fontTitle.setTextSize(18);
            fontTitle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            LinearLayout.LayoutParams fontParams = new LinearLayout.LayoutParams(-1, -2);
            fontParams.topMargin = (int) (18 * context.getResources().getDisplayMetrics().density);
            content.addView(fontCard, fontParams);
            fontCard.addView(fontTitle);
            android.widget.RadioGroup choices = new android.widget.RadioGroup(context);
            choices.setOrientation(android.widget.RadioGroup.VERTICAL);
            android.content.SharedPreferences prefs = context.getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE);
            String selectedFont = prefs.getString("font_family", "readex-pro");
            String[] families = {"readex-pro", "vazirmatn", "noto-sans-arabic", "tajawal", "rubik", "sans-serif", "serif"};
            int[] names = {R.string.NabdhFontReadex, R.string.NabdhFontVazirmatn,
                    R.string.NabdhFontNotoSansArabic, R.string.NabdhFontTajawal,
                    R.string.NabdhFontRubik, R.string.NabdhFontSans, R.string.NabdhFontSerif};
            String[] assets = {"ReadexPro.ttf", "Vazirmatn.ttf", "NotoSansArabic.ttf",
                    "Tajawal.ttf", "Rubik.ttf", null, null};
            android.graphics.Typeface[] fonts = new android.graphics.Typeface[families.length];
            for (int i = 0; i < families.length; i++) {
                if (assets[i] != null) {
                    try {
                        fonts[i] = android.graphics.Typeface.createFromAsset(context.getAssets(), "fonts/" + assets[i]);
                    } catch (RuntimeException missingFont) {
                        fonts[i] = android.graphics.Typeface.DEFAULT;
                    }
                } else {
                    fonts[i] = android.graphics.Typeface.create(families[i], android.graphics.Typeface.NORMAL);
                }
            }
            // Re-layout visible labels immediately after a typography setting changes.
            final Runnable refreshTypography = () -> {
                // Preferences are displayed as fragments inside LaunchActivity.
                // A fragment navigation does not invoke Activity.onResume().
                if (org.telegram.ui.LaunchActivity.instance != null) {
                    org.telegram.ui.LaunchActivity.instance.nabdhRefreshAllFonts();
                } else if (context instanceof android.app.Activity) {
                    android.view.View decor = ((android.app.Activity) context).getWindow().getDecorView();
                    decor.requestLayout();
                    decor.invalidate();
                }
            };
            final Runnable refreshDrawnText = () -> {
                // Telegram has cached TextPaint/StaticLayout for chat labels.
                // Update known paints before the same notification it uses for
                // theme-driven cell invalidation; retain the active theme.
                android.graphics.Typeface regular = org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rregular.ttf");
                android.graphics.Typeface bold = org.telegram.messenger.AndroidUtilities.bold();
                if (Theme.dialogs_namePaint != null) {
                    for (android.text.TextPaint paint : Theme.dialogs_namePaint) {
                        if (paint != null) paint.setTypeface(bold);
                    }
                }
                if (Theme.dialogs_messagePaint != null) {
                    for (android.text.TextPaint paint : Theme.dialogs_messagePaint) {
                        if (paint != null) paint.setTypeface(regular);
                    }
                }
                // These chat messages are canvas TextPaint, not TextViews.
                // Keep their existing point sizes and emoji fallback behavior.
                if (Theme.chat_msgTextPaint != null) Theme.chat_msgTextPaint.setTypeface(regular);
                if (Theme.chat_replyTextPaint != null) Theme.chat_replyTextPaint.setTypeface(regular);
                if (Theme.chat_quoteTextPaint != null) Theme.chat_quoteTextPaint.setTypeface(regular);
                if (Theme.chat_explanationTextPaint != null) Theme.chat_explanationTextPaint.setTypeface(regular);
                org.telegram.messenger.NotificationCenter.getGlobalInstance().postNotificationName(
                        org.telegram.messenger.NotificationCenter.didSetNewTheme, false, false);
            };
            for (int i = 0; i < families.length; i++) {
                final String family = families[i];
                final android.graphics.Typeface selectedTypeface = fonts[i];
                android.widget.RadioButton option = new android.widget.RadioButton(context);
                option.setId(View.generateViewId());
                option.setText(context.getString(names[i]));
                option.setTextSize(16);
                option.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
                option.setTypeface(selectedTypeface);
                option.setChecked(family.equals(selectedFont));
                option.setOnClickListener(v -> {
                    // Commit this tiny setting synchronously so immediate app exit
                    // cannot leave the font selection pending on disk.
                    prefs.edit().putString("font_family", family).commit();
                    org.telegram.messenger.AndroidUtilities.mediumTypeface = null;
                    refreshTypography.run();
                    refreshDrawnText.run();
                    fontTitle.setTypeface(selectedTypeface, android.graphics.Typeface.BOLD);
                    explanation.setTypeface(selectedTypeface, android.graphics.Typeface.NORMAL);
                });
                choices.addView(option);
            }
            fontCard.addView(choices);
            TextView note = new TextView(context);
            note.setText(context.getString(R.string.NabdhFontScope));
            note.setTextSize(13);
            note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
            fontCard.addView(note);
            TextView uiSizeTitle = new TextView(context);
            uiSizeTitle.setText(nabdhText(context, R.string.NabdhFontUiSize));
            uiSizeTitle.setTextSize(16);
            uiSizeTitle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            fontCard.addView(uiSizeTitle);
            android.widget.SeekBar uiScale = new android.widget.SeekBar(context);
            uiScale.setMax(30);
            uiScale.setProgress(Math.max(0, Math.min(30, prefs.getInt("ui_scale_percent", 100) - 85)));
            fontCard.addView(uiScale);
            uiScale.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener() {
                @Override public void onProgressChanged(android.widget.SeekBar seekBar, int progress, boolean fromUser) {
                    if (fromUser) {
                        prefs.edit().putInt("ui_scale_percent", progress + 85).apply();
                        refreshTypography.run();
                    }
                }
                @Override public void onStartTrackingTouch(android.widget.SeekBar seekBar) {}
                @Override public void onStopTrackingTouch(android.widget.SeekBar seekBar) {
                    prefs.edit().putInt("ui_scale_percent", seekBar.getProgress() + 85).commit();
                    refreshTypography.run();
                }
            });
            TextView chatSizeTitle = new TextView(context);
            chatSizeTitle.setText(nabdhText(context, R.string.NabdhFontChatSize));
            chatSizeTitle.setTextSize(16);
            chatSizeTitle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            fontCard.addView(chatSizeTitle);
            android.widget.SeekBar chatScale = new android.widget.SeekBar(context);
            chatScale.setMax(8);
            chatScale.setProgress(Math.max(0, Math.min(8, org.telegram.messenger.SharedConfig.fontSize - 14)));
            fontCard.addView(chatScale);
            chatScale.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener() {
                @Override public void onProgressChanged(android.widget.SeekBar seekBar, int progress, boolean fromUser) {}
                @Override public void onStartTrackingTouch(android.widget.SeekBar seekBar) {}
                @Override public void onStopTrackingTouch(android.widget.SeekBar seekBar) {
                    int size = seekBar.getProgress() + 14;
                    org.telegram.messenger.SharedConfig.fontSize = size;
                    org.telegram.messenger.SharedConfig.fontSizeIsDefault = false;
                    context.getSharedPreferences("userconfing", Context.MODE_PRIVATE)
                            .edit().putInt("fons_size", size).commit();
                    refreshTypography.run();
                }
            });
            android.widget.Switch boldOption = new android.widget.Switch(context);
            boldOption.setText(nabdhText(context, R.string.NabdhFontBold));
            boldOption.setTextSize(16);
            boldOption.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            boldOption.setChecked(prefs.getBoolean("font_bold", false));
            boldOption.setOnCheckedChangeListener((button, checked) -> {
                prefs.edit().putBoolean("font_bold", checked).commit();
                org.telegram.messenger.AndroidUtilities.mediumTypeface = null;
                refreshTypography.run();
                refreshDrawnText.run();
            });
            fontCard.addView(boldOption);
            TextView refreshInfo = new TextView(context);
            refreshInfo.setText(nabdhText(context, R.string.NabdhFontRefreshInfo));
            refreshInfo.setTextSize(13);
            refreshInfo.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
            fontCard.addView(refreshInfo);

            for (int i = 0; i < families.length; i++) {
                if (families[i].equals(selectedFont)) {
                    fontTitle.setTypeface(fonts[i], android.graphics.Typeface.BOLD);
                    explanation.setTypeface(fonts[i], android.graphics.Typeface.NORMAL);
                    break;
                }
            }
        }
""", 1)

for lang, labels in {
    "values": ("Application font", "Readex Pro", "Sans-serif", "Serif", "The font is saved and restored when you reopen NabdhGram. Some system-controlled surfaces may retain their own typography.", "Vazirmatn", "Noto Sans Arabic", "Tajawal", "Rubik"),
    "values-ar": ("خط التطبيق", "Readex Pro", "بدون حواف", "بحواف", "يُحفظ الخط المختار ويُستعاد عند فتح نبض جرام. قد تحتفظ بعض عناصر النظام بخطها الخاص.", "وزير متن", "نوتو سانس عربي", "تجوال", "روبيك"),
}.items():
    res = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    xml = res.read_text(encoding="utf-8")
    if xml.count("</resources>") != 1:
        raise SystemExit("Unexpected resource structure for font labels")
    keys = ("NabdhFontTitle", "NabdhFontReadex", "NabdhFontSans", "NabdhFontSerif", "NabdhFontScope", "NabdhFontVazirmatn", "NabdhFontNotoSansArabic", "NabdhFontTajawal", "NabdhFontRubik")
    extra = "".join('    <string name="' + k + '">' + escape(v).replace("'", "\\'") + '</string>\n' for k, v in zip(keys, labels))
    res.write_text(xml.replace("</resources>", extra + "</resources>", 1), encoding="utf-8")
for locale, texts in {
    "values": ("Outside chats · text size", "Inside chats · text size", "Bold text", "Reopen chats after changing their text size. The selected values are kept when you restart the app."),
    "values-ar": ("حجم الخط خارج المحادثات", "حجم الخط داخل المحادثات", "خط عريض", "أعد فتح المحادثة بعد تغيير حجم خطها. تُحفظ اختياراتك بعد إعادة تشغيل التطبيق."),
}.items():
    f = root / "TMessagesProj/src/main/res" / locale / "nabdhgram_settings.xml"
    xml = f.read_text(encoding="utf-8")
    extra = "".join('    <string name="' + key + '">' + escape(value) + '</string>\n'
        for key, value in zip(("NabdhFontUiSize", "NabdhFontChatSize",
                               "NabdhFontBold", "NabdhFontRefreshInfo"), texts))
    f.write_text(xml.replace("</resources>", extra + "</resources>", 1), encoding="utf-8")
child.write_text(s, encoding="utf-8")

# Telegram's in-app language may differ from Android's device language.
# Resolve NabdhGram-owned resources using the locale selected in Telegram.
for target in pages:
    java_source = target.read_text(encoding="utf-8")
    class_name = "NabdhGramSettingsActivity" if target == main else "NabdhGramFeatureCategoryActivity"
    class_anchor = "public class " + class_name + " extends BaseFragment {"
    if java_source.count(class_anchor) != 1:
        raise SystemExit("NabdhGram settings localization class changed: " + class_name)
    resolver = """    private static String nabdhText(Context context, int resId) {
        java.util.Locale selected = org.telegram.messenger.LocaleController.getInstance().getCurrentLocale();
        if (selected == null) {
            return context.getString(resId);
        }
        android.content.res.Configuration config =
                new android.content.res.Configuration(context.getResources().getConfiguration());
        config.setLocale(selected);
        return context.createConfigurationContext(config).getString(resId);
    }

"""
    java_source = java_source.replace(class_anchor, class_anchor + "\n" + resolver, 1)
    # Rewrite only app-owned texts; system labels retain Telegram's own localizer.
    java_source = java_source.replace("context.getString(", "nabdhText(context, ")
    # Restore the resolver's fallback to avoid recursion.
    java_source = java_source.replace("return nabdhText(context, resId);", "return context.getString(resId);")
    target.write_text(java_source, encoding="utf-8")

print("Applied localized Glass typography controls and settings cards.")
