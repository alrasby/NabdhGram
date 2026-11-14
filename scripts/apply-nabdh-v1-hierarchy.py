#!/usr/bin/env python3
"""Arrange existing NabdhGram V1 actions as category > feature > detail.

Runs AFTER apply-nabdh-v1-signatures.py. Does not fabricate working controls
for features that are not integrated yet. Preserves generated Glass/font/
Privacy Screen and native Telegram action implementations.
"""
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-v1-hierarchy.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
page = root / "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramFeatureCategoryActivity.java"
s = page.read_text(encoding="utf-8")

def replace(old, new, label):
    global s
    if s.count(old) != 1:
        raise SystemExit(f"V1 hierarchy {label}: expected one anchor, got {s.count(old)}")
    s = s.replace(old, new, 1)

replace("    private final int descriptionRes;",
        """    private final int descriptionRes;
    // 0 = category index; nonzero = feature details.
    private final int featureId;""", "field")
replace("""        this.descriptionRes = descriptionRes;
    }""",
        """        this.descriptionRes = descriptionRes;
        this.featureId = 0;
    }

    public NabdhGramFeatureCategoryActivity(int titleRes, int descriptionRes, int featureId) {
        this.titleRes = titleRes;
        this.descriptionRes = descriptionRes;
        this.featureId = featureId;
    }""", "overloaded constructor")
# Earlier Glass/locale passes may change how the toolbar title is resolved.
# Match only the actual single actionBar title call, without assuming a helper.
toolbar = re.findall(r"actionBar\.setTitle\([^;\n]+\);", s)
if len(toolbar) != 1:
    raise SystemExit(f"V1 hierarchy: expected one native toolbar call, got {len(toolbar)}")
replace(toolbar[0],
        "actionBar.setTitle(nabdhText(context, featureId == 0 ? titleRes : nabdhDetailTitle(featureId)));",
        "detail toolbar")
replace("explanation.setText(nabdhText(context, descriptionRes));",
        "explanation.setText(nabdhText(context, featureId == 0 ? nabdhCategoryDescription() : nabdhDetailDescription(featureId)));",
        "explanation")

# Font controls are already functional; move them behind Appearance > Fonts.
replace("if (titleRes == R.string.NabdhAppearanceTitle) {",
        "if (featureId == 601) {", "font detail routing")

# Existing Privacy Screen control stays exactly as created by Telegram overlay,
# but is no longer mixed with the scheduled-messages help page.
replace("if (titleRes == R.string.NabdhPrivacyTitle) {",
        "if (featureId == 201) {", "privacy detail routing")
schedule = re.search(r"\n\s*TextView scheduleTitle = new TextView\(context\);.*?\n\s*content.addView\(scheduleInfo\);", s, re.S)
if not schedule:
    raise SystemExit("V1 hierarchy: scheduled message help was not found")
original_schedule = schedule.group(0)
s = s.replace(original_schedule,
              "\n        }\n        if (featureId == 202) {" + original_schedule, 1)

replace("""        if (titleRes == R.string.NabdhShieldTitle ||
                titleRes == R.string.NabdhProductivityTitle) {
            addNabdhV1Tools(context, content);
        }
        if (titleRes == R.string.NabdhNetworkTitle) {
            addNabdhNetworkTools(context, content);
        }""",
        """        if (featureId == 0) {
            addNabdhFeatureMenu(context, content);
        } else if (featureId == 101 || featureId == 301 ||
                   featureId == 302 || featureId == 303) {
            addNabdhV1Tools(context, content);
        } else if (featureId == 501 || featureId == 502 || featureId == 503) {
            addNabdhNetworkTools(context, content);
        }""", "category-to-detail routing")

# Local analysis is never automatic. Each feature screen exposes only its own
# controls; Workspace keeps both its save and open actions together.
replace("""titleRes == R.string.NabdhShieldTitle
                ? R.string.NabdhV1ShieldDisclosure""",
        """featureId == 101
                ? R.string.NabdhV1ShieldDisclosure""", "feature disclosure")
replace("""if (titleRes == R.string.NabdhShieldTitle) {
            nabdhV1Button""",
        """if (featureId == 101) {
            nabdhV1Button""", "shield tool")
