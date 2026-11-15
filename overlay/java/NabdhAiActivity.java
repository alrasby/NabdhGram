package org.telegram.ui;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.RemoteException;
import android.text.InputType;
import android.graphics.Color;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.telegram.ui.Components.NabdhAiGemmaProvider;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Explicit, no-history on-device AI tool. No chat listeners or telemetry. */
public final class NabdhAiActivity extends Activity {
    private static final int PICK_GEMMA = 6734;
    private final ExecutorService copies = Executors.newSingleThreadExecutor();
    private Messenger remote;
    private boolean bound;
    private EditText textInput;
    private EditText checksum;
    private TextView state;
    private String approvedHash = "";
    private final Messenger responses = new Messenger(new Handler(Looper.getMainLooper()) {
        @Override public void handleMessage(Message message) {
            if (message.what != NabdhAiCoreService.RESPONSE) return;
            Bundle payload = message.getData();
            String error = payload.getString(NabdhAiCoreService.ERROR, "");
            String provider = payload.getString(NabdhAiCoreService.PROVIDER, "none");
            String result = payload.getString(NabdhAiCoreService.TEXT, "");
            state.setText(error.isEmpty() ? provider + "\n" + result : error);
        }
    });
    private final ServiceConnection connection = new ServiceConnection() {
        @Override public void onServiceConnected(ComponentName name, IBinder binder) {
            remote = new Messenger(binder);
            bound = true;
            request(NabdhAiCoreService.STATUS, "");
        }
        @Override public void onServiceDisconnected(ComponentName name) {
            remote = null;
            bound = false;
            if (state != null) state.setText("Local AI process exited; Telegram is unaffected");
        }
    };

    private Button action(String text, Runnable onClick) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        button.setOnClickListener(v -> onClick.run());
        return button;
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        setTitle("NabdhAI Core");
        ScrollView scroll = new ScrollView(this);
        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setPadding(20, 20, 20, 20);
        screen.setBackgroundColor(Color.rgb(18, 29, 33));
        scroll.addView(screen);
        TextView privacy = new TextView(this);
        privacy.setText("On-device, only when you tap Analyze. "
                + "No automatic chat reading, calls, recording, login access, "
                + "cloud upload, or passive learning. "
                + "Gemini Nano is preferred when AICore has it ready; "
                + "verified Gemma is the fallback on compatible devices.");
        privacy.setTextColor(Color.WHITE);
        privacy.setTextSize(15);
        screen.addView(privacy);
        textInput = new EditText(this);
        textInput.setHint("Paste only the text you want to analyze");
        textInput.setTextColor(Color.WHITE);
        textInput.setHintTextColor(Color.LTGRAY);
        textInput.setMinLines(4);
        textInput.setMaxLines(10);
        screen.addView(textInput);
        screen.addView(action("Analyze selected text with available local model", () -> {
            String text = textInput.getText().toString().trim();
            if (text.length() < 1 || text.length() > 4000) {
                state.setText("Provide 1–4000 characters"); return;
            }
            state.setText("Running local inference...");
            request(NabdhAiCoreService.INFER, text);
        }));
        screen.addView(action("Check automatically selected engine", () -> {
            state.setText("Checking models...");
            request(NabdhAiCoreService.STATUS, "");
        }));
        TextView gemma = new TextView(this);
        gemma.setText("Gemma: import a licensed MediaPipe-compatible .task model from a trusted source. "
                + "Enter its official SHA-256 below. Models are not included in the APK. "
                + "Models are stored only on this device and can be deleted.");
        gemma.setTextColor(Color.LTGRAY);
        gemma.setTextSize(13);
        screen.addView(gemma);
        checksum = new EditText(this);
        checksum.setSingleLine(true);
        checksum.setTextColor(Color.WHITE);
        checksum.setHintTextColor(Color.LTGRAY);
        checksum.setHint("Official 64-character model SHA-256");
        checksum.setInputType(InputType.TYPE_CLASS_TEXT);
        screen.addView(checksum);
        screen.addView(action("Import verified Gemma model", () -> {
            approvedHash = checksum.getText().toString().trim();
            if (!approvedHash.matches("(?i)[a-f0-9]{64}")) {
                state.setText("Supply the published SHA-256 of a trusted model");
                return;
            }
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            picker.setType("*/*");
            picker.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(picker, PICK_GEMMA);
        }));
        screen.addView(action("Delete local Gemma model", () ->
            new AlertDialog.Builder(this)
                .setTitle("Delete imported Gemma model?")
                .setMessage("Local model files will be removed. Your Telegram chats are unaffected.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Delete", (dialog, which) -> {
                    NabdhAiGemmaProvider.remove(this);
                    state.setText("Gemma model deleted");
                }).show()));
        state = new TextView(this);
        state.setTextColor(Color.WHITE);
        state.setTextSize(15);
        state.setPadding(8, 20, 8, 20);
        state.setText("Checking supported local models...");
        screen.addView(state);
        setContentView(scroll);
    }

    private void request(int code, String content) {
        if (!bound || remote == null) {
            if (state != null) state.setText("Local AI service unavailable");
            return;
        }
        Message message = Message.obtain(null, code);
        Bundle fields = new Bundle();
        fields.putString(NabdhAiCoreService.TEXT, content);
        message.setData(fields);
        message.replyTo = responses;
        try { remote.send(message); }
        catch (RemoteException failure) {
            state.setText("Local AI disconnected; Telegram remains available");
        }
    }

    @Override protected void onStart() {
        super.onStart();
        bindService(new Intent(this, NabdhAiCoreService.class), connection,
                Context.BIND_AUTO_CREATE);
    }
    @Override protected void onStop() {
        if (bound) { unbindService(connection); bound = false; remote = null; }
        super.onStop();
    }
    @Override protected void onDestroy() {
        copies.shutdownNow();
        super.onDestroy();
    }

    @Override protected void onActivityResult(int code, int result, Intent data) {
        super.onActivityResult(code, result, data);
        if (code != PICK_GEMMA || result != RESULT_OK ||
                data == null || data.getData() == null) return;
        final Uri source = data.getData();
        final String sha = approvedHash;
        approvedHash = "";
        checksum.setText("");
        state.setText("Verifying model SHA-256 and importing to private storage...");
        copies.execute(() -> {
            try {
                String actual = NabdhAiGemmaProvider.install(this, source, sha);
                runOnUiThread(() ->
                    state.setText("Verified Gemma imported (SHA-256: " + actual + ")"));
            } catch (Exception failure) {
                runOnUiThread(() -> state.setText(
                    "Gemma import rejected. Check model version, free space and published SHA-256."));
            }
        });
    }
}
