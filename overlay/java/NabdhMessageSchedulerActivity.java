package org.telegram.ui;

import android.app.Activity;
import android.app.DatePickerDialog;
import android.app.TimePickerDialog;
import android.os.Bundle;
import android.text.InputFilter;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.text.Editable;
import android.text.InputType;
import android.view.View;
import android.view.Gravity;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.telegram.messenger.ContactsController;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.SendMessagesHelper;
import org.telegram.messenger.UserConfig;
import org.telegram.messenger.LocaleController;
import org.telegram.tgnet.ConnectionsManager;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.NabdhToolUi;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Locale;

/**
 * Explicit user-triggered, server-side Telegram message scheduling.
 * No alarm, automated background job, contact upload or independent sender.
 * Uses Telegram's existing sendMessage(scheduleDate) path and error handling.
 */
public final class NabdhMessageSchedulerActivity extends Activity {
    private final Calendar schedule = Calendar.getInstance();
    private boolean dateChosen, timeChosen;
    private long selectedUserId;
    private String selectedName;
    private int account;
    private AutoCompleteTextView recipient;
    private ArrayAdapter<ContactChoice> adapter;
    private Button dateButton, timeButton;
    private EditText message;

    private static final class ContactChoice {
        final long id;
        final String name;
        ContactChoice(long id, String name) { this.id = id; this.name = name; }
        @Override public String toString() { return name; }
    }

    private String local(String en, String ar) {
        return LocaleController.isRTL ? ar : en;
    }

    private int dp(float n) {
        return (int) (getResources().getDisplayMetrics().density * n + .5f);
    }

    private TextView section(String title) {
        TextView view = new TextView(this);
        view.setText(title);
        view.setTextSize(13);
        view.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        view.setPadding(dp(4), dp(16), dp(4), dp(8));
        view.setGravity(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT);
        return view;
    }

    private Button button(String title) {
        Button view = new Button(this);
        view.setText(title);
        NabdhToolUi.styleButton(this, view);
        return view;
    }