replace("            nabdhV1Button(context, content, R.string.NabdhV1Focus,",
        "            if (featureId == 301) nabdhV1Button(context, content, R.string.NabdhV1Focus,", "focus")
replace("            nabdhV1Button(context, content, R.string.NabdhV1CatchUp,",
        "            if (featureId == 303) nabdhV1Button(context, content, R.string.NabdhV1CatchUp,", "recap")
replace("            nabdhV1Button(context, content, R.string.NabdhV1Save,",
        "            if (featureId == 302) nabdhV1Button(context, content, R.string.NabdhV1Save,", "save note")
replace("            nabdhV1Button(context, content, R.string.NabdhV1OpenWorkspace,",
        "            if (featureId == 302) nabdhV1Button(context, content, R.string.NabdhV1OpenWorkspace,", "open notes")
for symbol, detail in [("NabdhV1DataSettings", 501), ("NabdhV1CacheSettings", 502), ("NabdhV1ProxySettings", 503)]:
    replace(f"        nabdhV1Button(context, content, R.string.{symbol},",
            f"        if (featureId == {detail}) nabdhV1Button(context, content, R.string.{symbol},",
            symbol)

methods = r'''    private int nabdhCategoryDescription() {
        if (titleRes == R.string.NabdhShieldTitle) return R.string.NabdhHShieldOverview;
        if (titleRes == R.string.NabdhPrivacyTitle) return R.string.NabdhHPrivacyOverview;
        if (titleRes == R.string.NabdhProductivityTitle) return R.string.NabdhHProductivityOverview;
        if (titleRes == R.string.NabdhLanguageTitle) return R.string.NabdhHLanguageOverview;
        if (titleRes == R.string.NabdhNetworkTitle) return R.string.NabdhHNetworkOverview;
        return R.string.NabdhHAppearanceOverview;
    }

    private static int nabdhDetailTitle(int id) {
        switch (id) {
            case 101: return R.string.NabdhHLinks;
            case 102: return R.string.NabdhHFiles;
            case 103: return R.string.NabdhHScam;
            case 201: return R.string.NabdhHPrivacyScreen;
            case 202: return R.string.NabdhHScheduled;
            case 203: return R.string.NabdhHPreview;
            case 301: return R.string.NabdhHFocus;
            case 302: return R.string.NabdhHWorkspace;
            case 303: return R.string.NabdhHCatchUp;
            case 401: return R.string.NabdhHTranslation;
            case 402: return R.string.NabdhHVoice;
            case 501: return R.string.NabdhHData;
            case 502: return R.string.NabdhHStorage;
            case 503: return R.string.NabdhHProxy;
            case 601: return R.string.NabdhHFonts;
            case 602: return R.string.NabdhHThemes;
            default: throw new IllegalArgumentException("Unknown NabdhGram detail " + id);
        }
    }

    private static int nabdhDetailDescription(int id) {
        switch (id) {
            case 101: return R.string.NabdhHLinksDescription;
            case 102: return R.string.NabdhHFilesDescription;
            case 103: return R.string.NabdhHScamDescription;
            case 201: return R.string.NabdhHPrivacyScreenDescription;
            case 202: return R.string.NabdhHScheduledDescription;
            case 203: return R.string.NabdhHPreviewDescription;
            case 301: return R.string.NabdhHFocusDescription;
            case 302: return R.string.NabdhHWorkspaceDescription;
            case 303: return R.string.NabdhHCatchUpDescription;
            case 401: return R.string.NabdhHTranslationDescription;
            case 402: return R.string.NabdhHVoiceDescription;
            case 501: return R.string.NabdhHDataDescription;
            case 502: return R.string.NabdhHStorageDescription;
            case 503: return R.string.NabdhHProxyDescription;
            case 601: return R.string.NabdhHFontsDescription;
            case 602: return R.string.NabdhHThemesDescription;
            default: throw new IllegalArgumentException("Unknown NabdhGram detail " + id);
        }
    }

    private void addNabdhFeatureMenu(Context context, LinearLayout content) {
        if (titleRes == R.string.NabdhShieldTitle) {
            nabdhFeatureRow(context, content, 101);
            nabdhFeatureRow(context, content, 102);
            nabdhFeatureRow(context, content, 103);
        } else if (titleRes == R.string.NabdhPrivacyTitle) {
            nabdhFeatureRow(context, content, 201);
            nabdhFeatureRow(context, content, 203);
            nabdhFeatureRow(context, content, 202);
        } else if (titleRes == R.string.NabdhProductivityTitle) {
            nabdhFeatureRow(context, content, 301);
            nabdhFeatureRow(context, content, 302);
            nabdhFeatureRow(context, content, 303);
        } else if (titleRes == R.string.NabdhLanguageTitle) {
            nabdhFeatureRow(context, content, 401);
            nabdhFeatureRow(context, content, 402);
        } else if (titleRes == R.string.NabdhNetworkTitle) {
            nabdhFeatureRow(context, content, 501);
            nabdhFeatureRow(context, content, 502);
            nabdhFeatureRow(context, content, 503);
        } else if (titleRes == R.string.NabdhAppearanceTitle) {
            nabdhFeatureRow(context, content, 601);
            nabdhFeatureRow(context, content, 602);
        }
    }

    private void nabdhFeatureRow(Context context, LinearLayout content, int id) {
        LinearLayout card = new LinearLayout(context);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(android.view.Gravity.CENTER_VERTICAL);
        card.setLayoutDirection(org.telegram.messenger.LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        int h = nabdhDp(context, 16);
        card.setPadding(h, nabdhDp(context, 12), h, nabdhDp(context, 12));
        card.setMinimumHeight(nabdhDp(context, 68));
        card.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        card.setClipToOutline(true);
        card.setClickable(true);
        card.setFocusable(true);

        LinearLayout labels = new LinearLayout(context);
        labels.setOrientation(LinearLayout.VERTICAL);
        TextView name = new TextView(context);
        name.setText(nabdhText(context, nabdhDetailTitle(id)));
        name.setTextSize(16);
        name.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        labels.addView(name);
        TextView status = new TextView(context);
        status.setText(nabdhText(context, (id == 102 || id == 103 || id == 402)
                ? R.string.NabdhHStatusPending : R.string.NabdhHStatusDetails));
        status.setTextSize(12);
        status.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        labels.addView(status);
        card.addView(labels, new LinearLayout.LayoutParams(0, -2, 1f));
        TextView chevron = new TextView(context);
        chevron.setText(org.telegram.messenger.LocaleController.isRTL ? "‹" : "›");
        chevron.setTextSize(24);
        chevron.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        card.addView(chevron, new LinearLayout.LayoutParams(-2, -2));

        LinearLayout.LayoutParams row = new LinearLayout.LayoutParams(-1, -2);
        row.topMargin = nabdhDp(context, 10);
        content.addView(card, row);
        card.setContentDescription(nabdhText(context, nabdhDetailTitle(id)));
        card.setOnClickListener(v -> presentFragment(
                new NabdhGramFeatureCategoryActivity(titleRes, descriptionRes, id)));
    }

'''
replace("    private void addPrivacyControls(Context context, LinearLayout content) {",
        methods + "    private void addPrivacyControls(Context context, LinearLayout content) {",
        "hierarchy menu")

