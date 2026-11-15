#!/usr/bin/env python3
"""Late, narrowly-scoped renderer refactor for NabdhGram-owned settings.

Runs AFTER all existing overlay generators so it never changes Telegram's
native SettingsActivity, dialogs, network, data, or any feature callbacks.
Fail closed if an expected source method changed on future upstream upgrades.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-compact-settings.py TELEGRAM_SOURCE")

root = Path(sys.argv[1]).resolve()
java = root / "TMessagesProj/src/main/java/org/telegram/ui"
overlay = Path(__file__).resolve().parents[1] / "overlay/java/NabdhCompactSettings.java"
out = java / "Components/NabdhCompactSettings.java"
if out.exists():
    raise SystemExit("Compact settings: unexpected component collision")
out.write_bytes(overlay.read_bytes())

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Compact settings {label}: wanted 1 anchor, found {count}")
    return text.replace(old, new, 1)

def replace_method(text, signature, body, label):
    start = text.find(signature)
    if start < 0 or text.count(signature) != 1:
        raise SystemExit(f"Compact settings {label}: expected one method")
    first = text.find("{", start + len(signature))
    if first < 0:
        raise SystemExit("Compact settings: no method brace: " + label)
    # Count Java braces without treating quoted string content as Java syntax.
    depth, quoted, escaped = 0, None, False
    end = -1
    for i in range(first, len(text)):
        ch = text[i]
        if quoted:
            if escaped: escaped = False
            elif ch == "\\": escaped = True
            elif ch == quoted: quoted = None
            continue
        # Java comments routinely contain apostrophes (e.g. Telegram's).
        # Treat only double-quoted Java string literals as bracket shielding;
        # target UI methods have no brace-valued character literals.
        if ch == '"':
            quoted = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        raise SystemExit("Compact settings unmatched method: " + label)
    return text[:start] + body.rstrip() + text[end:]

main = java / "NabdhGramSettingsActivity.java"
source = main.read_text(encoding="utf-8")
assert source.count("section(context, content, R.string.") == 7, "preserve all seven native-ordered categories"
section = r'''    private void section(Context context, LinearLayout parent, int titleRes, int descriptionRes) {
        // Language and Appearance share a single category. Preserve the
        // original Appearance invocation for pinned-source order contracts,
        // but never draw a duplicate card.
        if (titleRes == R.string.NabdhAppearanceTitle) return;
        final int accent = org.telegram.ui.Components.NabdhDynamicAccent.accent(context,
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        final int icon = titleRes == R.string.NabdhShieldTitle ? R.drawable.settings_privacy
                : titleRes == R.string.NabdhPrivacyTitle ? R.drawable.settings_devices
                : titleRes == R.string.NabdhProductivityTitle ? R.drawable.settings_folders
                : titleRes == R.string.NabdhLanguageTitle ? R.drawable.settings_language
                : titleRes == R.string.NabdhNetworkTitle ? R.drawable.settings_data
                : titleRes == R.string.NabdhIntelligenceTitle ? R.drawable.settings_features
                : R.drawable.settings_chat;
        int summaryRes = R.string.NabdhCompactAppearance;
        if (titleRes == R.string.NabdhShieldTitle) summaryRes = R.string.NabdhCompactShield;
        else if (titleRes == R.string.NabdhPrivacyTitle) summaryRes = R.string.NabdhCompactPrivacy;
        else if (titleRes == R.string.NabdhProductivityTitle) summaryRes = R.string.NabdhCompactProductivity;
        else if (titleRes == R.string.NabdhLanguageTitle) summaryRes = R.string.NabdhCompactStyleLanguage;
        else if (titleRes == R.string.NabdhNetworkTitle) summaryRes = R.string.NabdhCompactNetwork;
        else if (titleRes == R.string.NabdhIntelligenceTitle) summaryRes = R.string.NabdhCompactIntelligence;
        org.telegram.ui.Components.NabdhCompactSettings.row(context, parent,
                titleRes == R.string.NabdhLanguageTitle
                        ? NabdhStrings.get(context, R.string.NabdhCompactStyleLanguageTitle)
                        : NabdhStrings.get(context, titleRes),
                NabdhStrings.get(context, summaryRes), icon, accent,
                () -> presentFragment(new NabdhGramFeatureCategoryActivity(
                        titleRes, descriptionRes)));
    }'''
source = replace_method(
    source,
    "    private void section(Context context, LinearLayout parent, int titleRes, int descriptionRes)",
    section, "root six grouped categories")
main.write_text(source, encoding="utf-8")

page = java / "NabdhGramFeatureCategoryActivity.java"
source = page.read_text(encoding="utf-8")
row = r'''    private void nabdhFeatureRow(Context context, LinearLayout content, int id) {
        // Group sibling feature destinations with one subtle shared surface.
        // Keep the original destination ID and route unchanged.
        String title = NabdhStrings.get(context, nabdhDetailTitle(id));
        String note = id == 402
                ? NabdhStrings.get(context, R.string.NabdhHStatusPartial) : null;
        org.telegram.ui.Components.NabdhCompactSettings.row(
                context, content, title, note, 0,
                () -> presentFragment(new NabdhGramFeatureCategoryActivity(
                        titleRes, descriptionRes, id)));
    }'''
source = replace_method(source,
    "    private void nabdhFeatureRow(Context context, LinearLayout content, int id)",
    row, "category grouped features")

actions = r'''    private void nabdhV1Button(Context context, LinearLayout content,
                              int title, Runnable action) {
        org.telegram.ui.Components.NabdhCompactSettings.row(
                context, content, NabdhStrings.get(context, title), null, 0, action);
    }'''
source = replace_method(source,
    "    private void nabdhV1Button(Context context, LinearLayout content,",
    actions, "compact detail action rows")

tools = r'''    private void nabdhExpandedButton(Context context, LinearLayout parent,
                                     int label, Runnable action) {
        int subtitle;
        int icon;
        if (label == R.string.NabdhExpandedBrowser) {
            subtitle = R.string.NabdhExpandedBrowserInfo;
            icon = R.drawable.nabdh_tool_browser;
        } else if (label == R.string.NabdhExpandedCamera) {
            subtitle = R.string.NabdhExpandedCameraInfo;
            icon = R.drawable.nabdh_tool_camera;
        } else if (label == R.string.NabdhExpandedChannelFeed) {
            subtitle = R.string.NabdhExpandedChannelFeedInfo;
            icon = R.drawable.nabdh_tool_feed;
        } else if (label == R.string.NabdhChatLockTitle) {
            subtitle = R.string.NabdhExpandedLockInfo;
            icon = R.drawable.nabdh_tool_lock;
        } else {
            subtitle = R.string.NabdhExpandedSwipesInfo;
            icon = R.drawable.nabdh_tool_swipe;
        }
        org.telegram.ui.Components.NabdhCompactSettings.row(
                context, parent, NabdhStrings.get(context, label),
                NabdhStrings.get(context, subtitle), icon, action);
    }'''
source = replace_method(source,
    "    private void nabdhExpandedButton(Context context, LinearLayout parent,",
    tools, "extra grouped destinations")

source = replace_once(source,
    "heading.setText(org.telegram.messenger.LocaleController.getString(R.string.NabdhExpandedTitle));",
    "heading.setText(NabdhStrings.get(context, R.string.NabdhExpandedTitle));",
    "invalid LOC_ERR extra-tools header")
source = replace_once(source,
    "        content.addView(explanation);",
    """        // Native-style guidance: quiet secondary copy outside the grouped list.
        // Detail pages retain the complete explanation and actual controls.
        explanation.setBackground(null);
        explanation.setTextSize(12);
        explanation.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        explanation.setPadding(nabdhDp(context, 8), nabdhDp(context, 6),
                nabdhDp(context, 8), nabdhDp(context, 12));
        if (featureId == 0) {
            explanation.setMaxLines(2);
            explanation.setEllipsize(android.text.TextUtils.TruncateAt.END);
        }
        content.addView(explanation);""", "compact category summary")
# Previously the Fonts detail displayed eight radios above both sliders,
# extending far past one viewport. The selected font remains identical, but
# the choice list is an explicit, collapsible native selector.
source = replace_once(source, "            fontCard.addView(choices);", """            choices.setVisibility(View.GONE);
            fontTitle.setText(NabdhStrings.get(context, R.string.NabdhFontTitle) +
                    "  ·  " + NabdhStrings.get(context,
                    names[Math.max(0, initialFontIndex)]));
            fontTitle.setTextSize(15);
            fontTitle.setPadding(nabdhDp(context, 8), nabdhDp(context, 12),
                    nabdhDp(context, 8), nabdhDp(context, 12));
            fontTitle.setClickable(true);
            fontTitle.setFocusable(true);
            fontTitle.setOnClickListener(v -> choices.setVisibility(
                    choices.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE));
            choices.setOnCheckedChangeListener((group, checkedId) -> {
                for (int i = 0; i < group.getChildCount(); i++) {
                    View child = group.getChildAt(i);
                    if (child.getId() == checkedId && child instanceof android.widget.RadioButton) {
                        fontTitle.setText(NabdhStrings.get(context, R.string.NabdhFontTitle)
                                + "  ·  " + ((android.widget.RadioButton) child).getText());
                        choices.setVisibility(View.GONE);
                        break;
                    }
                }
            });
            fontCard.addView(choices);""", "collapsible font choice without replacing its existing saved onClick behavior")
for invariant in ("NabdhShieldTitle", "NabdhHSettingsBackup",
                  "private void addNabdhFeatureMenu(", "private void addPrivacyControls("):
    if invariant not in source:
        raise SystemExit("Compact settings accidentally removed category logic: " + invariant)
# Language and Appearance become ONE visible category, with original
# feature IDs and detail routes unchanged. Swipe Actions already exists in
# Telegram Chats settings; remove our redundant custom navigation row.
source = replace_once(source,
    "            nabdhFeatureRow(context, content, 402);",
    """            nabdhFeatureRow(context, content, 402);
            nabdhFeatureRow(context, content, 601);
            nabdhFeatureRow(context, content, 602);
            nabdhFeatureRow(context, content, 603);""",
    "merged Language/Appearance nested destinations")
source = replace_once(source,
    """            nabdhExpandedButton(context, content, R.string.NabdhExpandedSwipes,
                    () -> nabdhChooseChatSwipe(context));""",
    "            // Swipe preferences remain in Telegram's native Chats settings.",
    "remove duplicate Swipe Actions control")
source = replace_once(source,
    "actionBar.setTitle(NabdhStrings.get(context, featureId == 0 ? titleRes : nabdhDetailTitle(featureId)));",
    """actionBar.setTitle(NabdhStrings.get(context,
                featureId == 0 && titleRes == R.string.NabdhLanguageTitle
                        ? R.string.NabdhCompactStyleLanguageTitle
                        : (featureId == 0 ? titleRes : nabdhDetailTitle(featureId))));""",
    "combined category toolbar title")
# Harmonize the boolean controls with Telegram's own checked/unchecked switch
# colors, keeping their existing preference callbacks untouched.
for widget in ("toggle", "remember", "monet", "boldOption"):
    creation = "android.widget.Switch " + widget + " = new android.widget.Switch(context);"
    if source.count(creation) == 1:
        source = source.replace(creation, creation +
            "\\n        org.telegram.ui.Components.NabdhToolUi.styleToggle(context, " +
            widget + ");", 1)
    elif source.count(creation) > 1:
        raise SystemExit("Multiple generated Switch declarations: " + widget)
# Inputs on every category detail share the same adaptive, non-underlined
# component as the custom PIN and on-device AI screens.
for field in ("input",):
    creation = "android.widget.EditText " + field + " = new android.widget.EditText(context);"
    if source.count(creation) == 1:
        source = source.replace(creation, creation +
            "\\n        org.telegram.ui.Components.NabdhToolUi.styleInput(context, " +
            field + ");", 1)

page.write_text(source, encoding="utf-8")

from xml.sax.saxutils import escape
translations = {
    "values": {
        "Shield": "Link warnings and manually checked files",
        "Privacy": "Private chats, previews and gestures",
        "Productivity": "Channel feed, notes and focus",
        "Language": "Translation and voice playback",
        "Network": "Browser, camera, data and storage",
        "Appearance": "Fonts, themes and settings backup",
        "StyleLanguageTitle": "Appearance and language",
        "StyleLanguage": "Fonts, themes, translation and voice",
        "Intelligence": "Optional private on-device AI tools",
    },
    "values-ar": {
        "Shield": "الروابط المشبوهة وفحص الملفات الاختياري",
        "Privacy": "قفل المحادثات والمعاينات وإجراءات السحب",
        "Productivity": "موجز القنوات والملاحظات والتركيز",
        "Language": "الترجمة وتشغيل الرسائل الصوتية",
        "Network": "المتصفح والكاميرا والبيانات والتخزين",
        "Appearance": "الخطوط والثيمات ونسخ الإعدادات",
        "StyleLanguageTitle": "المظهر واللغة",
        "StyleLanguage": "الخطوط والثيمات والترجمة والصوت",
        "Intelligence": "أدوات ذكاء محلي اختيارية وخاصة",
    },
}
for lang, entries in translations.items():
    path = root / "TMessagesProj/src/main/res" / lang / "nabdh_compact_settings.xml"
    if path.exists():
        raise SystemExit("Compact settings translation collision: " + str(path))
    rows = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for key, value in entries.items():
        rows.append(f'    <string name="NabdhCompact{key}">{escape(value)}</string>')
    path.write_text("\n".join(rows + ["</resources>", ""]), encoding="utf-8")

print("PASS: grouped NabdhGram categories, native short rows, safe custom localization")
