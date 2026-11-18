#!/usr/bin/env python3
"""Pinned-source acceptance gate for private, explicit Telegram server scheduling."""
from pathlib import Path
import xml.etree.ElementTree as ET
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-message-scheduler.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main"
ui = root / "java/org/telegram/ui"
scheduler = (ui / "NabdhMessageSchedulerActivity.java").read_text(encoding="utf-8")
category = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
manifest = (root / "AndroidManifest.xml").read_text(encoding="utf-8")
def test(yes, why):
    if not yes: raise SystemExit("FAIL: scheduler " + why)
test('android:name="org.telegram.ui.NabdhMessageSchedulerActivity"' in manifest and
     'android:exported="false"' in manifest.split('android:name="org.telegram.ui.NabdhMessageSchedulerActivity"')[1].split("/>")[0],
     "must remain private, not callable via another app")
test("if (featureId == 202)" in category and
     "NabdhSchedulerComposeInfo" in category and
     "NabdhMessageSchedulerActivity.class" in category,
     "must replace old help-only schedule page without changing its ID")
test("ContactsController.getInstance(account).contacts" in scheduler and
     "getUser(entry.user_id)" in scheduler and
     "chooseRecipients()" in scheduler and
     "LinkedHashMap<Long, ContactChoice> selected" in scheduler and
     "renderChoices(list, pending" in scheduler and
     "AutoCompleteTextView" not in scheduler,
     "must use bounded native multi-selection rather than dark system dropdown")
test("DatePickerDialog" in scheduler and "TimePickerDialog" in scheduler and
     "if (!dateChosen || !timeChosen)" in scheduler,
     "must collect an explicit date and time")
test("InputFilter.LengthFilter(4096)" in scheduler and
     "TextUtils.isEmpty(text)" in scheduler,
     "must validate bounded nonempty messages")
test("date <= now + 60" in scheduler and
     "date > now + 365L * 24L * 3600L" in scheduler,
     "must reject expired and excessively distant schedules")
test("SendMessagesHelper.SendMessageParams.of(text, peer)" in scheduler and
     "params.scheduleDate = when;" in scheduler and
     "SendMessagesHelper.getInstance(account).sendMessage(params)" in scheduler and
     "for (ContactChoice choice : recipients)" in scheduler and
     "MAX_RECIPIENTS = 20" in scheduler and
     "controller.getUser(choice.id)" in scheduler,
     "must prevalidate recipients, bound their count and use native per-peer scheduling")
test(".setPositiveButton(local(\"Schedule\", \"جدولة\"), (dialog, which) -> {" in scheduler and
     "UserConfig.getInstance(account).isClientActivated()" in scheduler,
     "must require user confirmation and active Telegram session")
for forbidden in ("AlarmManager", "WorkManager", "SmsManager", "ACCESS_CONTACTS", "READ_CONTACTS", "TimerTask"):
    test(forbidden not in scheduler, "may not introduce independent send, device SMS or address-book access: " + forbidden)
for lang in ("values", "values-ar"):
    resources = root / "res" / lang / "nabdh_message_scheduler.xml"
    test(resources.exists(), "missing native schedule labels in " + lang)
    values = {item.get("name"):item.text for item in ET.parse(resources).getroot()}
    test(set(values) == {"NabdhSchedulerCompose", "NabdhSchedulerComposeInfo"},
         "schedule label mismatch " + lang)
print("PASS: explicit multi-recipient contact selection and native bounded scheduling")
