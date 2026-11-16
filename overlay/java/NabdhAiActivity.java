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
    // SHA-256 published for the 555 MB gemma3-1b-it-int4.task file by
    // multiple community mirrors. This is an integrity check for that exact
    // file, not a grant of Gemma rights or proof of publisher provenance.
    private static final String GEMMA_3_1B_INT4_SHA256 =
            "e3d981c01aeaaac69a84ffa0d4be13281b3176731063f1bea1c9fe6887bd9dee";
    private final ExecutorService copies = Executors.newSingleThreadExecutor();
    private Messenger remote;
    private boolean bound;
    private boolean bindingRequested;
    private EditText textInput;
    private EditText checksum;
    private TextView state;
    private Button downloadNano;
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
            String summary = !error.isEmpty() ? displayStatus(error, provider) :
                    displayStatus(result, provider);
            // Show a harmless failure category for reliable user-side
            // diagnostics without exposing model prompts or internal logs.
            String diagnostic = payload.getString(NabdhAiCoreService.NANO_DIAGNOSTIC, "");
            if (!diagnostic.isEmpty()) {
                summary += "\\n" + local("AICore diagnostic: ", "تشخيص AICore: ") + diagnostic;
            }
            state.setText(summary);
            // Only AICore DOWNLOADABLE authorizes an actionable download.
            // A generic "Download" button on unsupported hardware is misleading.
            if (downloadNano != null) {
                boolean downloadable = bound && payload.getBoolean(
                        NabdhAiCoreService.NANO_CAN_DOWNLOAD, false);
                downloadNano.setEnabled(downloadable);
                downloadNano.setAlpha(downloadable ? 1f : 0.5f);
            }
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
            if (downloadNano != null) downloadNano.setEnabled(false);
            if (state != null) state.setText(local("Local AI process exited; Telegram is unaffected",
                    "توقفت عملية الذكاء المحلي، وTelegram يعمل بصورة طبيعية"));
        }
    };

    private String displayStatus(String code, String provider) {
        if (code == null) return "";
        if (code.startsWith("NANO_DOWNLOAD_PROGRESS:")) {
            try {
                long received = Long.parseLong(code.substring("NANO_DOWNLOAD_PROGRESS:".length()));
                return local("Downloading Gemini Nano: ", "تنزيل Gemini Nano: ")
                        + (received / (1024L * 1024L)) + " MB";
            } catch (NumberFormatException ignored) {
                return local("Downloading Gemini Nano", "جارٍ تنزيل Gemini Nano");
            }
        }
        switch (code) {
            case "MODEL_READY":
                return local("Local model ready: ", "النموذج المحلي جاهز: ") + provider;
            case "NO_MODEL":
                return local("No compatible local AI model is installed. Gemini Nano requires "
                        + "a supported AICore device, or you can import a compatible verified Gemma .task model.",
                        "لا يوجد نموذج ذكاء محلي متوافق مثبت. يحتاج Gemini Nano إلى جهاز مدعوم "
                        + "بنظام AICore، أو يمكنك استيراد نموذج Gemma بصيغة .task متوافقة وموثقة.");
            case "NANO_DOWNLOADABLE":
                return local("Gemini Nano is supported but not downloaded. "
                        + "Tap Download Gemini Nano to request the official AICore model.",
                        "جهازك يدعم Gemini Nano لكن النموذج لم يُنزّل. "
                        + "اضغط تنزيل Gemini Nano لطلب النموذج الرسمي عبر AICore.");
            case "NANO_DOWNLOADING":
                return local("AICore reports that Gemini Nano is downloading. "
                        + "Check again when the download completes.",
                        "يشير AICore إلى أن Gemini Nano قيد التنزيل. "
                        + "تحقق من الحالة بعد اكتمال التنزيل.");
            case "NANO_UNAVAILABLE":
                return local("Google AICore reports Gemini Nano UNAVAILABLE. The device may be "
                        + "unsupported or its feature configuration may not be ready. "
                        + "No model download has started. Check supported devices, update "
                        + "AICore if available, or import a verified compatible Gemma model.",
                        "Google AICore يُبلغ أن Gemini Nano غير متاح على هذا الجهاز حاليًا. "
                        + "قد يكون الجهاز غير مدعوم أو لم يكتمل إعداد AICore. "
                        + "لم يبدأ تنزيل نموذج. راجع الأجهزة المدعومة وتحديثات AICore، "
                        + "أو استورد نموذج Gemma متوافقًا وموثّقًا.");
            case "AICORE_CHECK_FAILED":
                return local("Could not check Google AICore (service unavailable or not initialized). "
                        + "Update AICore and Google Play system components if available, "
                        + "connect to the internet and try Check Engine again. "
                        + "This does not prove the device is unsupported.",
                        "تعذّر الاتصال بخدمة Google AICore أو فحصها. "
                        + "تحقق من تحديث AICore ومكوّنات Google Play إن توفرت، "
                        + "واتصل بالإنترنت وأعد فحص المحرك. "
                        + "هذا لا يثبت أن جهازك غير مدعوم.");
            case "NANO_DOWNLOAD_STARTING":
            case "NANO_DOWNLOAD_STARTED":
                return local("AICore started the requested Gemini Nano download.",
                        "بدأ AICore تنزيل Gemini Nano بناءً على طلبك.");
            case "NANO_DOWNLOAD_COMPLETE":
                return local("AICore download completed; verifying model readiness.",
                        "اكتمل التنزيل عبر AICore؛ جارٍ فحص جاهزية النموذج.");
            case "NANO_DOWNLOAD_PENDING":
                return local("The download request returned, but the model is not yet ready. "
                        + "Check status before trying inference.",
                        "عاد طلب التنزيل لكن النموذج لم يصبح جاهزًا بعد. "
                        + "افحص الحالة قبل الاستدلال.");
            case "NANO_DOWNLOAD_FAILED":
                return local("AICore could not download Gemini Nano. "
                        + "Check device support, connectivity and available storage.",
                        "تعذر تنزيل Gemini Nano عبر AICore. "
                        + "تحقق من دعم الجهاز والاتصال والمساحة.");
            case "Local inference failed; original Telegram remains available":
                return local("Local inference failed. Your Telegram messages are unaffected.",
                        "فشل الاستدلال المحلي؛ لم تتأثر رسائل Telegram.");
            case "Another local request is running":
                return local("A local AI operation is already running.",
                        "هناك عملية ذكاء محلي قيد التنفيذ.");
            case "Gemini Nano unavailable; import a verified compatible Gemma model":
                return displayStatus("NO_MODEL", provider);
            default:
                return "none".equals(provider) || provider.isEmpty() ? code : provider + "\n" + code;
        }
    }

    private Button action(String text, Runnable onClick) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        button.setMinHeight((int) (52 * getResources().getDisplayMetrics().density + .5f));
        button.setTextSize(14);
        button.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        org.telegram.ui.Components.NabdhToolUi.styleButton(this, button);
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
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundGray));
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
        org.telegram.ui.Components.NabdhToolUi.styleInput(this, textInput);
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
        downloadNano = action(local("Download Gemini Nano (only when available)",
                "تنزيل Gemini Nano عند توفره على الجهاز"), () ->
            new AlertDialog.Builder(this)
                .setTitle(local("Request official Gemini Nano download?",
                        "هل تريد تنزيل Gemini Nano الرسمي؟"))
                .setMessage(local("The model is managed by Google AICore and may require "
                        + "significant storage and network data. It will be requested only "
                        + "if AICore reports DOWNLOADABLE on this device.",
                        "يدير Google AICore النموذج، وقد يتطلب مساحة وبيانات تنزيل كبيرة. "
                        + "لن يبدأ الطلب إلا إذا أعلن AICore أن النموذج قابل للتنزيل على جهازك."))
                .setNegativeButton(local("Cancel", "إلغاء"), null)
                .setPositiveButton(local("Download", "تنزيل"), (dialog, which) -> {
                    state.setText(local("Checking Google AICore support...",
                            "جارٍ فحص دعم Google AICore..."));
                    request(NabdhAiCoreService.DOWNLOAD_NANO, "");
                }).show());
        // Disabled until the isolated service confirms DOWNLOADABLE.
        downloadNano.setEnabled(false);
        downloadNano.setAlpha(0.5f);
        screen.addView(downloadNano);
        screen.addView(action(local("Official Gemini Nano device support",
                "الأجهزة المدعومة رسميًا من Google"), () -> {
            Intent guide = new Intent(Intent.ACTION_VIEW,
                    Uri.parse("https://developers.google.com/ml-kit/genai/#device-support"));
            try { startActivity(guide); } catch (RuntimeException unsupported) {
                state.setText(local("No browser available to open the device support page.",
                        "لا يوجد متصفح متاح لعرض الأجهزة المدعومة."));
            }
        }));
        screen.addView(action(local("Open AI Chat (on-device)",
                "فتح AI Chat — محادثة محلية"), () ->
                startActivity(new Intent(this, NabdhAiChatActivity.class))));
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
        screen.addView(action(local("How to obtain a compatible Gemma model",
                "دليل الحصول على نموذج Gemma متوافق"), () -> {
            Intent guide = new Intent(Intent.ACTION_VIEW,
                    Uri.parse("https://developers.google.com/edge/mediapipe/solutions/genai/llm_inference/android"));
            try { startActivity(guide); } catch (RuntimeException unsupported) {
                state.setText(local("No browser available to open the model guide.",
                        "لا يوجد متصفح متاح لعرض دليل النموذج."));
            }
        }));
        checksum = new EditText(this);
        org.telegram.ui.Components.NabdhToolUi.styleInput(this, checksum);
        checksum.setSingleLine(true);
        checksum.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteBlackText));
        checksum.setHintTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        checksum.setHint(local("Official 64-character model SHA-256",
                "بصمة SHA-256 الرسمية للنموذج (64 خانة)"));
        checksum.setInputType(InputType.TYPE_CLASS_TEXT);
        screen.addView(checksum);
        screen.addView(action(local("Get Gemma 3 1B model (555 MB, separate download)",
                "الحصول على Gemma 3 1B (تنزيل منفصل 555 MB)"), () ->
            new AlertDialog.Builder(this)
                .setTitle(local("Gemma model licence and download",
                        "ترخيص وتنزيل نموذج Gemma"))
                .setMessage(local("Gemma 3 1B requires acceptance of Google's Gemma terms "
                        + "on Hugging Face. A large .task model is downloaded outside the APK. "
                        + "The app will fill a SHA-256 value published for the matching "
                        + "int4 model by third-party mirrors, then verify its actual bytes "
                        + "on import. This hash alone does not prove the publisher's identity. "
                        + "Import only after confirming the official file and licence.",
                        "يتطلب Gemma 3 1B قبول ترخيص Google Gemma في Hugging Face. "
                        + "يُنزّل ملف .task الكبير خارج APK. سنُدرج بصمة SHA-256 منشورة "
                        + "لنفس ملف int4 في نسخ مجتمعية مستقلة، ثم نتحقق من بايتات "
                        + "الملف عند الاستيراد. البصمة وحدها لا تثبت هوية الناشر. "
                        + "تحقق من المصدر الرسمي والترخيص قبل الاستيراد."))
                .setNegativeButton(local("Cancel", "إلغاء"), null)
                .setPositiveButton(local("Review licence & model", "مراجعة الترخيص والنموذج"),
                        (dialog, which) -> {
                            checksum.setText(GEMMA_3_1B_INT4_SHA256);
                            try {
                                startActivity(new Intent(Intent.ACTION_VIEW,
                                        Uri.parse("https://huggingface.co/litert-community/"
                                                + "Gemma3-1B-IT/blob/main/gemma3-1b-it-int4.task")));
                            } catch (RuntimeException missingBrowser) {
                                state.setText(local("No browser to open the official model page",
                                        "لا يوجد متصفح لفتح صفحة النموذج الرسمية"));
                            }
                        }).show()));
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
        // Make the actual model state visible immediately, without scrolling
        // past all tools, upload controls and the optional Gemma instructions.
        screen.addView(state, 1);
        TextView deviceInfo = new TextView(this);
        deviceInfo.setText(local("Device: ", "الجهاز: ")
                + android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL
                + " · Android " + android.os.Build.VERSION.RELEASE);
        deviceInfo.setTextSize(12);
        deviceInfo.setTextColor(org.telegram.ui.ActionBar.Theme.getColor(
                org.telegram.ui.ActionBar.Theme.key_windowBackgroundWhiteGrayText2));
        deviceInfo.setPadding(8, 0, 8, 12);
        screen.addView(deviceInfo, 2);
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
        if (downloadNano != null) downloadNano.setEnabled(false);
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
