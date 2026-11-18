#!/usr/bin/env python3
"""Install approved V1 local productivity and safety tools on pinned Telegram.

Scope intentionally honest: explicit text excerpts only, opt-in local
encrypted draft notes. No auto-reading chat histories, no malware scanner,
no fake voice model, no Telegram protocol or delivery changes.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-v1-signatures.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
source_templates = Path(__file__).resolve().parent.parent / "overlay/java"

for name in ("NabdhV1Engine.java", "NabdhWorkspace.java", "NabdhFileGuard.java"):
    target = ui / "Components" / name
    if target.exists():
        raise SystemExit("Existing native component: " + name)
    target.write_text((source_templates / name).read_text(encoding="utf-8"), encoding="utf-8")

category = ui / "NabdhGramFeatureCategoryActivity.java"
s = category.read_text(encoding="utf-8")

def patch(old, new, name):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(name + f": expected 1 anchor, found {n}")
    s = s.replace(old, new, 1)

patch("        fragmentView = scroll;",
      """        if (titleRes == R.string.NabdhShieldTitle ||
                titleRes == R.string.NabdhProductivityTitle) {
            addNabdhV1Tools(context, content);
        }
        if (titleRes == R.string.NabdhNetworkTitle) {
            addNabdhNetworkTools(context, content);
        }
        fragmentView = scroll;""",
      "V1 category route")
methods = """    private void nabdhV1Button(Context context, LinearLayout content,
                              int title, Runnable action) {
        TextView row = new TextView(context);
        row.setText(nabdhText(context, title));
        row.setGravity(android.view.Gravity.CENTER_VERTICAL);
        row.setTextSize(15);
        row.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        row.setPadding(nabdhDp(context, 24), nabdhDp(context, 17),
                       nabdhDp(context, 24), nabdhDp(context, 17));
        row.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.topMargin = nabdhDp(context, 8);
        content.addView(row, p);
        row.setFocusable(true);
        row.setClickable(true);
        row.setOnClickListener(v -> action.run());
    }

    private void nabdhV1Result(Context context, CharSequence source, int title, int mode) {
        String value = org.telegram.ui.Components.NabdhV1Engine.bounded(source);
        if (value.isEmpty()) {
            android.widget.Toast.makeText(context,
                nabdhText(context, R.string.NabdhV1Empty), android.widget.Toast.LENGTH_SHORT).show();
            return;
        }
        boolean arabic = org.telegram.messenger.LocaleController.isRTL;
        String output = mode == 0 ? org.telegram.ui.Components.NabdhV1Engine.focus(value, arabic)
                : mode == 1 ? org.telegram.ui.Components.NabdhV1Engine.catchUp(value, arabic)
                : mode == 3 ? org.telegram.ui.Components.NabdhV1Engine.scam(value, arabic)
                : org.telegram.ui.Components.NabdhV1Engine.shield(value, arabic);
        new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
            .setTitle(nabdhText(context, title))
            .setMessage(output)
            .setNegativeButton(nabdhText(context, R.string.NabdhV1Close), null)
            .setPositiveButton(nabdhText(context, R.string.NabdhV1Copy), (d, which) -> {
                android.content.ClipboardManager clipboard =
                    (android.content.ClipboardManager) context.getSystemService(
                        Context.CLIPBOARD_SERVICE);
                if (clipboard != null) {
                    clipboard.setPrimaryClip(android.content.ClipData.newPlainText(
                            "Nabdh local result", output));
                }
            }).show();
    }

    private void addNabdhNetworkTools(Context context, LinearLayout content) {
        // Real native Telegram data/auto-download and storage screens. No
        // fake "AI optimizer" toggle or modification to transfer limits.
        TextView disclosure = new TextView(context);
        disclosure.setText(nabdhText(context, R.string.NabdhV1NetworkDisclosure));
        disclosure.setTextSize(13);
        disclosure.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        content.addView(disclosure);
        nabdhV1Button(context, content, R.string.NabdhV1DataSettings,
            () -> presentFragment(new DataSettingsActivity()));
        nabdhV1Button(context, content, R.string.NabdhV1CacheSettings,
            () -> presentFragment(new CacheControlActivity()));
        nabdhV1Button(context, content, R.string.NabdhV1ProxySettings,
            () -> presentFragment(new ProxyListActivity()));
    }

    private void addNabdhV1Tools(Context context, LinearLayout content) {
        TextView note = new TextView(context);
        note.setText(nabdhText(context,
            titleRes == R.string.NabdhShieldTitle
                ? R.string.NabdhV1ShieldDisclosure : R.string.NabdhV1ManualDisclosure));
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        note.setTextSize(13);
        content.addView(note);

        final android.widget.EditText input = new android.widget.EditText(context);
        input.setTextSize(15);
        input.setMinLines(2);
        input.setMaxLines(7);
        input.setTextDirection(android.view.View.TEXT_DIRECTION_FIRST_STRONG);
        input.setGravity((org.telegram.messenger.LocaleController.isRTL
            ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT) | android.view.Gravity.TOP);
        input.setHint(nabdhText(context, R.string.NabdhV1InputHint));
        input.setInputType(android.text.InputType.TYPE_CLASS_TEXT |
                           android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.topMargin = nabdhDp(context, 12);
        content.addView(input, p);
        if (titleRes == R.string.NabdhShieldTitle) {
            nabdhV1Button(context, content, R.string.NabdhV1Shield, () ->
                nabdhV1Result(context, input.getText(), R.string.NabdhV1Shield, 2));
        } else {
            nabdhV1Button(context, content, R.string.NabdhV1Scam, () ->
                nabdhV1Result(context, input.getText(), R.string.NabdhV1Scam, 3));
            nabdhV1Button(context, content, R.string.NabdhV1Focus, () ->
                nabdhV1Result(context, input.getText(), R.string.NabdhV1Focus, 0));
            nabdhV1Button(context, content, R.string.NabdhV1CatchUp, () ->
                nabdhV1Result(context, input.getText(), R.string.NabdhV1CatchUp, 1));
            nabdhV1Button(context, content, R.string.NabdhV1Save, () -> {
                if (input.getText().length() == 0) {
                    android.widget.Toast.makeText(context,
                        nabdhText(context, R.string.NabdhV1Empty),
                        android.widget.Toast.LENGTH_SHORT).show();
                } else {
                    org.telegram.ui.Components.NabdhWorkspace.saveWithFeedback(
                        context, input.getText(), org.telegram.messenger.LocaleController.isRTL);
                }
            });
            nabdhV1Button(context, content, R.string.NabdhV1OpenWorkspace, () ->
                org.telegram.ui.Components.NabdhWorkspace.show(
                    context, org.telegram.messenger.LocaleController.isRTL));
        }
    }

"""
patch("    private void addPrivacyControls(Context context, LinearLayout content) {",
      methods + "    private void addPrivacyControls(Context context, LinearLayout content) {",
      "V1 local tool methods")
category.write_text(s, encoding="utf-8")

strings = {
    "values": {
        "NabdhV1InputHint": "Paste text, a link or a conversation excerpt (nothing is read automatically)",
        "NabdhV1Shield": "Check local URL warning signals",
        "NabdhV1Scam": "Check local message scam signals",
        "NabdhV1Focus": "Extract focus signals from pasted text",
        "NabdhV1CatchUp": "Review pasted conversation excerpt",
        "NabdhV1Save": "Save encrypted local note",
        "NabdhV1OpenWorkspace": "Open saved local notes",
        "NabdhV1DataSettings": "Wi-Fi and mobile data / auto-download",
        "NabdhV1CacheSettings": "Storage and cache manager",
        "NabdhV1ProxySettings": "Telegram proxy settings",
        "NabdhV1NetworkDisclosure": "Open the official Telegram data, storage and proxy controls. No hidden connection optimizer or Premium bypass is added.",
        "NabdhV1ShieldDisclosure": "Opt-in link signals only. Not a real-time blacklist, virus scanner or guarantee of safe files.",
        "NabdhV1ManualDisclosure": "Local analysis of only the text you explicitly enter. No unread chats are accessed. Saved notes are encrypted on this device only.",
        "NabdhV1Empty": "Enter or paste text first",
        "NabdhV1Close": "Close",
        "NabdhV1Copy": "Copy result",
    },
    "values-ar": {
        "NabdhV1InputHint": "الصق نصًا أو رابطًا أو مقتطف محادثة (لا تتم قراءة الرسائل تلقائيًا)",
        "NabdhV1Shield": "فحص مؤشرات الروابط محليًا",
        "NabdhV1Scam": "فحص مؤشرات احتيال النص محليًا",
        "NabdhV1Focus": "استخراج مؤشرات التركيز من النص",
        "NabdhV1CatchUp": "مراجعة مقتطف محادثة ملصق",
        "NabdhV1Save": "حفظ ملاحظة محلية مشفرة",
        "NabdhV1OpenWorkspace": "فتح الملاحظات المحفوظة",
        "NabdhV1DataSettings": "البيانات والتنزيل التلقائي للواي فاي والجوال",
        "NabdhV1CacheSettings": "إدارة التخزين والذاكرة المؤقتة",
        "NabdhV1ProxySettings": "إعدادات البروكسي الرسمية",
        "NabdhV1NetworkDisclosure": "تُفتح إعدادات Telegram الأصلية للبيانات والتخزين والبروكسي دون إضافة محرك تحسين اتصال وهمي أو تجاوز أي حدود.",
        "NabdhV1ShieldDisclosure": "تحذيرات محلية اختيارية فقط؛ ليست قاعدة روابط ضارة أو فحص فيروسات أو ضمانًا لسلامة الملفات.",
        "NabdhV1ManualDisclosure": "يحلل التطبيق النص الذي تدخله فقط؛ لا يصل تلقائيًا للمحادثات غير المقروءة. الملاحظات المحفوظة مشفرة محليًا على هذا الجهاز.",
        "NabdhV1Empty": "أدخل نصًا أو الصقه أولًا",
        "NabdhV1Close": "إغلاق",
        "NabdhV1Copy": "نسخ النتيجة",
    }
}
for locale, catalog in strings.items():
    output = root / "TMessagesProj/src/main/res" / locale / "nabdh_v1_tools.xml"
    if output.exists():
        raise SystemExit("V1 Android localization already exists: " + str(output))
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    lines.extend('    <string name="' + key + '">' + escape(value) + '</string>'
                 for key, value in catalog.items())
    lines.append("</resources>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("PASS: opt-in local Focus, Shield, manual recap and encrypted workspace integrated")