page.write_text(s, encoding="utf-8")

locales = {
    "values": {
        "NabdhHShieldOverview": "Choose a security feature. Link checks are opt-in; file inspection and scam detection are not yet integrated.",
        "NabdhHPrivacyOverview": "Privacy controls, native chat preview and Telegram scheduled messages.",
        "NabdhHProductivityOverview": "Local, opt-in text tools. Live chat and message-linked workflows remain in development.",
        "NabdhHLanguageOverview": "Translation follows available Telegram features. Voice processing improvements are still in development.",
        "NabdhHNetworkOverview": "Native Telegram data, storage and proxy controls; no artificial network optimizer.",
        "NabdhHAppearanceOverview": "Personalize fonts and use Telegram's existing theme management.",
        "NabdhHStatusPending": "In development — not enabled",
        "NabdhHStatusDetails": "Open feature options",
        "NabdhHLinks": "Safe Link Preview",
        "NabdhHLinksDescription": "Paste a link or text to check local warning signs. A lack of warnings never guarantees safety.",
        "NabdhHFiles": "File Guardian",
        "NabdhHFilesDescription": "Pre-open file scanning is not yet integrated. No file is scanned or certified safe by this page.",
        "NabdhHScam": "Scam warnings",
        "NabdhHScamDescription": "Message-level fraud detection and impersonation warnings are in development. Do not share login or OTP codes.",
        "NabdhHPrivacyScreen": "Privacy Screen",
        "NabdhHPrivacyScreenDescription": "Control Android 13+ recent-app snapshots. Ordinary screenshots are unaffected.",
        "NabdhHScheduled": "Scheduled messages",
        "NabdhHScheduledDescription": "Use Telegram's native long-press Send menu to schedule messages.",
        "NabdhHPreview": "Smart Chat Preview",
        "NabdhHPreviewDescription": "Native Telegram chat preview: long-press a chat. Use the separate Mark as Read action explicitly; final server read-receipt behavior still requires device validation.",
        "NabdhHFocus": "Focus Lens",
        "NabdhHFocusDescription": "Extract tasks, dates, questions and decisions from text you explicitly provide. Links back to original Telegram messages are not yet available.",
        "NabdhHWorkspace": "Message Workspace",
        "NabdhHWorkspaceDescription": "Save and review your own AES-GCM encrypted local notes. Message links, tasks and reminders are in development.",
        "NabdhHCatchUp": "Catch Me Up",
        "NabdhHCatchUpDescription": "Review only pasted excerpts. Unread conversations are not accessed or summarized automatically.",
        "NabdhHTranslation": "Translation",
        "NabdhHTranslationDescription": "Telegram's built-in translation options remain accessible in chats and Telegram Settings. Optional automatic live translation is not implemented here.",
        "NabdhHVoice": "Voice Clarity",
        "NabdhHVoiceDescription": "Advanced playback noise and clarity processing is in development. Native Telegram voice playback remains unchanged.",
        "NabdhHData": "Wi-Fi and mobile downloads",
        "NabdhHDataDescription": "Open Telegram's existing auto-download and mobile-data options. No additional background optimization is claimed.",
        "NabdhHStorage": "Storage and cache",
        "NabdhHStorageDescription": "Review Telegram's native cache, retained media and storage limits.",
        "NabdhHProxy": "Proxy and connection",
        "NabdhHProxyDescription": "Manage Telegram-compatible proxies using the native settings screen.",
        "NabdhHFonts": "Fonts, size and weight",
        "NabdhHFontsDescription": "Choose fonts and tune user-interface and chat text using existing NabdhGram typography controls.",
        "NabdhHThemes": "Glass themes and colors",
        "NabdhHThemesDescription": "Telegram's native theme manager supports built-in and .attheme themes. Use Telegram Appearance settings to change them; no duplicate theme engine is added.",
    },
    "values-ar": {
        "NabdhHShieldOverview": "اختر ميزة الحماية. فحص الروابط يدوي واختياري؛ فحص الملفات والاحتيال التلقائي لم يُدمجا بعد.",
        "NabdhHPrivacyOverview": "إعدادات الخصوصية ومعاينة المحادثات الأصلية والرسائل المجدولة في Telegram.",
        "NabdhHProductivityOverview": "أدوات نصية محلية باختيارك. ربط الرسائل والتلخيص المباشر للمحادثات ما زالا قيد التطوير.",
        "NabdhHLanguageOverview": "الترجمة المتاحة من Telegram، وتحسينات معالجة الصوت ما زالت قيد التطوير.",
        "NabdhHNetworkOverview": "خيارات Telegram الأصلية للتنزيل والتخزين والبروكسي، دون محرك تحسين اتصال وهمي.",
        "NabdhHAppearanceOverview": "تخصيص الخطوط مع إدارة الثيمات الأصلية في Telegram.",
        "NabdhHStatusPending": "قيد التطوير — غير مفعّل",
        "NabdhHStatusDetails": "فتح خيارات الميزة",
        "NabdhHLinks": "معاينة الروابط الآمنة",
        "NabdhHLinksDescription": "ألصق رابطًا أو نصًا لفحص مؤشرات خطورة محلية؛ عدم وجود تحذير لا يعني أن الرابط آمن.",
        "NabdhHFiles": "حارس الملفات",
        "NabdhHFilesDescription": "لم يُدمج فحص الملفات قبل فتحها بعد. لا تفحص هذه الصفحة الملفات ولا تصنفها آمنة.",
        "NabdhHScam": "تحذيرات الاحتيال",
        "NabdhHScamDescription": "كشف الاحتيال وانتحال الدعم داخل الرسائل قيد التطوير. لا تشارك رموز الدخول أو التحقق.",
        "NabdhHPrivacyScreen": "شاشة الخصوصية",
        "NabdhHPrivacyScreenDescription": "التحكم في معاينات التطبيقات الأخيرة على Android 13 والأحدث دون تعطيل لقطات الشاشة العادية.",
        "NabdhHScheduled": "الرسائل المجدولة",
        "NabdhHScheduledDescription": "استخدم الضغط المطوّل على زر الإرسال لجدولة الرسائل من Telegram الأصلي.",
        "NabdhHPreview": "المعاينة الذكية للمحادثات",
        "NabdhHPreviewDescription": "معاينة Telegram الأصلية: اضغط مطولًا على المحادثة. خيار اعتبارها مقروءة مستقل، ولا تزال إيصالات القراءة بحاجة لاختبار نهائي على الجهاز.",
        "NabdhHFocus": "عدسة التركيز",
        "NabdhHFocusDescription": "استخراج المهام والتواريخ والأسئلة والقرارات من نص تدخله بنفسك. الروابط للرسائل الأصلية لم تُنفّذ بعد.",
        "NabdhHWorkspace": "مساحة عمل الرسائل",
        "NabdhHWorkspaceDescription": "حفظ ملاحظاتك المحلية المشفرة بخوارزمية AES-GCM. ربط الرسائل والمهام والتذكيرات قيد التطوير.",
        "NabdhHCatchUp": "ملخص ما فاتك",
        "NabdhHCatchUpDescription": "مراجعة المقاطع الملصقة فقط؛ لا تُقرأ المحادثات غير المقروءة أو تُلخّص تلقائيًا.",
        "NabdhHTranslation": "الترجمة",
        "NabdhHTranslationDescription": "خيارات ترجمة Telegram الأصلية متاحة من المحادثات والإعدادات. الترجمة المباشرة الإضافية غير مدمجة هنا.",
        "NabdhHVoice": "وضوح الصوت",
        "NabdhHVoiceDescription": "معالجة الضوضاء ووضوح التشغيل المتقدمة قيد التطوير. تشغيل صوت Telegram الأصلي لم يتغير.",
        "NabdhHData": "تنزيلات الواي فاي والبيانات",
        "NabdhHDataDescription": "تفتح خيارات التنزيل التلقائي وبيانات الهاتف الأصلية في Telegram دون ادعاء تحسين خلفي إضافي.",
        "NabdhHStorage": "التخزين والذاكرة المؤقتة",
        "NabdhHStorageDescription": "مراجعة خيارات Telegram الأصلية للتخزين وإدارة الوسائط والذاكرة المؤقتة.",
        "NabdhHProxy": "البروكسي والاتصال",
        "NabdhHProxyDescription": "إدارة بروكسي Telegram من إعداداته الأصلية.",
        "NabdhHFonts": "الخطوط والحجم والوزن",
        "NabdhHFontsDescription": "اختيار الخطوط وتعديل حجم نصوص التطبيق والمحادثات عبر خيارات نبض جرام القائمة.",
        "NabdhHThemes": "ثيمات Glass والألوان",
        "NabdhHThemesDescription": "مدير ثيمات Telegram الأصلي يدعم الثيمات المدمجة وملفات .attheme. غيّرها من إعدادات المظهر، دون إنشاء محرك مكرر.",
    }
}

for locale, translations in locales.items():
    dest = root / "TMessagesProj/src/main/res" / locale / "nabdh_v1_hierarchy.xml"
    if dest.exists():
        raise SystemExit("V1 hierarchy resource already exists: " + str(dest))
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for key, value in translations.items():
        lines.append('    <string name="' + key + '">' +
                     escape(value).replace("'", "\\'") + '</string>')
    lines.append("</resources>")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("PASS: hierarchical NabdhGram settings, preserved Glass/privacy/fonts/opt-in V1 tools")
