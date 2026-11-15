#!/usr/bin/env python3
"""Security overlays for the optional chat PIN.

A locked dialog must not leak a message into native notifications/popups,
nor acknowledge reads solely because its invisible fragment was created.
Never change Telegram's server read-receipt/delete semantics after unlocking.
Strictly pinned to 13.2.2; fail if upstream call sites move.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-chat-lock-privacy.py TELEGRAM_SOURCE")
ui = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram/ui"


def once(text, before, after, what):
    occurrences = text.count(before)
    if occurrences != 1:
        raise SystemExit(f"Chat-lock privacy {what}: expected 1 anchor, found {occurrences}")
    return text.replace(before, after, 1)

notifications = ui.parent / "messenger/NotificationsController.java"
code = notifications.read_text(encoding="utf-8")

# Suppress all future user-visible notifications of a protected dialog, not
# just the notification collapsed body. Protect Android Auto/wearables/replies.
# This does NOT mark messages as read and does NOT affect normal chat data.
anchor = """            for (int a = 0; a < messageObjects.size(); a++) {
                MessageObject messageObject = messageObjects.get(a);
                if (messageObject.messageOwner != null"""
replacement = """            for (int a = 0; a < messageObjects.size(); a++) {
                MessageObject messageObject = messageObjects.get(a);
                if (messageObject == null ||
                    org.telegram.ui.Components.NabdhChatLock.isLocked(
                        ApplicationLoader.applicationContext, currentAccount,
                        messageObject.getDialogId())) {
                    continue;
                }
                if (messageObject.messageOwner != null"""
code = once(code, anchor, replacement, "new-message push source")

# A dialog may have been locked while unread notifications were in memory.
# Remove it from the display queue on the notifications thread, never from
# MessagesStorage or Telegram read state. This protects notification updates.
head = """    private void showOrUpdateNotification(boolean notifyAboutLast) {
        if (!getUserConfig().isClientActivated()"""
updated = """    private void showOrUpdateNotification(boolean notifyAboutLast) {
        // Existing story pushes can survive a lock toggle or process reload.
        for (int i = storyPushMessages.size() - 1; i >= 0; i--) {
            StoryNotification old = storyPushMessages.get(i);
            if (org.telegram.ui.Components.NabdhChatLock.isLocked(
                    ApplicationLoader.applicationContext, currentAccount,
                    old.dialogId)) {
                storyPushMessages.remove(i);
                storyPushMessagesDict.remove(old.dialogId);
            }
        }
        for (int i = pushMessages.size() - 1; i >= 0; i--) {
            MessageObject pending = pushMessages.get(i);
            if (pending != null &&
                org.telegram.ui.Components.NabdhChatLock.isLocked(
                        ApplicationLoader.applicationContext, currentAccount,
                        pending.getDialogId())) {
                pushMessages.remove(i);
                delayedPushMessages.remove(pending);
            }
        }
        if (!getUserConfig().isClientActivated()"""
code = once(code, head, updated, "old pending push cleanup")

# Locking an unread conversation must NOT call Telegram's
# removeNotificationsForDialog(): that method also marks its local unread count
# as read. Instead let the notification dispatcher re-render its own queue,
# filtering protected messages in showOrUpdateNotification above.
refresh_anchor = """    private void showOrUpdateNotification(boolean notifyAboutLast) {"""
refresh_method = """    public void nabdhRefreshLockedNotifications() {
        notificationsQueue.postRunnable(() -> {
            // Local notification UI refresh only: no read acknowledgements.
            showOrUpdateNotification(false);
        });
    }

    private void showOrUpdateNotification(boolean notifyAboutLast) {"""
code = once(code, refresh_anchor, refresh_method, "unread-preserving notification refresh")

# Extra notification stack must never recreate a protected child notification.
head = """        for (int a = 0; a < pushMessages.size(); a++) {
            MessageObject messageObject = pushMessages.get(a);
            long dialog_id = messageObject.getDialogId();
            long topicId = MessageObject.getTopicId"""
updated = """        for (int a = 0; a < pushMessages.size(); a++) {
            MessageObject messageObject = pushMessages.get(a);
            if (org.telegram.ui.Components.NabdhChatLock.isLocked(
                    ApplicationLoader.applicationContext, currentAccount,
                    messageObject.getDialogId())) continue;
            long dialog_id = messageObject.getDialogId();
            long topicId = MessageObject.getTopicId"""
code = once(code, head, updated, "wearable/child notifications")

# Defense in depth if Telegram adds a new caller for message formatting.
head = """    private String getStringForMessage(MessageObject messageObject, boolean shortMessage, boolean[] text, boolean[] preview) {
        if (AndroidUtilities.needShowPasscode()"""
updated = """    private String getStringForMessage(MessageObject messageObject, boolean shortMessage, boolean[] text, boolean[] preview) {
        if (messageObject != null &&
            org.telegram.ui.Components.NabdhChatLock.isLocked(
                    ApplicationLoader.applicationContext, currentAccount,
                    messageObject.getDialogId())) {
            if (preview != null) preview[0] = false;
            if (text != null) text[0] = false;
            return LocaleController.getString(R.string.YouHaveNewMessage);
        }
        if (AndroidUtilities.needShowPasscode()"""
code = once(code, head, updated, "notification formatter privacy")

# Popup Reply and direct reply must be excluded, even for existing messages.
head = """    public boolean hasMessagesToReply() {
        for (int a = 0; a < pushMessages.size(); a++) {
            MessageObject messageObject = pushMessages.get(a);
            long dialog_id = messageObject.getDialogId();"""
updated = """    public boolean hasMessagesToReply() {
        for (int a = 0; a < pushMessages.size(); a++) {
            MessageObject messageObject = pushMessages.get(a);
            if (org.telegram.ui.Components.NabdhChatLock.isLocked(
                    ApplicationLoader.applicationContext, currentAccount,
                    messageObject.getDialogId())) continue;
            long dialog_id = messageObject.getDialogId();"""
code = once(code, head, updated, "reply availability")
head = """    protected void forceShowPopupForReply() {
        notificationsQueue.postRunnable(() -> {
            ArrayList<MessageObject> popupArray = new ArrayList<>();
            for (int a = 0; a < pushMessages.size(); a++) {
                MessageObject messageObject = pushMessages.get(a);
                long dialog_id = messageObject.getDialogId();"""
updated = """    protected void forceShowPopupForReply() {
        notificationsQueue.postRunnable(() -> {
            ArrayList<MessageObject> popupArray = new ArrayList<>();
            for (int a = 0; a < pushMessages.size(); a++) {
                MessageObject messageObject = pushMessages.get(a);
                if (org.telegram.ui.Components.NabdhChatLock.isLocked(
                        ApplicationLoader.applicationContext, currentAccount,
                        messageObject.getDialogId())) continue;
                long dialog_id = messageObject.getDialogId();"""
code = once(code, head, updated, "popup reply")
notifications.write_text(code, encoding="utf-8")

chat = ui / "ChatActivity.java"
s = chat.read_text(encoding="utf-8")
# Use Telegram's shared FlagSecureReason reference counter, NOT raw
# Window.clearFlags: native Telegram PIN can independently require FLAG_SECURE.
# Keep this chat's reason attached until fragment destruction so system-recents
# snapshots remain protected, including after onPause.
head = """    public void onPause() {
        super.onPause();
        if (getParentActivity() != null &&
            org.telegram.ui.Components.NabdhChatLock.isLocked(
                    getParentActivity(), currentAccount, dialog_id)) {
            getParentActivity().getWindow().clearFlags(
                    android.view.WindowManager.LayoutParams.FLAG_SECURE);
        }
        scrolling = false;"""
s = once(s, head, """    public void onPause() {
        super.onPause();
        // Keep FLAG_SECURE through system-recents snapshots and backgrounding.
        scrolling = false;""", "secure recents lifecycle")
head = """        checkShowBlur(false);
        activityResumeTime = System.currentTimeMillis();"""
s = once(s, head, """        checkShowBlur(false);
        activityResumeTime = System.currentTimeMillis();""", "leave Telegram native secure screenshot state untouched")

# Replace raw FLAG_SECURE changes with a native reference-counted reason;
# this respects Telegram's own app passcode/screenshot policy.
direct_add = """            lockActivity.getWindow().addFlags(
                    android.view.WindowManager.LayoutParams.FLAG_SECURE);"""
s = once(s, direct_add,
         "            nabdhAttachChatLockSecureReason(lockActivity);",
         "reference-counted FLAG_SECURE owner")

method_anchor = """    private void createSearchHashtagViewsIfNeeded() {"""
method_block = """    private org.telegram.messenger.FlagSecureReason nabdhChatLockSecureReason;
    private android.view.Window nabdhChatLockSecureWindow;

    private void nabdhAttachChatLockSecureReason(android.app.Activity activity) {
        if (activity == null) return;
        android.view.Window currentWindow = activity.getWindow();
        if (nabdhChatLockSecureReason == null ||
                nabdhChatLockSecureWindow != currentWindow) {
            if (nabdhChatLockSecureReason != null) {
                nabdhChatLockSecureReason.detach();
            }
            nabdhChatLockSecureWindow = currentWindow;
            nabdhChatLockSecureReason = new org.telegram.messenger.FlagSecureReason(
                    currentWindow,
                    () -> org.telegram.ui.Components.NabdhChatLock.isLocked(
                            activity, currentAccount, dialog_id));
        }
        nabdhChatLockSecureReason.attach();
        nabdhChatLockSecureReason.invalidate();
    }

    private void createSearchHashtagViewsIfNeeded() {"""
s = once(s, method_anchor, method_block, "per-chat secure reason")

destroy_anchor = """    public void onFragmentDestroy() {
        super.onFragmentDestroy();"""
destroy_replacement = """    public void onFragmentDestroy() {
        if (nabdhChatLockSecureReason != null) {
            nabdhChatLockSecureReason.detach();
            nabdhChatLockSecureReason = null;
            nabdhChatLockSecureWindow = null;
        }
        super.onFragmentDestroy();"""
s = once(s, destroy_anchor, destroy_replacement, "native secure reason lifecycle")

# Prevent reads just because the protected fragment is constructed, resumed
# or cancelled before PIN authorization.
read_guard = """!org.telegram.ui.Components.NabdhChatLock.isLocked(
                org.telegram.messenger.ApplicationLoader.applicationContext,
                currentAccount, dialog_id) ||
            org.telegram.ui.Components.NabdhChatLock.isUnlocked(currentAccount, dialog_id)"""
calls = [
  "getMessagesController().markDialogAsReadNow(dialog_id, replyId);",
  "getMessagesController().markDialogAsRead(dialog_id, maxPositiveUnreadId, maxNegativeUnreadId, maxUnreadDate, false, threadId, counterDecrement, maxPositiveUnreadId == minMessageId[0] || maxNegativeUnreadId == minMessageId[0], scheduledRead);",
  "getMessagesController().markDialogAsRead(dialog_id, minMessageId[0], minMessageId[0], maxDate[0], false, threadId, 0, true, scheduledRead);",
  "getMessagesController().markDialogAsRead(dialog_id, messageObject.getId(), messageObject.getId(), messageObject.messageOwner.date, false, 0, 0, true, 0);",
]
for index, call in enumerate(calls):
    s = once(s, call, "if (" + read_guard + ") {\n            " + call + "\n        }", "read confirmation " + str(index+1))
# The final native read acknowledgement on pause runs BEFORE revocation.
# Returning from background must not silently reuse an old PIN authorization.
pause_ack = ("if (" + read_guard + ") {\\n            " +
             "getMessagesController().markDialogAsReadNow(dialog_id, replyId);" +
             "\\n        }")
s = once(s, pause_ack,
         pause_ack + "\\n        org.telegram.ui.Components.NabdhChatLock.revoke(currentAccount, dialog_id);",
         "revoke local PIN session only after native final read acknowledgement")
chat.write_text(s, encoding="utf-8")

# A PIN gate is not private if Telegram's main dialog list still previews
# the last message, thumbnail, sender or typing text for that protected chat.
# Replace only the rendered strings, never the real messages or read state.
cell = ui / "Cells/DialogCell.java"
cell_src = cell.read_text(encoding="utf-8")
cell_anchor = """            Layout.Alignment align = isForum && LocaleController.isRTL ? Layout.Alignment.ALIGN_OPPOSITE : Layout.Alignment.ALIGN_NORMAL;"""
cell_body = """            if (getContext() != null && currentDialogId != 0 && !isFolderCell() &&
                    org.telegram.ui.Components.NabdhChatLock.isLocked(
                            getContext().getApplicationContext(), currentAccount, currentDialogId)) {
                messageStringFinal = LocaleController.isRTL
                        ? "🔒 محادثة مقفلة" : "🔒 Locked chat";
                messageNameString = null;
                messageNameLayout = null;
                typingLayout = null;
                thumbsCount = 0;
            }
            Layout.Alignment align = isForum && LocaleController.isRTL ? Layout.Alignment.ALIGN_OPPOSITE : Layout.Alignment.ALIGN_NORMAL;"""
cell_src = once(cell_src, cell_anchor, cell_body, "chat-list message preview")
cell.write_text(cell_src, encoding="utf-8")

lock = ui / "Components/NabdhChatLock.java"
s = lock.read_text(encoding="utf-8")
head = """        save(context, info);
        UNLOCKED.remove(id(account, dialog));
    }"""
replace = """        save(context, info);
        UNLOCKED.remove(id(account, dialog));
        org.telegram.messenger.NotificationCenter.getInstance(account)
                .postNotificationName(org.telegram.messenger.NotificationCenter.dialogsNeedReload);
        // Rebuild Android notifications without Telegram's read-processing API.
        // Keeping the unread badge intact is part of the local-lock contract.
        org.telegram.messenger.NotificationsController.getInstance(account)
                .nabdhRefreshLockedNotifications();
    }"""
s = once(s, head, replace, "dismiss existing notifications on lock")
lock.write_text(s, encoding="utf-8")
print("PASS: locked notifications suppressed, popup/reply guarded, no read before PIN, recents retained")
