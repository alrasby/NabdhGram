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
import android.widget.CheckBox;
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
import java.util.LinkedHashMap;

/**
 * Explicit user-triggered, server-side Telegram message scheduling.
 * No alarm, automated background job, contact upload or independent sender.
 * Uses Telegram's existing sendMessage(scheduleDate) path and error handling.
 */
public final class NabdhMessageSchedulerActivity extends Activity {
    private final Calendar schedule = Calendar.getInstance();
    private boolean dateChosen, timeChosen;
    private static final int MAX_RECIPIENTS = 20;
    private final LinkedHashMap<Long, ContactChoice> selected = new LinkedHashMap<>();
    private ArrayList<ContactChoice> contacts = new ArrayList<>();
    private int account;
    private TextView recipient;
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
        // Touch opens a native Telegram multi-selection sheet, never a dark
        // system AutoComplete popup or the keyboard.
        recipient = new TextView(this);
        recipient.setTextSize(15);
        recipient.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        recipient.setGravity(Gravity.CENTER_VERTICAL |
                (LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT));
        recipient.setPadding(dp(16), dp(8), dp(16), dp(8));
        recipient.setBackground(
                org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        recipient.setMinHeight(dp(54));
        recipient.setClickable(true);
        recipient.setFocusable(true);
        recipient.setContentDescription(local("Choose Telegram contacts",
                "اختر جهات اتصال Telegram"));
        recipient.setOnClickListener(v -> chooseRecipients());
        content.addView(recipient, new LinearLayout.LayoutParams(-1, dp(58)));

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
        contacts = choices;
        selected.clear();
        updateRecipientLabel();
        if (choices.isEmpty()) {
            notifyUser(local("No Telegram contacts cached. Open Contacts in Telegram then return.",
                    "لا توجد جهات اتصال محمّلة. افتح جهات الاتصال في Telegram ثم عُد."));
        }
    }

    private void updateRecipientLabel() {
        if (recipient == null) return;
        if (selected.isEmpty()) {
            recipient.setText(local("Tap to select one or more Telegram contacts  ›",
                    "اضغط لاختيار جهة اتصال واحدة أو أكثر  ‹"));
            return;
        }
        StringBuilder names = new StringBuilder();
        int shown = 0;
        for (ContactChoice choice : selected.values()) {
            if (shown++ == 3) break;
            if (names.length() > 0) names.append("، ");
            names.append(choice.name);
        }
        if (selected.size() > 3) names.append(" …");
        recipient.setText(local("Selected: ", "المحددون: ") + selected.size() + " · " + names);
    }

