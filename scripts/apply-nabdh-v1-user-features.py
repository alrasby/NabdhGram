#!/usr/bin/env python3
"""One late, guarded integration pass for consent, Monet UI accents and safe backups.

No changes to Telegram message, login, call or network paths. Unavailable
model providers are honestly identified as unavailable, never fake AI.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-v1-user-features.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
templates = Path(__file__).resolve().parent.parent / "overlay/java"
for filename in ("NabdhAiPreferenceStore.java", "NabdhDynamicAccent.java",
                 "NabdhSettingsBackup.java"):
    target = ui / "Components" / filename
    if target.exists(): raise SystemExit("Already generated: " + filename)
    target.write_text((templates / filename).read_text(encoding="utf-8"),
                      encoding="utf-8")

def patch_one(text, old, new, label):
    n = text.count(old)
    if n != 1: raise SystemExit(f"V1 user features {label}: expected one anchor, got {n}")
    return text.replace(old, new, 1)

hub = ui / "NabdhGramSettingsActivity.java"
h = hub.read_text(encoding="utf-8")
# Theme colors are retained as fallbacks and only category accents change.
h = patch_one(h, "heading.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));",
    "heading.setTextColor(org.telegram.ui.Components.NabdhDynamicAccent.accent(context, Theme.getColor(Theme.key_windowBackgroundWhiteBlueText)));",
    "hub title")
h = patch_one(h, "categoryIcon.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));",
    "categoryIcon.setColorFilter(org.telegram.ui.Components.NabdhDynamicAccent.accent(context, Theme.getColor(Theme.key_windowBackgroundWhiteBlueText)));",
    "hub icon")
hub.write_text(h, encoding="utf-8")

page = ui / "NabdhGramFeatureCategoryActivity.java"
s = page.read_text(encoding="utf-8")
s = patch_one(s,
    "            case 602: return R.string.NabdhHThemes;",
    """            case 602: return R.string.NabdhHThemes;
            case 603: return R.string.NabdhHSettingsBackup;""", "backup title")
s = patch_one(s,
    "            case 602: return R.string.NabdhHThemesDescription;",
    """            case 602: return R.string.NabdhHThemesDescription;
            case 603: return R.string.NabdhHSettingsBackupDescription;""", "backup detail")
s = patch_one(s,
    """            nabdhFeatureRow(context, content, 602);""",
    """            nabdhFeatureRow(context, content, 602);
            nabdhFeatureRow(context, content, 603);""", "backup menu")
s = patch_one(s,
    "chevron.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));",
    "chevron.setTextColor(org.telegram.ui.Components.NabdhDynamicAccent.accent(context, Theme.getColor(Theme.key_windowBackgroundWhiteBlueText)));",
    "feature accent")

s = patch_one(s,
    """if (featureId == 602) {
            addNabdhGlassPresets(context, content);
        }""",
    """if (featureId == 602) {
            addNabdhGlassPresets(context, content);
            addNabdhMonetControl(context, content);
        }""", "Monet behind Glass Themes only")
s = patch_one(s,
    """        fragmentView = scroll;""",
    """        if (featureId == 603) {
            addNabdhBackupActions(context, content);
        }
        if (featureId == 0 && titleRes == R.string.NabdhIntelligenceTitle) {
            addNabdhPrivacyControls(context, content);
        }
        fragmentView = scroll;""", "separate backup/AI pages")

s = patch_one(s,
    """        super.onActivityResultFragment(requestCode, resultCode, data);""",
    """        super.onActivityResultFragment(requestCode, resultCode, data);
        if (featureId == 603 && (requestCode == 6603 || requestCode == 6604)) {
            if (resultCode == android.app.Activity.RESULT_OK && data != null
                    && data.getData() != null && getParentActivity() != null) {
                nabdhHandleBackupResult(requestCode, data.getData());
            }
            return;
        }""", "explicit SAF result route")
s = patch_one(s,
    """boolean arabic = org.telegram.messenger.LocaleController.isRTL;""",
    """boolean arabic = org.telegram.ui.Components.NabdhAiPreferenceStore.outputArabic(
                context, org.telegram.messenger.LocaleController.isRTL);""",
    "explicit output-language preference")
# Existing opt-in Lens source is preserved, not rebranded as an actual LLM.
methods = r'''    private void addNabdhPrivacyControls(Context context, LinearLayout content) {
        android.widget.LinearLayout card = new android.widget.LinearLayout(context);
        card.setOrientation(LinearLayout.VERTICAL);
        int pad = nabdhDp(context, 16);
        card.setPadding(pad, pad, pad, pad);
        card.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = nabdhDp(context, 12);
        content.addView(card, params);
        TextView info = new TextView(context);
        info.setText(nabdhText(context, R.string.NabdhAiPrivacyDisclosure));
        info.setTextSize(13);
        info.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        card.addView(info);
        android.widget.Switch remember = new android.widget.Switch(context);
        remember.setText(nabdhText(context, R.string.NabdhAiRemember));
        remember.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        remember.setChecked(org.telegram.ui.Components.NabdhAiPreferenceStore.rememberEnabled(context));
        remember.setOnCheckedChangeListener((view, value) ->
            org.telegram.ui.Components.NabdhAiPreferenceStore.setRememberEnabled(context, value));
        card.addView(remember);
        TextView languageLabel = new TextView(context);
        languageLabel.setText(nabdhText(context, R.string.NabdhAiOutputLanguage));
        languageLabel.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        languageLabel.setTextSize(15);
        card.addView(languageLabel);
        android.widget.RadioGroup languages = new android.widget.RadioGroup(context);
        final String[] codes = {"auto", "ar", "en"};
        final int[] names = {R.string.NabdhAiLanguageAuto, R.string.NabdhAiLanguageArabic,
                             R.string.NabdhAiLanguageEnglish};
        String chosen = org.telegram.ui.Components.NabdhAiPreferenceStore.outputLanguage(context);
        for (int index = 0; index < codes.length; index++) {
            final String language = codes[index];
            android.widget.RadioButton option = new android.widget.RadioButton(context);
            option.setId(View.generateViewId());
            option.setText(nabdhText(context, names[index]));
            option.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            option.setChecked(chosen.equals(language));
            option.setOnClickListener(v ->
                org.telegram.ui.Components.NabdhAiPreferenceStore.setOutputLanguage(context, language));
            languages.addView(option);
        }
        card.addView(languages);
        nabdhV1Button(context, content, R.string.NabdhAiClear, () -> {
            org.telegram.ui.Components.NabdhAiPreferenceStore.clear(context);
            remember.setChecked(false);
            android.widget.RadioButton first = (android.widget.RadioButton) languages.getChildAt(0);
            first.setChecked(true);
        });
    }

    private void addNabdhMonetControl(Context context, LinearLayout content) {
        if (android.os.Build.VERSION.SDK_INT < 31 ||
            !org.telegram.ui.Components.NabdhDynamicAccent.available(context)) {
            TextView unavailable = new TextView(context);
            unavailable.setText(nabdhText(context, R.string.NabdhMonetUnsupported));
            unavailable.setTextSize(13);
            unavailable.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
            content.addView(unavailable);
            return;
        }
        android.widget.Switch monet = new android.widget.Switch(context);
        monet.setText(nabdhText(context, R.string.NabdhMonetLabel));
        monet.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        monet.setPadding(nabdhDp(context, 16), nabdhDp(context, 14),
                nabdhDp(context, 16), nabdhDp(context, 14));
        monet.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        monet.setChecked(org.telegram.ui.Components.NabdhDynamicAccent.enabled(context));
        monet.setOnCheckedChangeListener((button, checked) ->
            org.telegram.ui.Components.NabdhDynamicAccent.setEnabled(context, checked));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.topMargin = nabdhDp(context, 10);
        content.addView(monet, p);
        TextView note = new TextView(context);
        note.setText(nabdhText(context, R.string.NabdhMonetScope));
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        note.setTextSize(13);
        content.addView(note);
    }

    private void addNabdhBackupActions(Context context, LinearLayout content) {
        TextView note = new TextView(context);
        note.setText(nabdhText(context, R.string.NabdhBackupScope));
        note.setTextSize(13);
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        content.addView(note);
        nabdhV1Button(context, content, R.string.NabdhBackupExport, () ->
                startActivityForResult(
                    org.telegram.ui.Components.NabdhSettingsBackup.exportIntent(), 6603));
        nabdhV1Button(context, content, R.string.NabdhBackupImport, () ->
                startActivityForResult(
                    org.telegram.ui.Components.NabdhSettingsBackup.importIntent(), 6604));
    }

    private void nabdhHandleBackupResult(int requestCode, android.net.Uri uri) {
        Context context = getParentActivity();
        if (context == null) return;
        try {
            if (requestCode == 6603) {
                org.telegram.ui.Components.NabdhSettingsBackup.write(context, uri);
                android.widget.Toast.makeText(context,
                    nabdhText(context, R.string.NabdhBackupDone),
                    android.widget.Toast.LENGTH_LONG).show();
                return;
            }
            String raw = org.telegram.ui.Components.NabdhSettingsBackup.read(context, uri);
            String summary = org.telegram.ui.Components.NabdhSettingsBackup.preview(
                    raw, org.telegram.messenger.LocaleController.isRTL);
            new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                .setTitle(nabdhText(context, R.string.NabdhBackupImport))
                .setMessage(summary)
                .setNegativeButton(nabdhText(context, R.string.NabdhV1Close), null)
                .setPositiveButton(nabdhText(context, R.string.NabdhBackupConfirm), (dialog, which) -> {
                    try {
                        org.telegram.ui.Components.NabdhSettingsBackup.restore(context, raw);
                        android.widget.Toast.makeText(context,
                            nabdhText(context, R.string.NabdhBackupDone),
                            android.widget.Toast.LENGTH_LONG).show();
                    } catch (Exception problem) {
                        android.widget.Toast.makeText(context,
                            nabdhText(context, R.string.NabdhBackupError),
                            android.widget.Toast.LENGTH_LONG).show();
                    }
                }).show();
        } catch (Exception invalid) {
            android.widget.Toast.makeText(context,
                nabdhText(context, R.string.NabdhBackupError),
                android.widget.Toast.LENGTH_LONG).show();
        }
    }

'''
s = patch_one(s,
    "    private void addPrivacyControls(Context context, LinearLayout content) {",
    methods + "    private void addPrivacyControls(Context context, LinearLayout content) {",
    "user privacy, Monet and backups")
page.write_text(s, encoding="utf-8")
strings = {
    "values": {
        "NabdhHSettingsBackup": "Settings backup",
        "NabdhHSettingsBackupDescription": "Export and restore selected NabdhGram appearance, Glass and voice settings only. No chats, sessions, keys, or AI permissions.",
        "NabdhAiPrivacyDisclosure": "Local AI models are not yet connected. No chat monitoring, passive learning, secret recording or automatic message reading. Only the explicit settings you choose below are saved.",
        "NabdhAiRemember": "Remember feedback I explicitly give (off by default)",
        "NabdhAiOutputLanguage": "Report language for manual Focus and Catch Me Up",
        "NabdhAiLanguageAuto": "Follow interface language",
        "NabdhAiLanguageArabic": "Arabic",
        "NabdhAiLanguageEnglish": "English",
        "NabdhAiClear": "Clear AI preferences and feedback",
        "NabdhMonetLabel": "Use Android wallpaper accent for NabdhGram Settings",
        "NabdhMonetUnsupported": "Android wallpaper color accents are available on Android 12+ only.",
        "NabdhMonetScope": "Optional accent for NabdhGram settings headings/icons; your Telegram themes and Glass presets are unchanged. Reopen settings to refresh accents.",
        "NabdhBackupScope": "Exports only font, text scale, Glass preset, voice boost, and explicitly chosen report language. Never exports Telegram chats, sessions, keys, login data, or AI consent.",
        "NabdhBackupExport": "Export selected settings",
        "NabdhBackupImport": "Import settings from JSON",
        "NabdhBackupConfirm": "Restore these settings",
        "NabdhBackupDone": "Settings saved. Reopen settings to refresh their appearance.",
        "NabdhBackupError": "Invalid or inaccessible settings backup; no private data was imported."
    },
    "values-ar": {
        "NabdhHSettingsBackup": "نسخ إعدادات نبض جرام",
        "NabdhHSettingsBackupDescription": "تصدير واستعادة إعدادات نبض جرام المختارة للخطوط وGlass والصوت فقط، دون محادثات أو جلسات أو مفاتيح أو أذونات AI.",
        "NabdhAiPrivacyDisclosure": "لم يُوصَّل نموذج لغوي محلي بعد. لا مراقبة للمحادثات ولا تعلم خفي ولا تسجيل ولا قراءة تلقائية للرسائل. تُحفظ التفضيلات التي تختارها أنت فقط.",
        "NabdhAiRemember": "تذكر التقييمات التي أقدمها بنفسي (متوقف افتراضيًا)",
        "NabdhAiOutputLanguage": "لغة نتائج عدسة التركيز وملخص المقاطع اليدوي",
        "NabdhAiLanguageAuto": "مثل لغة الواجهة",
        "NabdhAiLanguageArabic": "العربية",
        "NabdhAiLanguageEnglish": "الإنجليزية",
        "NabdhAiClear": "مسح تفضيلات وتقييمات الذكاء",
        "NabdhMonetLabel": "استخدام ألوان خلفية Android في إعدادات نبض جرام",
        "NabdhMonetUnsupported": "ألوان النظام التفاعلية متاحة في Android 12 والأحدث فقط.",
        "NabdhMonetScope": "يغير لون عناوين وأيقونات إعدادات نبض جرام فقط؛ ثيمات Telegram وGlass لا تتأثر. أعد فتح الإعدادات لإظهار الألوان الجديدة.",
        "NabdhBackupScope": "يُصدَّر الخط وحجمه وثيم Glass وتعزيز الصوت ولغة النتائج المختارة فقط. لا تُصدَّر رسائل Telegram أو الجلسات أو مفاتيح الدخول أو موافقة الذكاء.",
        "NabdhBackupExport": "تصدير الإعدادات المختارة",
        "NabdhBackupImport": "استيراد الإعدادات من JSON",
        "NabdhBackupConfirm": "استعادة هذه الإعدادات",
        "NabdhBackupDone": "حُفظت الإعدادات. أعد فتح الصفحة لتحديث المظهر.",
        "NabdhBackupError": "ملف إعدادات غير صالح أو غير قابل للقراءة؛ لم تُستورد أي بيانات خاصة."
    }
}
for locale, entries in strings.items():
    dest = root / "TMessagesProj/src/main/res" / locale / "nabdh_v1_user_features.xml"
    if dest.exists(): raise SystemExit("Duplicate user features resources: " + locale)
    rows = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for name, value in entries.items():
        rows.append('    <string name="' + name + '">' + escape(value).replace("'", "\\'") + '</string>')
    rows.append('</resources>')
    dest.write_text("\n".join(rows) + "\n", encoding="utf-8")
print("PASS: explicit AI privacy, opt-in settings accent, bounded SAF settings backup")
