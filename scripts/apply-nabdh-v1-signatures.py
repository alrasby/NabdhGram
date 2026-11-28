#!/usr/bin/env python3
"""Install approved V1 local productivity and safety tools on pinned Telegram.

Local tools for explicit message actions and bounded cached excerpts.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-v1-signatures.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
source_templates = Path(__file__).resolve().parent.parent / "overlay/java"

for name in ("NabdhV1Engine.java", "NabdhWorkspace.java", "NabdhFileGuard.java", "NabdhMessageTools.java"):
    target = ui / "Components" / name
    if target.exists():
        raise SystemExit("Existing native component: " + name)
    target.write_text((source_templates / name).read_text(encoding="utf-8"), encoding="utf-8")

chat = ui / "ChatActivity.java"
chat_source = chat.read_text(encoding="utf-8")
for anchor, replacement in (
    ("    public final static int OPTION_STOP_LIVE_LOCATION = 118;",
     """    public final static int OPTION_STOP_LIVE_LOCATION = 118;
    private static final int NABDH_V1_MESSAGE_TOOLS = 11000;"""),
    ("        if (showWelcomeMessageRevertOption(primaryMessage)) {",
     """        if (chatMode == MODE_DEFAULT && !isThreadChat() && !isInPreviewMode()
                && allowChatActions && !noforwardsOrPaidMedia && message.getDialogId() == getDialogId()
                && NabdhMessageTools.canUse(this, message)) {
            items.add(LocaleController.getString(R.string.NabdhV1MessageTools));
            options.add(NABDH_V1_MESSAGE_TOOLS);
            icons.add(R.drawable.msg_pin);
        }

        if (showWelcomeMessageRevertOption(primaryMessage)) {"""),
    ("        switch (option) {\n            case OPTION_RETRY:",
     """        switch (option) {
            case NABDH_V1_MESSAGE_TOOLS:
                NabdhMessageTools.show(this, selectedObject);
                break;
            case OPTION_RETRY:"""),
):
    if chat_source.count(anchor) != 1:
        raise SystemExit("Pinned message tools anchor changed: " + anchor)
    chat_source = chat_source.replace(anchor, replacement, 1)
chat.write_text(chat_source, encoding="utf-8")

utilities = ui.parent / "messenger/AndroidUtilities.java"
utilities_source = utilities.read_text(encoding="utf-8")
open_call = "        return openForView(f, message.getFileName(), mimeType, activity, resourcesProvider, restrict);"
if utilities_source.count(open_call) != 1:
    raise SystemExit("Pinned attachment open anchor changed")
utilities_source = utilities_source.replace(open_call, """        String fileName = message.getFileName();
        if (message.type == MessageObject.TYPE_FILE && activity != null
                && !activity.isFinishing() && !activity.isDestroyed()) {
            final boolean arabic = org.telegram.ui.Components.NabdhMessageTools.isArabic();
            String warning = org.telegram.ui.Components.NabdhFileGuard.warningBeforeOpen(
                    f, fileName, mimeType, arabic);
            if (warning != null) {
                final File localFile = f;
                new AlertDialog.Builder(activity, resourcesProvider)
                        .setTitle(LocaleController.getString(R.string.NabdhShieldTitle))
                        .setMessage(warning)
                        .setNegativeButton(LocaleController.getString(R.string.NabdhV1Cancel), null)
                        .setPositiveButton(LocaleController.getString(R.string.NabdhV1OpenAnyway), (dialog, which) -> {
                            if (!activity.isFinishing() && !activity.isDestroyed()) {
                                openForView(localFile, fileName, mimeType, activity, resourcesProvider, restrict);
                            }
                        }).show();
                return true;
            }
        }
        return openForView(f, fileName, mimeType, activity, resourcesProvider, restrict);""", 1)
utilities.write_text(utilities_source, encoding="utf-8")

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
        if (featureId == 101 || featureId == 301) {
            nabdhV1Button(context, content, R.string.NabdhV1TryExample, () ->
                nabdhV1Result(context, nabdhText(context, featureId == 301
                                ? R.string.NabdhV1FocusExample : R.string.NabdhV1ShieldExample),
                        featureId == 301 ? R.string.NabdhHFocus : R.string.NabdhHLinks,
                        featureId == 301 ? 0 : 2));
        }
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
                    context, org.telegram.ui.Components.NabdhMessageTools.isArabic(), this));
            if (featureId == 303) nabdhV1Button(context, content, R.string.NabdhV1UnreadDigest,
                () -> org.telegram.ui.Components.NabdhMessageTools.showUnreadDigest(this));
        }
    }

"""
patch("    private void addPrivacyControls(Context context, LinearLayout content) {",
      methods + "    private void addPrivacyControls(Context context, LinearLayout content) {",
      "V1 local tool methods")
category.write_text(s, encoding="utf-8")

strings = {
    "values": {
        "NabdhV1TryExample": "Try an example",
        "NabdhV1FocusExample": "We agreed to send the report by 2026-12-05. Please review the figures. What still needs approval?",
        "NabdhV1ShieldExample": "http://example.test/report",
        "NabdhV1MessageTools": "Message tools",
        "NabdhV1FocusMessage": "Extract focus signals",
        "NabdhV1CreateLinkedNote": "Save linked note",
        "NabdhV1CreateLinkedTask": "Save linked task",
        "NabdhV1RemindMessage": "Remind about this message in an hour",
        "NabdhV1CheckMessageSafety": "Check link and scam signals",
        "NabdhV1ReturnToMessage": "Return to message",
        "NabdhV1TaskHint": "Enter a task",
        "NabdhV1NoteHint": "Enter a note",
        "NabdhV1LinkedTask": "Linked task",
        "NabdhV1LinkedNote": "Linked note",
        "NabdhV1Cancel": "Cancel",
        "NabdhV1SaveItem": "Save",
        "NabdhV1SavedItem": "Saved encrypted on this device.",
        "NabdhV1SaveItemFailed": "Could not save the item.",
        "NabdhV1MediaMessage": "Media message",
        "NabdhV1ReminderAlreadySet": "This chat already has a reminder.",
        "NabdhV1ReminderEnableNotifications": "Enable notifications to receive reminders.",
        "NabdhV1ReminderScheduled": "Local reminder set for about one hour.",
        "NabdhV1ReminderFailed": "Could not schedule the reminder.",
        "NabdhV1UnreadDigestTitle": "Local unread digest",
        "NabdhV1UnreadDigestEmpty": "No eligible unread chats are cached for this account.",
        "NabdhV1UnreadDigestScope": "Shows up to 12 chats and the latest unread message available locally.",
        "NabdhV1ReopenTask": "Reopen task",
        "NabdhV1CompleteTask": "Complete task",
        "NabdhV1CopyItem": "Copy",
        "NabdhV1DeleteItem": "Delete",
        "NabdhV1ConfirmDeleteItem": "Delete local item?",
        "NabdhV1SavedTaskTitle": "Saved task",
        "NabdhV1SavedNoteTitle": "Saved note",
        "NabdhV1AttachedFile": "Attached file: %1$s",
        "NabdhV1UnreadDigestRow": "%1$s · Unread: %2$d",
        "NabdhV1OpenAnyway": "Open anyway",
        "NabdhV1MessageReminderTitle": "Message reminder",
        "NabdhV1MessageReminderText": "Tap to open the message",
        "NabdhV1InputHint": "Paste text, a link or a conversation excerpt (nothing is read automatically)",
        "NabdhV1Shield": "Check local URL warning signals",
        "NabdhV1Scam": "Check local message scam signals",
        "NabdhV1Focus": "Extract focus signals from pasted text",
        "NabdhV1CatchUp": "Review pasted conversation excerpt",
        "NabdhV1UnreadDigest": "Review cached unread chats",
        "NabdhV1Save": "Save encrypted local note",
        "NabdhV1OpenWorkspace": "Open saved local notes",
        "NabdhV1DataSettings": "Wi-Fi and mobile data / auto-download",
        "NabdhV1CacheSettings": "Storage and cache manager",
        "NabdhV1ProxySettings": "Telegram proxy settings",
        "NabdhV1NetworkDisclosure": "Open the official Telegram data, storage and proxy controls. No hidden connection optimizer or Premium bypass is added.",
        "NabdhV1ShieldDisclosure": "Local link signals and header checks for downloaded chat documents. Warnings are limited risk signals.",
        "NabdhV1ManualDisclosure": "Local analysis of only the text you explicitly enter. No unread chats are accessed. Saved notes are encrypted on this device only.",
        "NabdhV1Empty": "Enter or paste text first",
        "NabdhV1Close": "Close",
        "NabdhV1Copy": "Copy result",
    },
    "values-ar": {
        "NabdhV1TryExample": "جرّب مثالًا",
        "NabdhV1FocusExample": "تم الاتفاق على إرسال التقرير في 2026-12-05. يرجى مراجعة الأرقام. ماذا بقي للموافقة؟",
        "NabdhV1ShieldExample": "http://example.test/report",
        "NabdhV1MessageTools": "أدوات الرسالة",
        "NabdhV1FocusMessage": "استخراج النقاط المهمة",
        "NabdhV1CreateLinkedNote": "حفظ كملاحظة مرتبطة",
        "NabdhV1CreateLinkedTask": "حفظ كمهمة مرتبطة",
        "NabdhV1RemindMessage": "تذكير بالرسالة بعد ساعة",
        "NabdhV1CheckMessageSafety": "فحص مؤشرات الروابط والاحتيال",
        "NabdhV1ReturnToMessage": "العودة إلى الرسالة",
        "NabdhV1TaskHint": "اكتب المهمة",
        "NabdhV1NoteHint": "اكتب ملاحظتك",
        "NabdhV1LinkedTask": "مهمة مرتبطة",
        "NabdhV1LinkedNote": "ملاحظة مرتبطة",
        "NabdhV1Cancel": "إلغاء",
        "NabdhV1SaveItem": "حفظ",
        "NabdhV1SavedItem": "حُفظ العنصر مشفراً على الجهاز.",
        "NabdhV1SaveItemFailed": "تعذّر حفظ العنصر.",
        "NabdhV1MediaMessage": "رسالة وسائط",
        "NabdhV1ReminderAlreadySet": "يوجد تذكير لهذه المحادثة.",
        "NabdhV1ReminderEnableNotifications": "فعّل الإشعارات أولاً لتلقي التذكير.",
        "NabdhV1ReminderScheduled": "ضُبط تذكير محلي خلال نحو ساعة.",
        "NabdhV1ReminderFailed": "تعذّر ضبط التذكير.",
        "NabdhV1UnreadDigestTitle": "ملخص غير المقروء محلياً",
        "NabdhV1UnreadDigestEmpty": "لا توجد محادثات غير مقروءة متاحة في ذاكرة الحساب.",
        "NabdhV1UnreadDigestScope": "يعرض حتى 12 محادثة وآخر رسالة غير مقروءة متاحة محلياً.",
        "NabdhV1ReopenTask": "إعادة فتح المهمة",
        "NabdhV1CompleteTask": "إكمال المهمة",
        "NabdhV1CopyItem": "نسخ",
        "NabdhV1DeleteItem": "حذف",
        "NabdhV1ConfirmDeleteItem": "حذف العنصر المحلي؟",
        "NabdhV1SavedTaskTitle": "مهمة محفوظة",
        "NabdhV1SavedNoteTitle": "ملاحظة محفوظة",
        "NabdhV1AttachedFile": "الملف المرفق: %1$s",
        "NabdhV1UnreadDigestRow": "%1$s · غير مقروءة: %2$d",
        "NabdhV1OpenAnyway": "فتح على أي حال",
        "NabdhV1MessageReminderTitle": "تذكير برسالة",
        "NabdhV1MessageReminderText": "اضغط لفتح الرسالة",
        "NabdhV1InputHint": "الصق نصًا أو رابطًا أو مقتطف محادثة (لا تتم قراءة الرسائل تلقائيًا)",
        "NabdhV1Shield": "فحص مؤشرات الروابط محليًا",
        "NabdhV1Scam": "فحص مؤشرات احتيال النص محليًا",
        "NabdhV1Focus": "استخراج مؤشرات التركيز من النص",
        "NabdhV1CatchUp": "مراجعة مقتطف محادثة ملصق",
        "NabdhV1UnreadDigest": "مراجعة المحادثات غير المقروءة محلياً",
        "NabdhV1Save": "حفظ ملاحظة محلية مشفرة",
        "NabdhV1OpenWorkspace": "فتح الملاحظات المحفوظة",
        "NabdhV1DataSettings": "البيانات والتنزيل التلقائي للواي فاي والجوال",
        "NabdhV1CacheSettings": "إدارة التخزين والذاكرة المؤقتة",
        "NabdhV1ProxySettings": "إعدادات البروكسي الرسمية",
        "NabdhV1NetworkDisclosure": "تُفتح إعدادات Telegram الأصلية للبيانات والتخزين والبروكسي دون إضافة محرك تحسين اتصال وهمي أو تجاوز أي حدود.",
        "NabdhV1ShieldDisclosure": "مؤشرات محلية للروابط وفحص توقيع المستندات المنزّلة من المحادثات. التحذيرات مؤشرات محدودة للمخاطر.",
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
