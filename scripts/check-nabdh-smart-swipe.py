#!/usr/bin/env python3
"""Fail fast if Smart Swipe V1 is partially installed or LEFT behavior regresses."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-smart-swipe.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main"
dialogs = (root / "java/org/telegram/ui/DialogsActivity.java").read_text(encoding="utf-8")
cell = (root / "java/org/telegram/ui/Cells/DialogCell.java").read_text(encoding="utf-8")
receiver = (root / "java/org/telegram/ui/NabdhSwipeReminder.java").read_text(encoding="utf-8")
manifest = ET.parse(root / "AndroidManifest.xml").getroot()
android = "{http://schemas.android.com/apk/res/android}"
checks = {
    "LEFT native action preserved": "ItemTouchHelper.LEFT | ItemTouchHelper.RIGHT" in dialogs
        and "if (direction == ItemTouchHelper.RIGHT)" in dialogs
        and "if (!getMessagesController().isPromoDialog(dialogId, false)" in dialogs,
    "RIGHT only offers intentional actions": "showNabdhSmartSwipeActions(dialogId)" in dialogs
        and "menu.setItems(choices," in dialogs
        and "performSelectedDialogsAction(selected, archive, true, false)" in dialogs,
    "reminders offer 30m, 2h, next morning, custom, cancel":
        "30 * 60_000L" in dialogs and "2 * 60 * 60_000L" in dialogs
        and "Calendar.DAY_OF_YEAR" in dialogs and "DatePickerDialog" in dialogs
        and "NabdhSwipeReminder.cancel" in dialogs,
    "chat opening uses correct Telegram account": 'putExtra("currentAccount", account)' in receiver
        and 'setAction("com.tmessages.openchat")' in receiver
        and "DialogObject.getEncryptedChatId(dialogId)" in receiver,
    "scheduled alarms persist and reboot": "ACTION_BOOT_COMPLETED" in receiver
        and "setAndAllowWhileIdle" in receiver
        and "SharedPreferences" in receiver,
    "permission respected": "POST_NOTIFICATIONS" in receiver
        and "POST_NOTIFICATIONS" in dialogs,
    "rightward short reveal is cancellable": "return 1.1f;" in dialogs
        and "peek.getTranslationX() > peek.getMeasuredWidth() * 0.22f" in dialogs
        and "showNabdhSmartSwipeActions(peekDialogId)" in dialogs
        and "translationX > 0 ? 0.22f : 0.45f" in cell,
    "rounded tray and translated card": "NabdhGram Smart Swipe: LEFT side action tray" in cell
        and "nabdhCardBounds.set(dp(7), dp(3)" in cell,
    "haptics respect device preference": "performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);" in cell,
    "return animation duration softens": "return 230; // Soft return" in dialogs,
    "receiver registered unexported": any(
        n.attrib.get(android + "name") == "org.telegram.ui.NabdhSwipeReminder"
        and n.attrib.get(android + "exported") == "false"
        for n in manifest.findall(".//receiver")),
}
failed = [name for name, result in checks.items() if not result]
for name, passed in checks.items():
    print(("PASS " if passed else "FAIL ") + name)
if failed:
    raise SystemExit("Smart Swipe V1 overlay incomplete: " + ", ".join(failed))
