package org.telegram.ui;

import android.app.Activity;
import android.os.Bundle;
import android.text.InputType;
import android.graphics.Color;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.UserConfig;
import org.telegram.messenger.DialogObject;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.Components.NabdhChatLock;

/** Explicit PIN setup and per-conversation opt-in. No chat messages read. */
public final class NabdhChatLockActivity extends Activity {
    private LinearLayout screen;
    private int account;
    private boolean authorized;

    private String local(String en, String ar) {
        return org.telegram.messenger.LocaleController.isRTL ? ar : en;
    }

    @Override protected void onStop() {
        // Authorization must never outlive the foreground PIN management UI.
        authorized = false;
        super.onStop();
    }

    @Override protected void onRestart() {
        super.onRestart();
        if (screen != null) render();
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        account = UserConfig.selectedAccount;
        setTitle(local("Chat locks", "قفل المحادثات"));
        ScrollView scroll = new ScrollView(this);
        screen = new LinearLayout(this);
        screen.setPadding(24, 24, 24, 24);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhite));
        screen.setLayoutDirection(org.telegram.messenger.LocaleController.isRTL
                ? android.view.View.LAYOUT_DIRECTION_RTL
                : android.view.View.LAYOUT_DIRECTION_LTR);
        scroll.addView(screen);
        setContentView(scroll);
        render();
    }

    private TextView line(String text) {
        TextView value = new TextView(this);
        value.setText(text);
        value.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        value.setTextSize(16);
        value.setPadding(10, 12, 10, 12);
        screen.addView(value);
        return value;
    }
    private EditText secretField(String hint) {
        EditText field = new EditText(this);
        field.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        field.setHintTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        field.setHint(hint);
        field.setSingleLine(true);
        field.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        screen.addView(field);
        return field;
    }
    private void action(String text, Runnable callback) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        button.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        button.setBackground(
                org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        button.setOnClickListener(v -> callback.run());
        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(-1, -2);
        params.bottomMargin = (int) (8 * getResources().getDisplayMetrics().density);
        screen.addView(button, params);
    }

    private void render() {
        screen.removeAllViews();
        if (!NabdhChatLock.configured(this)) {
            line(local("Set a 6–12 digit local PIN. This does not change Telegram login or passcode.",
                    "أنشئ رمز PIN محليًا من 6 إلى 12 رقمًا. لا يؤثر على رمز دخول Telegram."));
            EditText pin = secretField(local("New PIN", "رمز PIN الجديد"));
            EditText confirm = secretField(local("Confirm PIN", "تأكيد رمز PIN"));
            action(local("Set chat-lock PIN", "تفعيل رمز قفل المحادثات"), () -> {
                String first = pin.getText().toString();
                String again = confirm.getText().toString();
                pin.getText().clear();
                confirm.getText().clear();
                if (!first.equals(again)) { notice(local("PINs do not match", "رمزا PIN غير متطابقين")); return; }
                try {
                    NabdhChatLock.setPin(this, first);
                    authorized = true;
                    render();
                } catch (Exception failure) {
                    notice(local("PIN not accepted: use 6–12 digits",
                            "تعذر اعتماد الرمز، استخدم 6 إلى 12 رقمًا"));
                }
            });
            return;
        }
        if (!authorized) {
            line(local("Enter your local PIN before editing protected conversations.",
                    "أدخل رمز PIN المحلي لتعديل المحادثات المحمية."));
            EditText pin = secretField("PIN");
            action(local("Manage locked chats", "إدارة المحادثات المقفلة"), () -> {
                String entered = pin.getText().toString();
                pin.getText().clear();
                if (NabdhChatLock.verify(this, entered)) {
                    authorized = true;
                    render();
                } else notice(local("Incorrect PIN or temporarily blocked",
                            "رمز PIN غير صحيح أو المحاولات محظورة مؤقتًا"));
            });
            return;
        }
        line(org.telegram.messenger.LocaleController.getString(
                org.telegram.messenger.R.string.NabdhChatLockNotice));
        MessagesController controller = MessagesController.getInstance(account);
        if (controller == null || controller.dialogs_dict == null) {
            line(local("Chat list not loaded. Return to the main chat list and try again.",
                        "لم تُحمّل قائمة المحادثات. عد للرئيسية ثم حاول مجددًا."));
            return;
        }
        int shown = 0;
        for (int i = 0; i < controller.dialogs_dict.size() && shown < 200; i++) {
            TLRPC.Dialog dialog = controller.dialogs_dict.valueAt(i);
            if (dialog == null || dialog.id == 0 ||
                    DialogObject.isEncryptedDialog(dialog.id)) continue;
            String title = null;
            if (dialog.id < 0) {
                TLRPC.Chat chat = controller.getChat(-dialog.id);
                if (chat != null) title = chat.title;
            } else {
                TLRPC.User person = controller.getUser(dialog.id);
                if (person != null) {
                    String first = person.first_name == null ? "" : person.first_name;
                    String last = person.last_name == null ? "" : person.last_name;
                    title = (first + " " + last).trim();
                }
            }
            if (title == null || title.isEmpty()) continue;
            shown++;
            final long dialogId = dialog.id;
            boolean locked = NabdhChatLock.isLocked(this, account, dialogId);
            action((locked ? "🔒 " : "○ ") + title, () -> {
                try {
                    NabdhChatLock.setLocked(this, account, dialogId, !locked);
                    render();
                } catch (Exception failure) {
                    notice(local("Could not update lock", "تعذر تحديث القفل"));
                }
            });
        }
        if (shown == 0) line(local("No regular conversations loaded.", "لم تُحمّل محادثات عادية بعد."));
    }
    private void notice(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }
}
