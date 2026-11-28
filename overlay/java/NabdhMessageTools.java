package org.telegram.ui.Components;

import android.content.Context;
import android.os.Bundle;
import android.text.InputFilter;
import android.widget.EditText;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;

import org.telegram.messenger.DialogObject;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.UserObject;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ChatActivity;
import org.telegram.ui.NabdhSwipeReminder;

/** Local productivity actions for messages and the existing unread dialog cache. */
public final class NabdhMessageTools {
    private static final int MAX_DIGEST_DIALOGS = 12;
    private static final int MAX_SCAN = 240;

    private NabdhMessageTools() {}

    public static boolean isArabic() {
        java.util.Locale locale = LocaleController.getInstance().getCurrentLocale();
        return locale != null && "ar".equals(locale.getLanguage());
    }

    private static String label(String arabic, String english) {
        return isArabic() ? arabic : english;
    }

    static boolean canAccess(BaseFragment fragment, long dialogId) {
        Context context = fragment.getParentActivity();
        return context != null && dialogId != 0 && !DialogObject.isEncryptedDialog(dialogId)
                && !fragment.getMessagesController().isPeerNoForwards(dialogId)
                && !NabdhChatLock.isLocked(context, fragment.getCurrentAccount(), dialogId);
    }

    public static boolean canUse(BaseFragment fragment, MessageObject message) {
        return message != null && message.messageOwner != null && message.getId() > 0
                && !message.isSponsored() && !message.isEphemeral() && !message.isExpiredStory()
                && !message.messageOwner.noforwards && message.messageOwner.ttl_period == 0
                && message.type != MessageObject.TYPE_PAID_MEDIA
                && !(message.messageOwner instanceof TLRPC.TL_messageService)
                && canAccess(fragment, message.getDialogId());
    }

    public static void show(ChatActivity fragment, MessageObject source) {
        if (!canUse(fragment, source)) return;
        Context context = fragment.getParentActivity();
        int account = fragment.getCurrentAccount();
        long ownerId = fragment.getUserConfig().getClientUserId();
        if (ownerId == 0) return;
        long dialogId = source.getDialogId();
        new AlertDialog.Builder(context)
                .setTitle(label("أدوات الرسالة", "Message tools"))
                .setItems(new String[] {
                        label("استخراج النقاط المهمة", "Extract focus signals"),
                        label("حفظ كملاحظة مرتبطة", "Save linked note"),
                        label("حفظ كمهمة مرتبطة", "Save linked task"),
                        label("تذكير بالرسالة بعد ساعة", "Remind about this message in an hour"),
                        label("فحص مؤشرات الروابط والاحتيال", "Check link and scam signals")
                }, (dialog, which) -> {
                    if (fragment.getCurrentAccount() != account ||
                            fragment.getUserConfig().getClientUserId() != ownerId || !canUse(fragment, source)) return;
                    if (which == 0) {
                        String text = NabdhV1Engine.focus(excerpt(source, 1600), isArabic());
                        if (source.type == MessageObject.TYPE_FILE) {
                            text += "\n\n" + label("الملف المرفق: ", "Attached file: ")
                                    + NabdhV1Engine.bounded(source.getFileName());
                        }
                        new AlertDialog.Builder(context)
                                .setTitle("Focus Lens")
                                .setMessage(text)
                                .setPositiveButton(label("العودة إلى الرسالة", "Return to message"),
                                        (d, ignored) -> {
                                            if (fragment.getCurrentAccount() == account
                                                    && fragment.getUserConfig().getClientUserId() == ownerId
                                                    && canUse(fragment, source)) {
                                                fragment.scrollToMessageId(
                                                        source.getId(), 0, true, 0, true, 0);
                                            }
                                        }).show();
                    } else if (which == 3) {
                        remind(context, account, ownerId, dialogId, source.getId());
                    } else if (which == 4) {
                        String text = excerpt(source, 1600);
                        new AlertDialog.Builder(context)
                                .setTitle("NabdhShield")
                                .setMessage(NabdhV1Engine.shield(text, isArabic()) + "\n\n"
                                        + NabdhV1Engine.scam(text, isArabic()))
                                .setPositiveButton(label("إغلاق", "Close"), null)
                                .show();
                    } else {
                        composeLinkedNote(fragment, context, source, account, ownerId, which == 2);
                    }
                })
                .setNegativeButton(label("إغلاق", "Close"), null)
                .show();
    }

    private static void composeLinkedNote(ChatActivity fragment, Context context,
                                          MessageObject source, int account, long ownerId, boolean task) {
        EditText input = new EditText(context);
        input.setHint(task ? label("اكتب المهمة", "Enter a task") : label("اكتب ملاحظتك", "Enter a note"));
        input.setFilters(new InputFilter[] {new InputFilter.LengthFilter(NabdhWorkspace.MAX_ENTRY)});
        input.setTextDirection(android.view.View.TEXT_DIRECTION_FIRST_STRONG);
        new AlertDialog.Builder(context)
                .setTitle(task ? label("مهمة مرتبطة", "Linked task") : label("ملاحظة مرتبطة", "Linked note"))
                .setView(input)
                .setNegativeButton(label("إلغاء", "Cancel"), null)
                .setPositiveButton(label("حفظ", "Save"), (dialog, ignored) -> {
                    if (fragment.getCurrentAccount() != account
                            || fragment.getUserConfig().getClientUserId() != ownerId || !canUse(fragment, source)) return;
                    String text = NabdhV1Engine.bounded(input.getText());
                    if (text.isEmpty()) return;
                    try {
                        NabdhWorkspace.save(context, text, "linked-note",
                                account, ownerId, source.getDialogId(), source.getId(), task);
                        Toast.makeText(context, label("حُفظ العنصر مشفراً على الجهاز.",
                                "Saved encrypted on this device."), Toast.LENGTH_SHORT).show();
                    } catch (Exception e) {
                        Toast.makeText(context, label("تعذّر حفظ العنصر.", "Could not save the item."),
                                Toast.LENGTH_SHORT).show();
                    }
                }).show();
    }

