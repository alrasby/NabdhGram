#!/usr/bin/env python3
"""Regression contract for chat-lock confidentiality and read side effects.

Source checks are NOT a substitute for physical-device notification tests.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-chat-lock-privacy.py TELEGRAM_SOURCE")

root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
chat = (ui / "ChatActivity.java").read_text(encoding="utf-8")
notification = (ui.parent / "messenger/NotificationsController.java").read_text(encoding="utf-8")
cell = (ui / "Cells/DialogCell.java").read_text(encoding="utf-8")
locks = (ui / "Components/NabdhChatLock.java").read_text(encoding="utf-8")
activity = (ui / "NabdhChatLockActivity.java").read_text(encoding="utf-8")
feed = (ui / "NabdhChannelFeedActivity.java").read_text(encoding="utf-8")
manifest = (root / "TMessagesProj/src/main/AndroidManifest.xml").read_text(encoding="utf-8")

def require(test, message):
    if not test:
        raise SystemExit("FAIL: " + message)

require("storyPushMessagesDict.remove(old.dialogId);" in notification,
        "cached protected-chat story notifications are also suppressed")
require(notification.count("NabdhChatLock.isLocked(") >= 5,
        "notifications, child notifications and popup replies are gated")
require("private String getStringForMessage(" in notification and
        "return LocaleController.getString(R.string.YouHaveNewMessage);" in notification,
        "locked message body cannot be formatted into notification details")
require(notification.count("if (org.telegram.ui.Components.NabdhChatLock.isLocked(") >= 2,
        "locked new and queued messages do not reach Android notifications")
require(chat.count("NabdhChatLock.isUnlocked(currentAccount, dialog_id)") >= 4,
        "all four native ChatActivity direct read-ack paths require PIN")
require("public static synchronized void revoke(int account, long dialog)" in locks and
        chat.count("NabdhChatLock.revoke(currentAccount, dialog_id);") == 1,
        "local PIN authorization ends on chat background")
require(chat.index("getMessagesController().markDialogAsReadNow(dialog_id, replyId);") <
        chat.index("NabdhChatLock.revoke(currentAccount, dialog_id);"),
        "final legitimate read acknowledgement must precede PIN revocation")
require("Keep FLAG_SECURE through system-recents snapshots" in chat,
        "privacy screenshot flag remains during background transitions")
require("new org.telegram.messenger.FlagSecureReason(" in chat and
        "nabdhAttachChatLockSecureReason(lockActivity);" in chat and
        "nabdhChatLockSecureReason.detach();" in chat,
        "local PIN must use Telegram's native secure-window reference counter")
require("lockActivity.getWindow().addFlags(" not in chat and
        "getParentActivity().getWindow().clearFlags(" not in chat,
        "local PIN must never override Telegram's existing FLAG_SECURE ownership")
require("NabdhChatLock.isLocked(" in feed and
        "getApplicationContext(), account, dialog.id" in feed,
        "cached Channel Feed cannot expose posts from a PIN-locked channel")
require("@Override protected void onResume()" in feed and
        "if (items != null) render();" in feed,
        "Channel Feed must hide newly locked channel previews on resume")
require("Locked chat" in cell and "محادثة مقفلة" in cell and
        "messageNameLayout = null;" in cell and "thumbsCount = 0;" in cell,
        "chat-list message, sender and media preview are suppressed")
require("nabdhRefreshLockedNotifications()" in locks and
        "public void nabdhRefreshLockedNotifications()" in notification,
        "locking refreshes Android notifications on the native notification dispatcher")
require("removeNotificationsForDialog(dialog)" not in locks,
        "locking must not alter Telegram unread counters")
require("showOrUpdateNotification(false);" in notification,
        "queued protected notifications are re-evaluated on locking")
require('android:exported="false"' in manifest and
        "org.telegram.ui.NabdhChatLockActivity" in manifest,
        "PIN management activity is private")
require("NabdhChatLock.verify(this, entered)" in activity,
        "editing locked chat settings requires the PIN")
require("@Override protected void onStop()" in activity and
        "authorized = false;" in activity and
        "@Override protected void onRestart()" in activity,
        "PIN manager must re-authenticate after backgrounding")
require("org.telegram.messenger.LocaleController.getString(" in activity and
        "Theme.key_windowBackgroundWhiteBlackText" in activity,
        "PIN manager must respect selected locale and theme")
require("DialogObject.isEncryptedDialog(dialog.id)" in activity,
        "native secret chats are not silently added to lock manager")
require("MessagesController.markDialogAsRead(" not in locks and
        "MessagesController.markDialogAsReadNow(" not in locks,
        "PIN manager never acknowledges Telegram messages")
print("PASS: source contract for PIN gating, notification redaction, popup, recents and no-read")
