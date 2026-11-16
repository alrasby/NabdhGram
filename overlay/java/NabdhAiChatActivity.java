package org.telegram.ui;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.RemoteException;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.NabdhToolUi;
import org.telegram.messenger.LocaleController;

/** Opt-in, in-memory conversation. No Telegram messages, calls, recording or cloud. */
public final class NabdhAiChatActivity extends Activity {
    private final StringBuilder history = new StringBuilder();
    private Messenger service;
    private boolean bound;
    private boolean bindingRequested;
    private boolean waiting;
    private boolean ignorePendingResponse;
    private TextView transcript;
    private TextView status;
    private EditText input;
    private Button sendButton;
    private ScrollView scroller;
    private String pendingText;

    private String local(String en, String ar) {
        return LocaleController.isRTL ? ar : en;
    }
    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
    private final Messenger replies = new Messenger(new Handler(Looper.getMainLooper()) {
        @Override public void handleMessage(Message response) {
            if (response.what != NabdhAiCoreService.RESPONSE || isFinishing()) return;
            final Bundle payload = response.getData();
            final String result = payload.getString(NabdhAiCoreService.TEXT, "");
            final String engine = payload.getString(NabdhAiCoreService.PROVIDER, "none");
            final String error = payload.getString(NabdhAiCoreService.ERROR, "");
            waiting = false;
            sendButton.setEnabled(bound);
            if (ignorePendingResponse) {
                ignorePendingResponse = false;
                return;
            }
            if (!error.isEmpty() || result.isEmpty()) {
                status.setText("NO_MODEL".equals(error) || "NANO_UNAVAILABLE".equals(error)
                        || "AICORE_CHECK_FAILED".equals(error) ?
                        local("No on-device model is ready. Open NabdhAI Core to check "
                                + "AICore or import a verified Gemma .task model.",
                                "لا يوجد نموذج محلي جاهز. افتح محرك NabdhAI لفحص AICore "
                                + "أو استيراد نموذج Gemma متوافق وموثق.")
                        : local("Local inference failed. You can retry.",
                                "تعذر الاستدلال المحلي، ويمكنك إعادة المحاولة."));
                pendingText = null;
                return;
            }
            if (pendingText != null) {
                append(local("You", "أنت") + ": ", pendingText);
                remember("User: ", pendingText);
                pendingText = null;
            }
            append("NabdhAI (" + engine + "): ", result);
            remember("Assistant: ", result);
            status.setText(local("Reply generated locally by ", "إجابة محلية بواسطة ") + engine);
        }
    });
    private final ServiceConnection connection = new ServiceConnection() {
        @Override public void onServiceConnected(ComponentName name, IBinder binder) {
            service = new Messenger(binder);
            bound = true;
            sendButton.setEnabled(true);
            status.setText(local("Ready to ask if a local model is installed.",
                    "جاهز لاستقبال الأسئلة عند توفر نموذج محلي."));
        }
        @Override public void onServiceDisconnected(ComponentName name) {
            service = null;
            bound = false;
            waiting = false;
            if (sendButton != null) sendButton.setEnabled(false);
            if (status != null) status.setText(local("Local AI process disconnected.",
                    "انقطع اتصال محرك الذكاء المحلي."));
        }
    };
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        scroller = new ScrollView(this);
        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setPadding(dp(16), dp(12), dp(16), dp(22));
        screen.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));
        scroller.addView(screen);
        TextView privacy = new TextView(this);
        privacy.setText(local("Private session, cleared when you close this page. "
                + "Only text typed here is passed to the local engine. "
                + "No automatic Telegram chat or call access.",
                "محادثة محلية خاصة تُمحى عند إغلاق الصفحة. "
                + "يُرسل للنموذج النص الذي تكتبه هنا فقط، "
                + "دون قراءة تلقائية لرسائل Telegram أو المكالمات."));
        privacy.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        privacy.setTextSize(13);
        screen.addView(privacy);
        transcript = new TextView(this);
        transcript.setTextSize(15);
        transcript.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        transcript.setPadding(dp(8), dp(16), dp(8), dp(16));
        transcript.setText(local("AI Chat: type your first question.",
                "AI Chat: اكتب سؤالك الأول."));
        screen.addView(transcript);
        status = new TextView(this);
        status.setTextSize(13);
        status.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        status.setText(local("Connecting to private AI process...",
                "جارٍ الاتصال بمحرك الذكاء المحلي..."));
        screen.addView(status);
        input = new EditText(this);
        NabdhToolUi.styleInput(this, input);
        input.setHint(local("Write your question", "اكتب سؤالك"));
        input.setMinLines(2);
        input.setMaxLines(5);
        input.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        screen.addView(input);
        sendButton = new Button(this);
        NabdhToolUi.styleButton(this, sendButton);
        sendButton.setAllCaps(false);
        sendButton.setText(local("Send to local AI", "إرسال إلى الذكاء المحلي"));
        sendButton.setEnabled(false);
        sendButton.setOnClickListener(v -> send());
        screen.addView(sendButton);
        Button clear = new Button(this);
        NabdhToolUi.styleButton(this, clear);
        clear.setAllCaps(false);
        clear.setText(local("Clear private conversation", "مسح المحادثة الخاصة"));
        clear.setOnClickListener(v -> {
            history.setLength(0);
            pendingText = null;
            ignorePendingResponse = waiting;
            transcript.setText(local("Conversation cleared", "تم مسح المحادثة"));
            status.setText(local("Private text is not retained", "لا يُحتفظ بالنص الخاص"));
        });
        screen.addView(clear);
        Button model = new Button(this);
        NabdhToolUi.styleButton(this, model);
        model.setAllCaps(false);
        model.setText(local("Configure local model", "إعداد النموذج المحلي"));
        model.setOnClickListener(v -> startActivity(new Intent(this, NabdhAiActivity.class)));
        screen.addView(model);
        NabdhToolUi.install(this, scroller, "NabdhAI Chat");
    }
    private void append(String prefix, String body) {
        if (transcript.length() > 12000)
            transcript.setText(transcript.getText().subSequence(transcript.length() - 7000,
                    transcript.length()));
        transcript.append("\n\n" + prefix + body);
        scroller.post(() -> scroller.fullScroll(ScrollView.FOCUS_DOWN));
    }
    private void remember(String role, String value) {
        history.append(role).append(value).append("\n");
        if (history.length() > 2300) history.delete(0, history.length() - 2300);
    }
    private void send() {
        if (!bound || service == null || waiting) return;
        String user = input.getText().toString().trim();
        if (user.isEmpty() || user.length() > 1500) {
            status.setText(local("Use 1–1500 characters", "أدخل نصًا بين حرف و1500 حرف"));
            return;
        }
        final String prompt = history.toString() + "\nUser: " + user;
        Message task = Message.obtain(null, NabdhAiCoreService.CHAT);
        Bundle data = new Bundle();
        data.putString(NabdhAiCoreService.TEXT, prompt);
        task.setData(data);
        task.replyTo = replies;
        try {
            service.send(task);
            pendingText = user;
            ignorePendingResponse = false;
            waiting = true;
            sendButton.setEnabled(false);
            input.setText("");
            status.setText(local("Generating locally...", "جارٍ توليد الرد محليًا..."));
        } catch (RemoteException error) {
            status.setText(local("Local model connection interrupted",
                    "انقطع الاتصال بالنموذج المحلي"));
        }
    }
    @Override protected void onStart() {
        super.onStart();
        if (Build.VERSION.SDK_INT < 26) {
            status.setText(local("Local AI requires Android 26+ on supported devices.",
                    "يتطلب الذكاء المحلي Android 26 أو أحدث على جهاز مدعوم."));
            return;
        }
        bindingRequested = bindService(new Intent(this, NabdhAiCoreService.class),
                connection, Context.BIND_AUTO_CREATE);
        if (!bindingRequested) status.setText(local("Local model service unavailable",
                "خدمة الذكاء المحلي غير متاحة"));
    }
    @Override protected void onStop() {
        if (bindingRequested) {
            unbindService(connection);
            bindingRequested = false;
        }
        service = null;
        bound = false;
        waiting = false;
        if (sendButton != null) sendButton.setEnabled(false);
        super.onStop();
    }
    @Override protected void onDestroy() {
        history.setLength(0);
        super.onDestroy();
    }
}
