package org.telegram.ui;

import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import org.telegram.ui.Components.NabdhAiGemmaProvider;
import org.telegram.ui.Components.NabdhAiNanoProvider;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Separate :nabdh_ai process. All inference is explicit and foreground-bound.
 * A native model crash cannot take down Telegram's chat/call/login process.
 */
public final class NabdhAiCoreService extends Service {
    public static final int STATUS = 1, INFER = 2, RESPONSE = 3;
    public static final String TEXT = "text", PROVIDER = "provider", ERROR = "error";
    private final ExecutorService serial = Executors.newSingleThreadExecutor();
    private final AtomicBoolean busy = new AtomicBoolean(false);
    private final Messenger incoming = new Messenger(new Handler(Looper.getMainLooper()) {
        @Override public void handleMessage(Message request) {
            if (request.what != STATUS && request.what != INFER) {
                super.handleMessage(request);
                return;
            }
            final Messenger response = request.replyTo;
            if (response == null) return;
            final String input = request.getData() == null ? "" :
                    request.getData().getString(TEXT, "");
            if (request.what == INFER && (input.trim().isEmpty() || input.length() > 4000)) {
                send(response, "", "none", "Select 1–4000 characters for on-device processing");
                return;
            }
            if (!busy.compareAndSet(false, true)) {
                send(response, "", "none", "Another local request is running");
                return;
            }
            serial.execute(() -> {
                try {
                    final boolean nano = Build.VERSION.SDK_INT >= 26
                            && NabdhAiNanoProvider.available();
                    final boolean gemma = !nano && NabdhAiGemmaProvider.available(
                            NabdhAiCoreService.this);
                    String selected = nano ? "Gemini Nano" : gemma ? "Gemma" : "none";
                    if (request.what == STATUS) {
                        send(response, nano || gemma ? "Ready" : "No compatible local model ready",
                             selected, "");
                        return;
                    }
                    if (!nano && !gemma) {
                        send(response, "", "none",
                                "Gemini Nano unavailable; import a verified compatible Gemma model");
                        return;
                    }
                    // Exactly one provider is instantiated per request.
                    String prompt = "Analyze only the user-supplied excerpt. "
                            + "List key points, tasks and dates when present. "
                            + "Do not invent details or claim to have read any chat.\n\n"
                            + input;
                    String output = nano ? NabdhAiNanoProvider.infer(prompt)
                            : NabdhAiGemmaProvider.infer(NabdhAiCoreService.this, prompt);
                    send(response, output, selected, "");
                } catch (Throwable failure) {
                    // No user input or full exception trace enters Telegram logs.
                    send(response, "", "none", "Local inference failed; original Telegram remains available");
                } finally {
                    busy.set(false);
                }
            });
        }
    });
    private static void send(Messenger recipient, String value, String engine, String error) {
        Message reply = Message.obtain(null, RESPONSE);
        Bundle data = new Bundle();
        data.putString(TEXT, value);
        data.putString(PROVIDER, engine);
        data.putString(ERROR, error);
        reply.setData(data);
        try { recipient.send(reply); } catch (android.os.RemoteException ignored) { }
    }
    @Override public IBinder onBind(Intent intent) { return incoming.getBinder(); }
    @Override public void onDestroy() {
        serial.shutdownNow();
        super.onDestroy();
    }
}
