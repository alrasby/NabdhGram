#!/usr/bin/env python3
"""Smart Swipe source checks: independent directions, clickable row buttons and actual spring."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-smart-swipe.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main"
dialogs = (root / "java/org/telegram/ui/DialogsActivity.java").read_text(encoding="utf-8")
cell = (root / "java/org/telegram/ui/Cells/DialogCell.java").read_text(encoding="utf-8")
controller = (root / "java/org/telegram/ui/Components/NabdhSmartSwipeController.java").read_text(encoding="utf-8")
receiver = (root / "java/org/telegram/ui/NabdhSwipeReminder.java").read_text(encoding="utf-8")
manifest = ET.parse(root / "AndroidManifest.xml").getroot()
android = "{http://schemas.android.com/apk/res/android}"
checks = {
    "LEFT original direction retained without ItemTouchHelper RIGHT":
        "return makeMovementFlags(0, ItemTouchHelper.LEFT);" in dialogs
        and "ItemTouchHelper.LEFT | ItemTouchHelper.RIGHT" not in dialogs
        and "installNabdhSmartSwipe(viewPage);" in dialogs,
    "gesture listener installs before ItemTouchHelper":
        dialogs.index("installNabdhSmartSwipe(viewPage);") <
        dialogs.index("viewPage.itemTouchhelper = new ItemTouchHelper("),
    "gesture respects touch-slop, vertical scroll, and edge back":
        "getScaledTouchSlop()" in controller
        and "NabdhSwipeMotion.classify(" in controller
        and "downX <= dp(24)" in controller,
    "reverse gesture and tap-outside close":
        "actionStartOffset, dx, dp(212)" in controller
        and "row.getTranslationX() < dp(135)" in controller
        and "Outside tap dismisses without chat opening." in controller,
    "physical spring with damping and stiffness":
        "new SpringAnimation" in controller
        and "force.setStiffness(550f);" in controller
        and "force.setDampingRatio(0.88f);" in controller
        and "spring.setMinimumVisibleChange(0.7f);" in controller,
    "four actual tappable row views not canvas labels":
        "nabdhSmartBar.addView(button" in cell
        and "button.setOnClickListener(" in cell
        and 'new String[]{"Remind", "Mute", "Pin", "Archive"}' in cell
        and "row.nabdhSetSmartSwipeActions(callback," in dialogs,
    "actions require explicit tap":
        "nabdhRunSmartAction(dialogId, action)" in dialogs
        and "getMessagesController().addDialogToFolder(" in dialogs
        and "updated.folder_id != targetFolder" in dialogs
        and "canMoveToFolder(" in dialogs
        and "performSelectedDialogsAction(selected, pin, true, false)" in dialogs,
    "card surface remains fixed while reveal slides":
        "if (translationX < 0)" in cell
        and "nabdhCardEngine.setViewport(" in cell
        and "nabdhUpdateSmartTrayClip(value);" in cell
        and "nabdhSmartBar.setClipBounds(nabdhSmartTrayClip);" in cell
        and "nabdhSmartBar.setAlpha(Math.min" not in cell,
    "haptic once, obeys device vibration preference":
        "nabdhSwipeHapticTriggered = true;" in cell
        and "nabdhSwipeHapticTriggered = false;" in cell
        and "performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);" in cell
        and "FLAG_IGNORE_GLOBAL_SETTING" not in cell[cell.index("nabdhSwipeHapticTriggered = true;"):cell.index("nabdhSwipeHapticTriggered = true;")+360],
    "story/avatar touch does not intercept four inline buttons":
        "nabdhHitSmartAction(ev)" in cell
        and "nabdhHitSmartAction(event)" in cell
        and "return super.dispatchTouchEvent(ev);" in cell,
    "active spring cancels before vertical list scroll":
        "page.nabdhCancelSwipe.run();" in dialogs
        and "if (spring != null) spring.cancel();" in controller
        and "row.nabdhClearSmartSwipeActions();" in controller,
    "RTL actions layout and reduced motion preference":
        "button.layout(width - button.getRight(), button.getTop()," in cell
        and "ValueAnimator.areAnimatorsEnabled()" in controller,
    "opposite-direction reveal skips native Telegram circle animation":
        "drawRevealBackground = translationX < 0" in cell
        and "translationX >= dp(70)" in cell,
    "guard against delayed RecyclerListView chat opening":
        "nabdhIgnoreItemClicksUntil" in dialogs
        and "android.os.SystemClock.uptimeMillis() + 450L" in dialogs
        and "page.listView.cancelClickRunnables(true);" in dialogs,
    "expanded tray consumes DOWN-UP without opening background chat":
        "page.listView.cancelClickRunnables(true);" in dialogs
        and "gesture = Gesture.TRAY_TOUCH;" in controller
        and "row.nabdhPerformSmartAction(actionIndex);" in controller
        and "pressedAction = expanded.nabdhSmartActionAt(cx, cy);" in controller
        and "expanded.nabdhSmartActionAt(" in controller
        and "actionPress.release(" in controller
        and "button.getLeft()" in cell and "button.getRight()" in cell
        and "nabdhSetSmartPressed(-1)" in cell,
    "reverse swipe closes the tray without tapping":
        "actionStartOffset, dx, dp(212)" in controller
        and "row.getTranslationX() < dp(135)" in controller,
    "dynamic labels match actual muted/pinned/archived state":
        "getMessagesController().isDialogMuted(id, 0)" in dialogs
        and "isDialogPinned(dialog), dialog.folder_id != 0" in dialogs
        and '"Unmute"' in cell and '"Unpin"' in cell and '"Unarchive"' in cell
        and "nabdhSetSmartSwipeActions(NabdhSmartAction callback," in cell,
    "native READ reveal clipped to same rounded Glass card":
        "nabdhCardEngine.clipViewport(canvas)" in cell
        and "nabdhCardEngine.clipTrailingAction(canvas, translationX)" in cell
        and "nabdhCardEngine.setViewport(" in cell,
    "four independent rounded pill backgrounds and Android ripple":
        "new android.graphics.drawable.RippleDrawable" in cell
        and "lp.setMargins(dp(2), dp(3), dp(2), dp(3));" in cell
        and "pill.setCornerRadius(dp(11));" in cell,
    "RIGHT tray has opaque themed reveal and clipped interactive buttons":
        "nabdhSmartBar.setBackground(null);" in cell
        and "super.draw(canvas);" in cell
        and "canvas.restoreToCount(saved);" in cell
        and "if (translationX > 0 && nabdhOwnsCard())" in cell
        and cell.index("Stationary reveal surface:") < cell.index("canvas.translate(translationX, 0);"),
    "native reveal does not run when spring keeps stale corner progress on RIGHT":
        "if (translationX < 0)" in cell
        and "drawRevealBackground = translationX < 0" in cell,
    "native rectangular and circle fills excluded from owned card action surface":
        "if (!nabdhOwnsCard()) {\n                    canvas.drawRect(tx - dp(8)" in cell
        and "if (!nabdhOwnsCard()) {\n                    canvas.drawCircle(drawableCx" in cell
        and "nabdhCardEngine.drawAction(canvas, backgroundColor, revealBackgroundColor," in cell,
    "native backing excluded for owned cards in both directions":
        "if (!nabdhOwnsCard() && (translationX != 0 || cornerProgress != 0.0f))" in cell
        and "nabdhCardEngine.clipTrailingAction(canvas, translationX)" in cell,
    "reminder chooser uses NabdhGram-themed rounded Glass options":
        "nabdhSwipeBlend(background, accent, 0.075f)" in dialogs
        and "capsule.setCornerRadius(dp(14));" in dialogs
        and "chooser.setBackgroundColor(background);" in dialogs
        and "new android.graphics.drawable.RippleDrawable(" in dialogs
        and "setLayoutDirection(rtl" in dialogs,
    "reminder action offers settings and confirms schedule/cancel":
        "nabdhShowReminderConfirmation(when);" in dialogs
        and "nabdhShowReminderConfirmation(chosen.getTimeInMillis());" in dialogs
        and "ACTION_APP_NOTIFICATION_SETTINGS" in dialogs,
    "reminder choices and custom date/time":
        "30 * 60_000L" in dialogs and "2 * 60 * 60_000L" in dialogs
        and "Calendar.DAY_OF_YEAR" in dialogs and "DatePickerDialog" in dialogs
        and "NabdhSwipeReminder.cancel" in dialogs,
    "reminder survives process restart and device reboot":
        "ACTION_BOOT_COMPLETED" in receiver and "setAndAllowWhileIdle" in receiver
        and "SharedPreferences" in receiver,
    "reminder identifies account/chat including secret chat":
        'putExtra("currentAccount", account)' in receiver
        and 'setAction("com.tmessages.openchat")' in receiver
        and "DialogObject.getEncryptedChatId(dialogId)" in receiver,
    "Android 13 notification permission respected":
        "POST_NOTIFICATIONS" in receiver and "POST_NOTIFICATIONS" in dialogs,
    "nonexported receiver in manifest": any(
        n.attrib.get(android+"name") == "org.telegram.ui.NabdhSwipeReminder"
        and n.attrib.get(android+"exported") == "false"
        for n in manifest.findall(".//receiver")),
}
for name, ok in checks.items():
    print(("PASS " if ok else "FAIL ") + name)
if not all(checks.values()):
    raise SystemExit("Smart Swipe V1.1 regression check failed")
