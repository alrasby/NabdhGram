#!/usr/bin/env python3
"""Install explicit contact/date/time scheduled-message UI into NabdhGram V1.

Uses Telegram's own SendMessagesHelper with scheduleDate and never schedules
background local alarms or sends a message absent user confirmation.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-message-scheduler.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
source = Path(__file__).resolve().parents[1] / "overlay/java/NabdhMessageSchedulerActivity.java"
target = ui / "NabdhMessageSchedulerActivity.java"
if target.exists():
    raise SystemExit("Scheduler duplicate class collision")
target.write_bytes(source.read_bytes())

manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
anchor = '        <activity android:name="org.telegram.ui.NabdhBrowserActivity"'
if m.count(anchor) != 1:
    raise SystemExit("Nabdh Browser manifest anchor changed")
m = m.replace(anchor, """        <activity android:name="org.telegram.ui.NabdhMessageSchedulerActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
""" + anchor, 1)
manifest.write_text(m, encoding="utf-8")

page = ui / "NabdhGramFeatureCategoryActivity.java"
s = page.read_text(encoding="utf-8")
start_pattern = "        if (featureId == 202) {"
if s.count(start_pattern) != 1:
    raise SystemExit("Unexpected scheduled-message help page routing")
start = s.index(start_pattern)
end_marker = "            content.addView(scheduleInfo);"
end = s.index(end_marker, start) + len(end_marker)
close = s.index("\n        }", end) + len("\n        }")
old = s[start:close]
if "scheduleTitle" not in old or "scheduleInfo" not in old:
    raise SystemExit("Scheduled-message helper structure changed")
new = """        if (featureId == 202) {
            // User-selected recipient + date + time + message are handled in
            // one private screen; native Telegram queues the schedule server-side.
            org.telegram.ui.Components.NabdhCompactSettings.row(
                    context, content,
                    NabdhStrings.get(context, R.string.NabdhSchedulerCompose),
                    NabdhStrings.get(context, R.string.NabdhSchedulerComposeInfo),
                    0, () -> context.startActivity(new android.content.Intent(
                            context, NabdhMessageSchedulerActivity.class)));
        }"""
s = s[:start] + new + s[close:]
page.write_text(s, encoding="utf-8")

translations = {
    "values": {
        "NabdhSchedulerCompose": "Schedule a new message",
        "NabdhSchedulerComposeInfo": "Choose contact, date, time and message",
    },
    "values-ar": {
        "NabdhSchedulerCompose": "جدولة رسالة جديدة",
        "NabdhSchedulerComposeInfo": "اختر المستلم والتاريخ والوقت ونص الرسالة",
    },
}
from xml.sax.saxutils import escape
for locale, labels in translations.items():
    dest = root / "TMessagesProj/src/main/res" / locale / "nabdh_message_scheduler.xml"
    if dest.exists():
        raise SystemExit("Scheduler resource name collision")
    parts = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for key, val in labels.items():
        parts.append(f'    <string name="{key}">{escape(val)}</string>')
    dest.write_text("\n".join(parts + ["</resources>", ""]), encoding="utf-8")
# The old scheduled-messages description pointed only to long-press Send.
# Reword the existing detail page so it accurately describes this new form.
for locale, old, new in (
    ("values", "Use Telegram's native long-press Send menu to schedule messages.",
     "Choose a Telegram contact, date, time and message below. Telegram stores scheduled messages on its servers."),
    ("values-ar", "استخدم قائمة Telegram الأصلية بالضغط المطول على الإرسال لجدولة الرسائل.",
     "اختر جهة اتصال في Telegram والتاريخ والوقت والرسالة أدناه. يحفظ Telegram الرسالة المجدولة على خوادمه."),
):
    resource = root / "TMessagesProj/src/main/res" / locale / "nabdh_v1_hierarchy.xml"
    raw = resource.read_text(encoding="utf-8")
    old_label = '<string name="NabdhHScheduledDescription">' + old + '</string>'
    new_label = '<string name="NabdhHScheduledDescription">' + new + '</string>'
    if raw.count(old_label) != 1:
        raise SystemExit("Scheduled explanation resource changed: " + locale)
    resource.write_text(raw.replace(old_label, new_label, 1), encoding="utf-8")

print("PASS: private Telegram-backed message scheduler replaced old help-only page")