    private void renderChoices(LinearLayout list,
                               LinkedHashMap<Long, ContactChoice> pending,
                               String filter, TextView countLabel) {
        list.removeAllViews();
        String query = filter == null ? "" : filter.trim().toLowerCase(Locale.ROOT);
        int visible = 0;
        for (ContactChoice choice : contacts) {
            if (!query.isEmpty() &&
                    !choice.name.toLowerCase(Locale.ROOT).contains(query)) continue;
            visible++;
            CheckBox box = new CheckBox(this);
            box.setText(choice.name);
            box.setTextSize(14);
            box.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            box.setGravity(Gravity.CENTER_VERTICAL |
                    (LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT));
            box.setPadding(dp(14), dp(6), dp(14), dp(6));
            box.setLayoutDirection(LocaleController.isRTL
                    ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
            box.setChecked(pending.containsKey(choice.id));
            NabdhToolUi.styleToggle(this, box);
            box.setBackground(
                    org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
            box.setOnCheckedChangeListener((button, checked) -> {
                if (checked && pending.size() >= MAX_RECIPIENTS) {
                    button.setChecked(false);
                    notifyUser(local("Choose up to 20 contacts per schedule",
                            "يمكن اختيار 20 جهة اتصال كحد أقصى لكل جدولة"));
                    return;
                }
                if (checked) pending.put(choice.id, choice);
                else pending.remove(choice.id);
                countLabel.setText(local("Selected: ", "تم اختيار: ")
                        + pending.size() + " / " + MAX_RECIPIENTS);
            });
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, dp(55));
            lp.bottomMargin = dp(3);
            list.addView(box, lp);
        }
        if (visible == 0) {
            TextView empty = section(local("No matching Telegram contacts",
                    "لا توجد جهات اتصال مطابقة"));
            list.addView(empty);
        }
        countLabel.setText(local("Selected: ", "تم اختيار: ")
                + pending.size() + " / " + MAX_RECIPIENTS);
    }

    private void chooseRecipients() {
        if (contacts.isEmpty()) {
            notifyUser(local("Open Telegram Contacts, then reload this list.",
                    "افتح جهات الاتصال في Telegram، ثم حدّث هذه القائمة."));
            return;
        }
        final LinkedHashMap<Long, ContactChoice> pending = new LinkedHashMap<>(selected);
        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        sheet.setPadding(dp(12), dp(8), dp(12), dp(6));
        sheet.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));
        sheet.setLayoutDirection(LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        sheet.setFocusableInTouchMode(true);
        sheet.requestFocus();

        EditText query = new EditText(this);
        query.setSingleLine(true);
        query.setHint(local("Search Telegram contacts", "ابحث في جهات اتصال Telegram"));
        NabdhToolUi.styleInput(this, query);
        sheet.addView(query, new LinearLayout.LayoutParams(-1, dp(52)));

        TextView count = section("");
        sheet.addView(count);
        ScrollView scroll = new ScrollView(this);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(list);
        sheet.addView(scroll, new LinearLayout.LayoutParams(-1, dp(340)));
        renderChoices(list, pending, "", count);
        query.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence v, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence v, int start, int before, int count) {
                renderChoices(list, pending, v.toString(), count);
            }
            @Override public void afterTextChanged(Editable v) {}
        });
        new org.telegram.ui.ActionBar.AlertDialog.Builder(this)
                .setTitle(local("Telegram recipients", "المستلمون من Telegram"))
                .setView(sheet)
                .setNegativeButton(local("Cancel", "إلغاء"), null)
                .setPositiveButton(local("Use selected", "اعتماد الاختيار"), (dialog, which) -> {
                    selected.clear();
                    selected.putAll(pending);
                    updateRecipientLabel();
                }).show();
    }

    private void updateDateTime() {
        if (dateChosen) dateButton.setText(String.format(Locale.US, "%04d-%02d-%02d",
                schedule.get(Calendar.YEAR), schedule.get(Calendar.MONTH) + 1,
                schedule.get(Calendar.DAY_OF_MONTH)));
        if (timeChosen) timeButton.setText(String.format(Locale.US, "%02d:%02d",
                schedule.get(Calendar.HOUR_OF_DAY), schedule.get(Calendar.MINUTE)));
    }

    private void confirmSchedule() {
        if (selected.isEmpty()) {
            notifyUser(local("Select at least one Telegram contact", "اختر جهة اتصال واحدة على الأقل"));
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
        final int when = (int) date;
        final ArrayList<ContactChoice> recipients = new ArrayList<>(selected.values());
        StringBuilder names = new StringBuilder();
        for (ContactChoice choice : recipients) {
            if (names.length() > 0) names.append("\n");
            names.append("• ").append(choice.name);
        }
        final String summary = local("Recipients: ", "المستلمون: ")
                + recipients.size() + "\n" + names + "\n"
                + String.format(Locale.US, "%04d-%02d-%02d  %02d:%02d",
                schedule.get(Calendar.YEAR), schedule.get(Calendar.MONTH) + 1,
                schedule.get(Calendar.DAY_OF_MONTH), schedule.get(Calendar.HOUR_OF_DAY),
                schedule.get(Calendar.MINUTE)) + "\n\n" + text;
        new org.telegram.ui.ActionBar.AlertDialog.Builder(this)
                .setTitle(local("Confirm scheduled message", "تأكيد جدولة الرسالة"))
                .setMessage(summary)
                .setNegativeButton(local("Cancel", "إلغاء"), null)
                .setPositiveButton(local("Schedule", "جدولة"), (dialog, which) -> {
                    if (!UserConfig.getInstance(account).isClientActivated()) {
                        notifyUser(local("Telegram session is unavailable",
                                "جلسة Telegram غير متاحة"));
                        return;
                    }
                    MessagesController controller = MessagesController.getInstance(account);
                    // Validate all recipients before sending any request.
                    for (ContactChoice choice : recipients) {
                        TLRPC.User user = controller.getUser(choice.id);
                        if (user == null || user.deleted) {
                            notifyUser(local("A contact is unavailable; reload contacts",
                                    "إحدى جهات الاتصال غير متاحة؛ حدّث القائمة"));
                            return;
                        }
                    }
                    long current = ConnectionsManager.getInstance(account).getCurrentTime();
                    if (when <= current + 60) {
                        notifyUser(local("Selected time has passed", "انتهى الموعد المحدد"));
                        return;
                    }
                    for (ContactChoice choice : recipients) {
                        long peer = choice.id;
                        SendMessagesHelper.SendMessageParams params =
                                SendMessagesHelper.SendMessageParams.of(text, peer);
                        params.scheduleDate = when;
                        params.notify = true;
                        SendMessagesHelper.getInstance(account).sendMessage(params);
                    }
                    notifyUser(local("Scheduled messages submitted to Telegram. "
                                    + "Check the chat's scheduled messages for confirmation.",
                            "أُرسلت طلبات الجدولة إلى Telegram. تحقق من الرسائل المجدولة "
                                    + "داخل المحادثة للتأكد من قبولها."));
                    finish();
                })
                .show();
    }
}