    private void notifyUser(String text) {
        Toast.makeText(this, text, Toast.LENGTH_LONG).show();
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        account = UserConfig.selectedAccount;
        if (!UserConfig.getInstance(account).isClientActivated()) {
            notifyUser(local("Sign in to Telegram first", "سجّل الدخول إلى Telegram أولاً"));
            finish();
            return;
        }
        schedule.add(Calendar.MINUTE, 10);
        schedule.set(Calendar.SECOND, 0);
        schedule.set(Calendar.MILLISECOND, 0);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(16), dp(8), dp(16), dp(30));
        content.setLayoutDirection(LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        content.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));
        scroll.addView(content);
        NabdhToolUi.install(this, scroll, local("Message Scheduler", "جدولة الرسائل"));

        TextView note = section(local("Choose a Telegram contact, date, time and message. "
                + "Telegram stores the scheduled message after you confirm.",
                "اختر جهة اتصال في Telegram وتاريخًا ووقتًا ورسالة. "
                + "سيحفظ Telegram الرسالة المجدولة بعد التأكيد."));
        note.setTextSize(13);
        content.addView(note);

        content.addView(section(local("CONTACT", "جهة الاتصال")));
        recipient = new AutoCompleteTextView(this);
        recipient.setHint(local("Search Telegram contacts", "ابحث في جهات اتصال Telegram"));
        recipient.setSingleLine(true);
        recipient.setThreshold(1);
        NabdhToolUi.styleInput(this, recipient);
        recipient.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence value, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence value, int start, int before, int count) {
                // A manually edited name must never silently retain an old recipient.
                selectedUserId = 0;
                selectedName = null;
            }
            @Override public void afterTextChanged(Editable value) {}
        });
        content.addView(recipient, new LinearLayout.LayoutParams(-1, dp(54)));
        recipient.setOnItemClickListener((parent, row, index, id) -> {
            Object choice = parent.getItemAtPosition(index);
            if (choice instanceof ContactChoice) {
                selectedUserId = ((ContactChoice) choice).id;
                selectedName = ((ContactChoice) choice).name;
            }
        });

        Button refresh = button(local("Reload Telegram contacts", "تحديث جهات اتصال Telegram"));
        refresh.setOnClickListener(v -> reloadContacts());
        LinearLayout.LayoutParams refParams = new LinearLayout.LayoutParams(-1, -2);
        refParams.topMargin = dp(8);
        content.addView(refresh, refParams);
        reloadContacts();

        content.addView(section(local("SPECIFIC TIME", "موعد الإرسال")));
        LinearLayout when = new LinearLayout(this);
        when.setOrientation(LinearLayout.HORIZONTAL);
        when.setLayoutDirection(LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        dateButton = button(local("Select date", "حدد التاريخ"));
        timeButton = button(local("Select time", "حدد الوقت"));
        LinearLayout.LayoutParams left = new LinearLayout.LayoutParams(0, dp(54), 1f);
        left.setMarginEnd(dp(8));
        when.addView(dateButton, left);
        when.addView(timeButton, new LinearLayout.LayoutParams(0, dp(54), 1f));
        content.addView(when);
        dateButton.setOnClickListener(v -> {
            DatePickerDialog picker = new DatePickerDialog(this, (dialog, year, month, day) -> {
                schedule.set(Calendar.YEAR, year);
                schedule.set(Calendar.MONTH, month);
                schedule.set(Calendar.DAY_OF_MONTH, day);
                dateChosen = true;
                updateDateTime();
            }, schedule.get(Calendar.YEAR), schedule.get(Calendar.MONTH),
                    schedule.get(Calendar.DAY_OF_MONTH));
            picker.getDatePicker().setMinDate(System.currentTimeMillis() - 1000L);
            picker.show();
        });
        timeButton.setOnClickListener(v ->
                new TimePickerDialog(this, (dialog, hour, minute) -> {
                    schedule.set(Calendar.HOUR_OF_DAY, hour);
                    schedule.set(Calendar.MINUTE, minute);
                    timeChosen = true;
                    updateDateTime();
                }, schedule.get(Calendar.HOUR_OF_DAY), schedule.get(Calendar.MINUTE),
                        android.text.format.DateFormat.is24HourFormat(this)).show());

        content.addView(section(local("MESSAGE TO SEND", "نص الرسالة")));
        message = new EditText(this);
        message.setHint(local("Write the message", "اكتب الرسالة"));
        message.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE
                | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        message.setMinLines(3);
        message.setMaxLines(7);
        message.setGravity(Gravity.TOP |
                (LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT));
        message.setFilters(new InputFilter[]{new InputFilter.LengthFilter(4096)});
        NabdhToolUi.styleInput(this, message);
        content.addView(message, new LinearLayout.LayoutParams(-1, -2));

        Button submit = button(local("Review and schedule", "مراجعة وجدولة الرسالة"));
        LinearLayout.LayoutParams submitParams = new LinearLayout.LayoutParams(-1, dp(54));
        submitParams.topMargin = dp(18);
        content.addView(submit, submitParams);
        submit.setOnClickListener(v -> confirmSchedule());
    }

    private void reloadContacts() {
        ArrayList<ContactChoice> choices = new ArrayList<>();
        MessagesController controller = MessagesController.getInstance(account);
        ArrayList<TLRPC.TL_contact> contacts = ContactsController.getInstance(account).contacts;
        if (contacts != null) {
            for (TLRPC.TL_contact entry : new ArrayList<>(contacts)) {
                if (entry == null || entry.user_id <= 0
                        || entry.user_id == UserConfig.getInstance(account).getClientUserId()) continue;
                TLRPC.User user = controller.getUser(entry.user_id);
                if (user == null || user.deleted) continue;
                String first = user.first_name == null ? "" : user.first_name;
                String last = user.last_name == null ? "" : user.last_name;
                String name = (first + " " + last).trim();
                if (name.isEmpty() && user.username != null) name = "@" + user.username;
                if (name.isEmpty()) continue;
                // A stable @username or user ID disambiguates duplicate names.
                if (user.username != null && !user.username.isEmpty()
                        && !name.equals("@" + user.username)) {
                    name += " · @" + user.username;
                } else if (user.username == null || user.username.isEmpty()) {
                    name += " · " + user.id;
                }
                choices.add(new ContactChoice(user.id, name));
            }
        }
        choices.sort((a,b) -> a.name.compareToIgnoreCase(b.name));
        adapter = new ArrayAdapter<>(this, android.R.layout.simple_dropdown_item_1line, choices);
        recipient.setAdapter(adapter);
        selectedUserId = 0;
        selectedName = null;
        recipient.setText("");
        if (choices.isEmpty()) {
            notifyUser(local("No Telegram contacts cached. Open Contacts in Telegram then return.",
                    "لا توجد جهات اتصال محمّلة. افتح جهات الاتصال في Telegram ثم عُد."));
        }
    }

    private void updateDateTime() {
        if (dateChosen) dateButton.setText(String.format(Locale.US, "%04d-%02d-%02d",
                schedule.get(Calendar.YEAR), schedule.get(Calendar.MONTH) + 1,
                schedule.get(Calendar.DAY_OF_MONTH)));
        if (timeChosen) timeButton.setText(String.format(Locale.US, "%02d:%02d",
                schedule.get(Calendar.HOUR_OF_DAY), schedule.get(Calendar.MINUTE)));
    }

    private void confirmSchedule() {
        if (selectedUserId <= 0 || selectedName == null) {
            notifyUser(local("Select a contact from suggestions", "اختر جهة اتصال من نتائج البحث"));
            return;
        }
        if (!dateChosen || !timeChosen) {
            notifyUser(local("Select both date and time", "حدد التاريخ والوقت معًا"));
            return;
        }
        String text = message.getText().toString().trim();
        if (TextUtils.isEmpty(text)) {
            notifyUser(local("Enter a message to send", "اكتب نص الرسالة"));
            return;
        }
        long date = schedule.getTimeInMillis() / 1000L;
        long now = ConnectionsManager.getInstance(account).getCurrentTime();
        if (date <= now + 60 || date > now + 365L * 24L * 3600L
                || date > Integer.MAX_VALUE) {
            notifyUser(local("Choose a future date, at least 1 minute and at most 1 year ahead",
                    "اختر موعدًا بعد دقيقة على الأقل وخلال سنة من الآن"));
            return;
        }
        final long peer = selectedUserId;
        final int when = (int) date;
        final String target = selectedName;
        final String summary = target + "\n" + String.format(Locale.US,
                "%04d-%02d-%02d  %02d:%02d",
                schedule.get(Calendar.YEAR), schedule.get(Calendar.MONTH) + 1,
                schedule.get(Calendar.DAY_OF_MONTH), schedule.get(Calendar.HOUR_OF_DAY),
                schedule.get(Calendar.MINUTE)) + "\n\n" + text;
        new org.telegram.ui.ActionBar.AlertDialog.Builder(this)
                .setTitle(local("Confirm scheduled message", "تأكيد جدولة الرسالة"))
                .setMessage(summary)
                .setNegativeButton(local("Cancel", "إلغاء"), null)
                .setPositiveButton(local("Schedule", "جدولة"), (dialog, which) -> {
                    if (!UserConfig.getInstance(account).isClientActivated()
                            || MessagesController.getInstance(account).getUser(peer) == null) {
                        notifyUser(local("Contact unavailable; reload contacts",
                                "جهة الاتصال غير متاحة. حدّث القائمة"));
                        return;
                    }
                    long current = ConnectionsManager.getInstance(account).getCurrentTime();
                    if (when <= current + 60) {
                        notifyUser(local("Selected time has passed", "انتهى الموعد المحدد"));
                        return;
                    }
                    // One explicit confirmed action. Telegram queues the scheduled
                    // message on its servers; no autonomous Android sender exists.
                    SendMessagesHelper.SendMessageParams params =
                            SendMessagesHelper.SendMessageParams.of(text, peer);
                    params.scheduleDate = when;
                    params.notify = true;
                    SendMessagesHelper.getInstance(account).sendMessage(params);
                    notifyUser(local("Scheduled message submitted to Telegram. "
                                    + "Check the chat's scheduled messages for confirmation.",
                            "أُرسِل طلب الجدولة إلى Telegram. تحقق من الرسائل المجدولة "
                                    + "داخل المحادثة للتأكد من قبولها."));
                    finish();
                })
                .show();
    }
}
