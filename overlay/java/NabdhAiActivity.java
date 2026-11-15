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
    private boolean bindingRequested;
    private EditText textInput;
    private EditText checksum;
    private TextView state;
    private String approvedHash = "";
    private String local(String en, String ar) {
        return org.telegram.messenger.LocaleController.isRTL ? ar : en;
    }
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
            if (state != null) state.setText(local("Local AI process exited; Telegram is unaffected",
                    "توقفت عملية الذكاء المحلي، وTelegram يعمل بصورة طبيعية"));
        }
    };

    private Button action(String text, Runnable onClick) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        button.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        button.setBackground(
                org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        button.setOnClickListener(v -> onClick.run());
        return button;
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        setTitle(local("NabdhAI Core", "محرك نبض للذكاء الاصطناعي"));
        ScrollView scroll = new ScrollView(this);
        LinearLayout screen = new LinearLayout(this);
        screen.setOrientation(LinearLayout.VERTICAL);
        screen.setPadding(20, 20, 20, 20);
        screen.setBackgroundColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhite));
        screen.setLayoutDirection(org.telegram.messenger.LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        scroll.addView(screen);
        TextView privacy = new TextView(this);
        privacy.setText(local("On-device, only when you tap Analyze. "
                + "No automatic chat reading, calls, recording, login access, "
                + "cloud upload, or passive learning. "
                + "Gemini Nano is preferred when AICore has it ready; "
                + "verified Gemma is the fallback on compatible devices.",
                "استنتاج محلي فقط بعد الضغط على تحليل. لا قراءة تلقائية للمحادثات أو "
                + "وصول للمكالمات والتسجيل وتسجيل الدخول، ولا رفع سحابي أو تعلّم خفي. "
                + "يُفضّل Gemini Nano عند توفره، وإلا يُستخدم Gemma الموثّق على الأجهزة المتوافقة."));
        privacy.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        privacy.setTextSize(15);
        screen.addView(privacy);
        textInput = new EditText(this);
        textInput.setHint(local("Paste only the text you want to analyze",
                "الصق فقط النص الذي ترغب في تحليله"));
        textInput.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        textInput.setHintTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        textInput.setMinLines(4);
        textInput.setMaxLines(10);
        screen.addView(textInput);
        screen.addView(action(local("Analyze selected text with available local model",
                "تحليل النص بالنموذج المحلي المتاح"), () -> {
            String text = textInput.getText().toString().trim();
            if (text.length() < 1 || text.length() > 4000) {
                state.setText(local("Provide 1–4000 characters",
                        "أدخل نصًا بين حرف واحد و4000 حرف")); return;
            }
            state.setText(local("Running local inference...", "جارٍ تنفيذ الاستنتاج المحلي..."));
            request(NabdhAiCoreService.INFER, text);
        }));
        screen.addView(action(local("Check automatically selected engine",
                "فحص المحرك المحدد تلقائيًا"), () -> {
            state.setText(local("Checking models...", "جارٍ فحص النماذج..."));
            request(NabdhAiCoreService.STATUS, "");
        }));
        TextView gemma = new TextView(this);
        gemma.setText(local("Gemma: import a licensed MediaPipe-compatible .task model from a trusted source. "
                + "Enter its official SHA-256 below. Models are not included in the APK. "
                + "Models are stored only on this device and can be deleted.",
                "Gemma: استورد نموذج .task مرخّصًا ومتوافقًا مع MediaPipe من مصدر موثوق، "
                + "ثم أدخل بصمته SHA-256 الرسمية. النماذج غير مضمّنة بالتطبيق، "
                + "وتُحفظ محليًا ويمكن حذفها."));
        gemma.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        gemma.setTextSize(13);
        screen.addView(gemma);
        checksum = new EditText(this);
        checksum.setSingleLine(true);
        checksum.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        checksum.setHintTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        checksum.setHint(local("Official 64-character model SHA-256",
                "بصمة SHA-256 الرسمية للنموذج (64 خانة)"));
        checksum.setInputType(InputType.TYPE_CLASS_TEXT);
        screen.addView(checksum);
        screen.addView(action(local("Import verified Gemma model",
                "استيراد نموذج Gemma موثّق"), () -> {
            approvedHash = checksum.getText().toString().trim();
            if (!approvedHash.matches("(?i)[a-f0-9]{64}")) {
                state.setText(local("Supply the published SHA-256 of a trusted model",
                        "أدخل بصمة SHA-256 المنشورة لنموذج موثوق"));
                return;
            }
            Intent picker = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            picker.setType("*/*");
            picker.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(picker, PICK_GEMMA);
        }));
        screen.addView(action(local("Delete local Gemma model", "حذف نموذج Gemma المحلي"), () ->
            new AlertDialog.Builder(this)
                .setTitle(local("Delete imported Gemma model?",
                        "هل تريد حذف نموذج Gemma المستورد؟"))
                .setMessage(local("Local model files will be removed. Your Telegram chats are unaffected.",
                        "سيُحذف النموذج المحلي فقط، ولن تتأثر محادثات Telegram."))
                .setNegativeButton(local("Cancel", "إلغاء"), null)
                .setPositiveButton(local("Delete", "حذف"), (dialog, which) -> {
                    NabdhAiGemmaProvider.remove(this);
                    state.setText(local("Gemma model deleted", "حُذف نموذج Gemma المحلي"));
                }).show()));
        state = new TextView(this);
        state.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        state.setTextSize(15);
        state.setPadding(8, 20, 8, 20);
        state.setText(local("Checking supported local models...",
                "جارٍ فحص النماذج المحلية المدعومة..."));
        screen.addView(state);
        org.telegram.ui.Components.NabdhToolUi.install(this, scroll,
                local("NabdhAI Core", "محرك نبض للذكاء الاصطناعي"));
    }

    private void request(int code, String content) {
        if (!bound || remote == null) {
            if (state != null) state.setText(local("Local AI service unavailable", "خدمة الذكاء المحلي غير متاحة"));
            return;
        }
        Message message = Message.obtain(null, code);
        Bundle fields = new Bundle();
        fields.putString(NabdhAiCoreService.TEXT, content);
        message.setData(fields);
        message.replyTo = responses;
        try { remote.send(message); }
        catch (RemoteException failure) {
            state.setText(local("Local AI disconnected; Telegram remains available",
                    "انقطع الاتصال بمحرك الذكاء المحلي، وTelegram يعمل طبيعيًا"));
        }
    }

    @Override protected void onStart() {
        super.onStart();
        // Protect Telegram Android 23–25: neither optional AI SDK may load here.
        // Gemini Nano requires API 26+; Gemma requires even newer hardware.
        if (android.os.Build.VERSION.SDK_INT < 26) {
            state.setText(local(
                "On-device AI is unavailable on this Android version. Telegram remains fully usable.",
                "الذكاء المحلي غير متاح لهذا الإصدار من Android، وستبقى وظائف Telegram متاحة."));
            return;
        }
        // Bind in this Activity lifecycle only. Never keep AI alive in Telegram background.
        bindingRequested = bindService(
                new Intent(this, NabdhAiCoreService.class),
                connection, Context.BIND_AUTO_CREATE);
        if (!bindingRequested && state != null) state.setText(local("Local AI service unavailable", "خدمة الذكاء المحلي غير متاحة"));
    }
    @Override protected void onStop() {
        if (bindingRequested) {
            unbindService(connection);
            bindingRequested = false;
        }
        bound = false;
        remote = null;
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
        state.setText(local("Verifying model SHA-256 and importing to private storage...",
                "جارٍ التحقق من بصمة النموذج واستيراده إلى التخزين الخاص..."));
        copies.execute(() -> {
            try {
                String actual = NabdhAiGemmaProvider.install(this, source, sha);
                runOnUiThread(() ->
                    state.setText(local("Verified Gemma imported (SHA-256: ",
                            "تم استيراد نموذج Gemma الموثّق (SHA-256: ") + actual + ")"));
            } catch (Exception failure) {
                runOnUiThread(() -> state.setText(
                    local("Gemma import rejected. Check model version, free space and published SHA-256.",
                    "رُفض استيراد Gemma. تحقق من إصدار النموذج والمساحة وبصمة SHA-256 المنشورة.")));
            }
        });
    }
}
