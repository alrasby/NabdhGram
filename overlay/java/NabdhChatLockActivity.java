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

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        account = UserConfig.selectedAccount;
        setTitle("Chat locks");
        ScrollView scroll = new ScrollView(this);
        screen = new LinearLayout(this);
        screen.setPadding(24, 24, 24, 24);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setBackgroundColor(Color.rgb(18, 29, 33));
        scroll.addView(screen);
        setContentView(scroll);
        render();
    }

    private TextView line(String text) {
        TextView value = new TextView(this);
        value.setText(text);
        value.setTextColor(Color.WHITE);
        value.setTextSize(16);
        value.setPadding(10, 12, 10, 12);
        screen.addView(value);
        return value;
    }
    private EditText secretField(String hint) {
        EditText field = new EditText(this);
        field.setTextColor(Color.WHITE);
        field.setHintTextColor(Color.LTGRAY);
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
        button.setOnClickListener(v -> callback.run());
        screen.addView(button);
    }

    private void render() {
        screen.removeAllViews();
        if (!NabdhChatLock.configured(this)) {
            line("Set a 6–12 digit local PIN. This does not change Telegram login or passcode.");
            EditText pin = secretField("New PIN");
            EditText confirm = secretField("Confirm PIN");
            action("Set chat-lock PIN", () -> {
                String first = pin.getText().toString();
                String again = confirm.getText().toString();
                pin.getText().clear();
                confirm.getText().clear();
                if (!first.equals(again)) { notice("PINs do not match"); return; }
                try {
                    NabdhChatLock.setPin(this, first);
                    authorized = true;
                    render();
                } catch (Exception failure) {
                    notice("PIN not accepted: use 6–12 digits");
                }
            });
            return;
        }
        if (!authorized) {
            line("Enter your local PIN before editing protected conversations.");
            EditText pin = secretField("PIN");
            action("Manage locked chats", () -> {
                String entered = pin.getText().toString();
                pin.getText().clear();
                if (NabdhChatLock.verify(this, entered)) {
                    authorized = true;
                    render();
                } else notice("Incorrect PIN or temporarily blocked");
            });
            return;
        }
        line("Select conversations to lock. Opening a protected chat requires your PIN; the message contents are not copied. Notification previews must be managed separately in Telegram settings.");
        MessagesController controller = MessagesController.getInstance(account);
        if (controller == null || controller.dialogs_dict == null) {
            line("Chat list not loaded. Return to the main chat list and try again.");
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
                    notice("Could not update lock");
                }
            });
        }
        if (shown == 0) line("No regular conversations loaded.");
    }
    private void notice(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }
}
