package org.telegram.ui;

import android.Manifest;
import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import java.util.Map;

/**
 * Local-only, per-account chat reminder. No Telegram message is ever sent.
 * Inexact while-idle alarms avoid requiring SCHEDULE_EXACT_ALARM privileges.
 */
public final class NabdhSwipeReminder extends BroadcastReceiver {
    private static final String PREFS = "nabdh_smart_swipe_reminders";
    private static final String FIRE = "org.telegram.ui.NABDHSWIPE_REMIND";
    private static final String CHANNEL = "nabdh_smart_swipe_reminders";

    private static String key(int account, long dialogId) {
        return account + ":" + dialogId;
    }

    public static long getScheduledTime(Context context, int account, long dialogId) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getLong(key(account, dialogId), 0L);
    }

    public static void schedule(Context context, int account, long dialogId, long when) {
        if (dialogId == 0L || account < 0 || when <= System.currentTimeMillis()) {
            return;
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putLong(key(account, dialogId), when).apply();
        arm(context, account, dialogId, when);
    }

    public static void cancel(Context context, int account, long dialogId) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .remove(key(account, dialogId)).apply();
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        PendingIntent pending = alarmIntent(context, account, dialogId, PendingIntent.FLAG_NO_CREATE);
        if (manager != null && pending != null) {
            manager.cancel(pending);
            pending.cancel();
        }
    }

    private static Uri identity(int account, long dialogId) {
        return Uri.parse("nabdhgram://swipe-reminder/" + account + "/" + dialogId);
    }

    private static PendingIntent alarmIntent(Context context, int account, long dialogId, int flag) {
        Intent intent = new Intent(context, NabdhSwipeReminder.class).setAction(FIRE)
                .setData(identity(account, dialogId))
                .putExtra("account", account).putExtra("dialogId", dialogId);
        return PendingIntent.getBroadcast(context, 0, intent,
                flag | PendingIntent.FLAG_IMMUTABLE);
    }

    private static void arm(Context context, int account, long dialogId, long when) {
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) {
            return;
        }
        PendingIntent alarm = alarmIntent(context, account, dialogId, PendingIntent.FLAG_UPDATE_CURRENT);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, when, alarm);
        } else {
            manager.set(AlarmManager.RTC_WAKEUP, when, alarm);
        }
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) {
            return;
        }
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            for (Map.Entry<String, ?> entry : prefs.getAll().entrySet()) {
                try {
                    String[] parts = entry.getKey().split(":");
                    if (parts.length != 2 || !(entry.getValue() instanceof Long)) {
                        continue;
                    }
                    int account = Integer.parseInt(parts[0]);
                    long dialogId = Long.parseLong(parts[1]);
                    long when = (Long) entry.getValue();
                    arm(context, account, dialogId, Math.max(System.currentTimeMillis() + 2000L, when));
                } catch (NumberFormatException ignored) {
                    // Ignore legacy or malformed preferences without crashing boot.
                }
            }
            return;
        }
        if (!FIRE.equals(intent.getAction())) {
            return;
        }
        int account = intent.getIntExtra("account", -1);
        long dialogId = intent.getLongExtra("dialogId", 0L);
        if (account < 0 || dialogId == 0L) {
            return;
        }
        long when = getScheduledTime(context, account, dialogId);
        if (when == 0L) {
            return; // Reminder cancelled after alarm was queued.
        }
        if (when > System.currentTimeMillis() + 1500L) {
            arm(context, account, dialogId, when); // Older replacement alarm.
            return;
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .remove(key(account, dialogId)).apply();
        if (Build.VERSION.SDK_INT >= 33
                && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
            return; // Android blocks notifications; never bypass user settings.
        }
        NotificationManager manager = (NotificationManager)
                context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) {
            return;
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(CHANNEL,
                    "NabdhGram chat reminders", NotificationManager.IMPORTANCE_DEFAULT);
            manager.createNotificationChannel(channel);
        }
        Intent open = new Intent(context, LaunchActivity.class)
                .setAction("com.tmessages.openchat")
                .setData(identity(account, dialogId))
                .putExtra("currentAccount", account)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        if (org.telegram.messenger.DialogObject.isEncryptedDialog(dialogId)) {
            open.putExtra("encId",
                    org.telegram.messenger.DialogObject.getEncryptedChatId(dialogId));
        } else if (dialogId > 0) {
            open.putExtra("userId", dialogId);
        } else {
            open.putExtra("chatId", -dialogId);
        }
        PendingIntent openPending = PendingIntent.getActivity(context, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        boolean arabic = java.util.Locale.getDefault().getLanguage().equals("ar");
        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(context, CHANNEL) : new Notification.Builder(context);
        Notification notification = builder
                .setSmallIcon(android.R.drawable.ic_popup_reminder)
                .setContentTitle(arabic ? "تذكير بمحادثة" : "Chat reminder")
                .setContentText(arabic ? "اضغط للعودة إلى المحادثة" : "Tap to return to the conversation")
                .setContentIntent(openPending).setAutoCancel(true)
                .setCategory(Notification.CATEGORY_REMINDER).build();
        manager.notify((account * 31 + (int) (dialogId ^ (dialogId >>> 32))) & 0x7fffffff, notification);
    }
}
