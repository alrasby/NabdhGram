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
        "getScaledTouchSlop()" in dialogs
        and "Math.abs(dy) * 1.5f" in dialogs
        and "downX <= dp(24)" in dialogs,
    "reverse gesture and tap-outside close":
        "expanded.setTranslationX(Math.max(0f, dp(212) + dx));" in dialogs
        and "row.getTranslationX() < dp(135)" in dialogs
        and "Outside tap dismisses without chat opening." in dialogs,
    "physical spring with damping and stiffness":
        "new androidx.dynamicanimation.animation.SpringAnimation" in dialogs
        and "force.setStiffness(550f);" in dialogs
        and "force.setDampingRatio(0.88f);" in dialogs
        and "spring.setMinimumVisibleChange(0.7f);" in dialogs,
    "four actual tappable row views not canvas labels":
        "nabdhSmartBar.addView(button" in cell
        and "button.setOnClickListener(" in cell
        and 'new String[]{"Remind", "Mute", "Pin", "Archive"}' in cell
        and "row.nabdhSetSmartSwipeActions(index ->" in dialogs,
    "actions require explicit tap":
        "nabdhRunSmartAction(dialogId, index)" in dialogs
        and "performSelectedDialogsAction(selected, archive, true, false)" in dialogs
        and "performSelectedDialogsAction(selected, pin, true, false)" in dialogs,
    "card surface remains fixed while reveal slides":
        "if (translationX < 0)" in cell
        and "nabdhCardBounds.set(dp(7), dp(3)" in cell
        and "nabdhSmartBar.setAlpha(Math.min(1f, value / dp(100)))" in cell,
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
        "stopSwipeOnScroll[0].run();" in dialogs
        and "if (spring != null) spring.cancel();" in dialogs
        and "expanded.nabdhClearSmartSwipeActions();" in dialogs,
    "RTL actions layout and reduced motion preference":
        "setLayoutDirection(LocaleController.isRTL" in cell
        and "ValueAnimator.areAnimatorsEnabled()" in dialogs,
    "opposite-direction reveal skips native Telegram circle animation":
        "drawRevealBackground = translationX < 0" in cell
        and "translationX >= dp(70)" in cell,
    "guard against delayed RecyclerListView chat opening":
        "nabdhIgnoreItemClicksUntil" in dialogs
        and "android.os.SystemClock.uptimeMillis() + 450L" in dialogs
        and "page.listView.cancelClickRunnables(true);" in dialogs,
    "expanded tray consumes DOWN-UP without opening background chat":
        "page.listView.cancelClickRunnables(true);" in dialogs
        and "consumedDown = true;" in dialogs
        and "row.nabdhPerformSmartAction(actionIndex);" in dialogs
        and "pressedAction = LocaleController.isRTL ? 3 - visual : visual;" in dialogs,
    "reverse swipe closes the tray without tapping":
        "expanded.setTranslationX(Math.max(0f, dp(212) + dx));" in dialogs
        and "row.getTranslationX() < dp(135)" in dialogs,
    "dynamic labels match actual muted/pinned/archived state":
        "getMessagesController().isDialogMuted(dialogId, 0)" in dialogs
        and "isDialogPinned(current), current.folder_id != 0" in dialogs
        and '"Unmute"' in cell and '"Unpin"' in cell and '"Unarchive"' in cell
        and "nabdhSetSmartSwipeActions(NabdhSmartAction callback," in cell,
    "native READ reveal clipped to same rounded Glass card":
        "nabdhSwipeRevealClip.reset();" in cell
        and "canvas.clipPath(nabdhSwipeRevealClip);" in cell
        and "nabdhCardBounds.set(dp(7), dp(3)" in cell,
    "four independent rounded pill backgrounds and Android ripple":
        "new android.graphics.drawable.RippleDrawable" in cell
        and "lp.setMargins(dp(2), dp(3), dp(2), dp(3));" in cell
        and "pill.setCornerRadius(dp(11));" in cell,
    "RIGHT tray has no opaque window background":
        "surface.setColor(android.graphics.Color.argb(30," in cell
        and "final int glassAccent = Theme.getColor(Theme.key_chats_archiveBackground);" in cell,
    "native reveal does not run when spring keeps stale corner progress on RIGHT":
        "if (translationX < 0)" in cell
        and "drawRevealBackground = translationX < 0" in cell,
    "native RIGHT white backing suppressed without changing LEFT":
        "if (translationX < 0 || (translationX == 0 && cornerProgress != 0.0f))" in cell
        and "Theme.dialogs_pinnedPaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhite" in cell,
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