    private static String excerpt(MessageObject message, int limit) {
        String value = NabdhV1Engine.bounded(message.messageOwner.message);
        if (value.isEmpty()) value = NabdhV1Engine.bounded(message.messageText);
        if (value.isEmpty()) return label("رسالة وسائط", "Media message");
        if (value.length() <= limit) return value;
        int end = Character.isHighSurrogate(value.charAt(limit - 1)) ? limit - 1 : limit;
        return value.substring(0, end);
    }

    private static void remind(Context context, int account, long ownerId, long dialogId, int messageId) {
        long now = System.currentTimeMillis();
        if (NabdhSwipeReminder.getScheduledTime(context, account, dialogId) > now) {
            Toast.makeText(context, label("يوجد تذكير لهذه المحادثة.",
                    "This chat already has a reminder."), Toast.LENGTH_SHORT).show();
            return;
        }
        if (!androidx.core.app.NotificationManagerCompat.from(context).areNotificationsEnabled()) {
            Toast.makeText(context, label("فعّل الإشعارات أولاً لتلقي التذكير.",
                    "Enable notifications to receive reminders."), Toast.LENGTH_SHORT).show();
            return;
        }
        boolean scheduled = NabdhSwipeReminder.scheduleMessage(
                context, account, ownerId, dialogId, messageId, now + 3600000L);
        Toast.makeText(context, scheduled
                ? label("ضُبط تذكير محلي خلال نحو ساعة.", "Local reminder set for about one hour.")
                : label("تعذّر ضبط التذكير.", "Could not schedule the reminder."), Toast.LENGTH_SHORT).show();
    }

    static void openMessage(BaseFragment fragment, long dialogId, int messageId) {
        if (!canAccess(fragment, dialogId)) return;
        Bundle args = new Bundle();
        args.putLong(dialogId > 0 ? "user_id" : "chat_id", Math.abs(dialogId));
        if (messageId > 0) args.putInt("message_id", messageId);
        if (fragment.getMessagesController().checkCanOpenChat(args, fragment)) {
            ChatActivity chat = new ChatActivity(args);
            chat.setCurrentAccount(fragment.getCurrentAccount());
            fragment.presentFragment(chat);
        }
    }

    public static void showUnreadDigest(BaseFragment fragment) {
        Context context = fragment.getParentActivity();
        if (context == null) return;
        int account = fragment.getCurrentAccount();
        long ownerId = fragment.getUserConfig().getClientUserId();
        if (ownerId == 0) return;
        MessagesController controller = fragment.getMessagesController();
        List<String> summaries = new ArrayList<>();
        List<TLRPC.Dialog> sources = new ArrayList<>();
        List<Integer> targets = new ArrayList<>();
        List<TLRPC.Dialog> dialogs = controller.getAllDialogs();
        for (int i = 0; i < Math.min(dialogs.size(), MAX_SCAN)
                && summaries.size() < MAX_DIGEST_DIALOGS; i++) {
            TLRPC.Dialog dialog = dialogs.get(i);
            if (!(dialog instanceof TLRPC.TL_dialog) || dialog.unread_count <= 0
                    || !canAccess(fragment, dialog.id)) continue;
            String title;
            if (dialog.id > 0) {
                TLRPC.User user = controller.getUser(dialog.id);
                if (user == null) continue;
                title = UserObject.getUserName(user);
            } else {
                TLRPC.Chat chat = controller.getChat(-dialog.id);
                if (chat == null) continue;
                title = chat.title;
            }
            String summary = title + " · " + dialog.unread_count + label(" غير مقروءة", " unread");
            int target = 0;
            List<MessageObject> cached = controller.dialogMessage.get(dialog.id);
            if (cached != null) {
                for (MessageObject message : cached) {
                    if (canUse(fragment, message) && !message.isOut() && message.isUnread()
                            && message.getDialogId() == dialog.id && message.getId() == dialog.top_message) {
                        summary += "\n" + excerpt(message, 150);
                        target = dialog.id > 0 || !controller.isForum(dialog.id) ? message.getId() : 0;
                        break;
                    }
                }
            }
            summaries.add(summary);
            sources.add(dialog);
            targets.add(target);
        }
        AlertDialog.Builder builder = new AlertDialog.Builder(context)
                .setTitle(label("ملخص غير المقروء محلياً", "Local unread digest"))
                .setNegativeButton(label("إغلاق", "Close"), null);
        if (summaries.isEmpty()) {
            builder.setMessage(label("لا توجد محادثات غير مقروءة متاحة في ذاكرة الحساب.",
                    "No eligible unread chats are available in this account's cache."));
        } else {
            builder.setMessage(label("يعرض حتى 12 محادثة وآخر رسالة غير مقروءة متاحة محلياً.",
                    "Shows up to 12 chats and the latest unread message available locally."));
            builder.setItems(summaries.toArray(new String[0]), (dialog, which) -> {
                if (fragment.getCurrentAccount() == account
                        && fragment.getUserConfig().getClientUserId() == ownerId) {
                    openMessage(fragment, sources.get(which).id, targets.get(which));
                }
            });
        }
        builder.show();
    }
}
