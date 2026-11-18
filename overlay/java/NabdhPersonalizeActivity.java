package org.telegram.ui;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.CompoundButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import android.graphics.drawable.GradientDrawable;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.NabdhCompactSettings;
import org.telegram.ui.Components.NabdhHomePrefs;
import org.telegram.ui.Components.NabdhToolUi;

/** Explicit, locally applied layout and Camera2 controls; no server changes. */
public final class NabdhPersonalizeActivity extends Activity {
    public static final String EXTRA_SECTION = "section";
    public static final String HOME = "home";
    public static final String BUBBLES = "bubbles";
    public static final String CAMERA = "camera";
    private LinearLayout content;
    private String section;

    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }
    private String local(String en, String ar) { return LocaleController.isRTL ? ar : en; }
    private void refresh() {
        // Native chat list rechecks prefs onResume. Native MessageDrawable already
        // reads SharedConfig.bubbleRadius; invalidate theme-bound visible cells.
        NotificationCenter.getGlobalInstance().postNotificationName(
                NotificationCenter.didSetNewTheme, false, false);
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        section = getIntent().getStringExtra(EXTRA_SECTION);
        if (!HOME.equals(section) && !BUBBLES.equals(section) && !CAMERA.equals(section)) {
            finish(); return;
        }
        ScrollView scroll = new ScrollView(this);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(16), dp(8), dp(16), dp(24));
        content.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));
        scroll.addView(content);
        render();
        NabdhToolUi.install(this, scroll,
                HOME.equals(section) ? local("Home layout", "تنسيق الشاشة الرئيسية") :
                BUBBLES.equals(section) ? local("Chat bubbles", "فقاعات المحادثات") :
                local("Nabdh Camera2", "إعدادات كاميرا نبض"));
    }
    private void header(String en, String ar) {
        NabdhCompactSettings.header(this, content, local(en, ar));
    }
    private void note(String en, String ar) {
        TextView label = new TextView(this);
        label.setText(local(en, ar));
        label.setTextSize(13);
        label.setGravity(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT);
        label.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        label.setPadding(dp(9), dp(5), dp(9), dp(14));
        content.addView(label);
    }
    private void toggle(String key, String en, String ar, String detailEn, String detailAr) {
        // Force the switch to the LEFT in both RTL and LTR, as requested.
        LinearLayout line = new LinearLayout(this);
        line.setOrientation(LinearLayout.HORIZONTAL);
        line.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        line.setGravity(Gravity.CENTER_VERTICAL);
        line.setPadding(dp(12), dp(8), dp(12), dp(8));
        GradientDrawable shape = new GradientDrawable();
        shape.setCornerRadius(dp(18));
        shape.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        line.setBackground(shape);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = dp(8);
        content.addView(line, lp);
        Switch control = new Switch(this);
        control.setChecked(NabdhHomePrefs.enabled(this, key));
        line.addView(control, new LinearLayout.LayoutParams(dp(58), dp(48)));
        LinearLayout textStack = new LinearLayout(this);
        textStack.setOrientation(LinearLayout.VERTICAL);
        textStack.setLayoutDirection(LocaleController.isRTL ?
                View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        textStack.setPadding(dp(12), 0, dp(4), 0);
        TextView title = new TextView(this);
        title.setText(local(en, ar));
        title.setTextSize(15);
        title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        TextView description = new TextView(this);
        description.setText(local(detailEn, detailAr));
        description.setTextSize(12);
        description.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        textStack.addView(title);
        textStack.addView(description);
        line.addView(textStack, new LinearLayout.LayoutParams(0, -2, 1));
        control.setOnCheckedChangeListener((button, checked) -> {
            NabdhHomePrefs.set(this, key, checked);
            refresh();
        });
        line.setOnClickListener(v -> control.setChecked(!control.isChecked()));
    }
    private void choice(String label, String detail, int mode, boolean selected) {
        NabdhCompactSettings.row(this, content, (selected ? "✓  " : "") + label,
                detail, R.drawable.settings_folders, () -> {
                    NabdhHomePrefs.setFolderMode(this, mode);
                    refresh();
                    render();
                });
    }
    private void videoFpsChoice(int rate) {
        int active = NabdhHomePrefs.videoFps(this);
        NabdhCompactSettings.row(this, content,
                (active == rate ? "✓  " : "") + rate + " FPS",
                local("Recorder requests this value; unsupported hardware falls back.",
                        "يطلب التسجيل هذا المعدل، ويستخدم المتاح إذا لم تدعمه الكاميرا."),
                R.drawable.nabdh_tool_camera, () -> {
                    NabdhHomePrefs.setVideoFps(this, rate);
                    render();
                });
    }
    private void bubble(String en, String ar, int radius) {
        int current = NabdhHomePrefs.bubbleRadius(this);
        NabdhCompactSettings.row(this, content,
                (current == radius ? "✓  " : "") + local(en, ar),
                local("Corner radius: ", "استدارة الزوايا: ") + radius + "dp",
                R.drawable.settings_chat, () -> {
                    NabdhHomePrefs.setBubbleRadius(this, radius);
                    refresh();
                    render();
                });
    }
    private void render() {
        content.removeAllViews();
        if (HOME.equals(section)) {
            header("Main screen", "الشاشة الرئيسية");
            toggle("center_title", "Center NabdhGram title", "توسيط عنوان نبض جرام",
                    "Center the title without moving the main toolbar buttons",
                    "توسيط الاسم دون تحريك أزرار شريط العنوان");
            toggle("hide_stories", "Hide stories", "إخفاء القصص",
                    "Hide the stories strip only; stories are not deleted",
                    "إخفاء شريط القصص فقط دون حذفها");
            toggle("hide_fab", "Hide floating compose button", "إخفاء زر المحادثة العائم",
                    "Chats and Telegram compose tools remain available",
                    "تبقى المحادثات وأدوات المراسلة متاحة");
            toggle("hide_search", "Hide search bar", "إخفاء شريط البحث",
                    "Keep Telegram's search action available when opened",
                    "يبقى البحث متاحًا من أداة البحث عند فتحها");
            header("Chat folders", "مجلدات المحادثات");
            note("Native Telegram folder tabs stay visible, even when only All Chats exists. "
                    + "Create additional folders in Telegram settings; this controls labels, not their contents.",
                    "يبقى شريط مجلدات Telegram ظاهرًا حتى عند وجود «كل المحادثات» فقط. "
                    + "أنشئ مجلدات أخرى من إعدادات Telegram؛ هذا الخيار يغير العرض لا المحتوى.");
            int mode = NabdhHomePrefs.folderMode(this);
            choice(local("Names and icons", "أسماء مع أيقونات"),
                    local("Folder icon and original title", "أيقونة المجلد مع اسمه"), 0, mode == 0);
            choice(local("Names only", "الأسماء فقط"),
                    local("Telegram's original names", "الأسماء الأصلية دون أيقونات إضافية"), 1, mode == 1);
            choice(local("Icons only", "الأيقونات فقط"),
                    local("Minimal folder tabs", "شريط مجلدات بأيقونات مختصرة"), 2, mode == 2);
        } else if (BUBBLES.equals(section)) {
            header("Bubble corners", "أشكال فقاعات المحادثات");
            note("These use Telegram's actual message bubble radius. Your existing Glass "
                    + "theme colors, replies, media and accessibility are preserved.",
                    "تستخدم الأشكال استدارة فقاعات Telegram الفعلية، دون تغيير ألوان الثيم الزجاجي "
                    + "أو الردود والوسائط وإمكانية الوصول.");
            // A lightweight preview follows the exact radius used by
            // Telegram MessageDrawable, without creating a fake chat.
            int radius = dp(NabdhHomePrefs.bubbleRadius(this));
            for (boolean outgoing : new boolean[]{false, true}) {
                TextView sample = new TextView(this);
                sample.setText(outgoing
                        ? local("Outgoing message", "رسالة صادرة")
                        : local("Incoming message", "رسالة واردة"));
                sample.setTextSize(15);
                sample.setTextColor(Theme.getColor(outgoing
                        ? Theme.key_chat_messageTextOut : Theme.key_chat_messageTextIn));
                sample.setPadding(dp(14), dp(13), dp(14), dp(13));
                GradientDrawable bg = new GradientDrawable();
                bg.setCornerRadius(radius);
                bg.setColor(Theme.getColor(outgoing
                        ? Theme.key_chat_outBubble : Theme.key_chat_inBubble));
                sample.setBackground(bg);
                LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-2, -2);
                params.gravity = outgoing ? Gravity.RIGHT : Gravity.LEFT;
                params.bottomMargin = dp(12);
                content.addView(sample, params);
            }
            bubble("Compact", "مضغوطة", 12);
            bubble("Soft rounded", "دائرية ناعمة", 19);
            bubble("Extra rounded", "دائرية واسعة", 24);
        } else {
            header("Camera2 photo settings", "إعدادات صور Camera2");
            toggle("camera_remember", "Remember last lens", "تذكر آخر عدسة",
                    "Use the last front/back lens when you open the camera again",
                    "فتح العدسة الأمامية أو الخلفية المستخدمة أخيرًا");
            toggle("camera_mirror", "Mirror front camera photos", "عكس صور الكاميرا الأمامية",
                    "Save a mirrored selfie; optional image re-encoding",
                    "حفظ صورة سيلفي معكوسة، مع إعادة ترميز الصورة عند التفعيل");
            toggle("camera_stabilize", "Optical image stabilization", "تثبيت الصورة البصري",
                    "Enable only when the selected Camera2 lens supports OIS",
                    "يُفعّل فقط عندما تدعم العدسة تثبيت الصورة البصري OIS");
            toggle("camera_quality", "Prefer full-resolution photos", "تفضيل دقة الصور العالية",
                    "Use the largest compatible native Camera2 JPEG size (default on); "
                    + "if a high-resolution session fails, safely retry with a fast size.",
                    "استخدام أكبر دقة JPEG حقيقية متوافقة مع Camera2 (مفعلة افتراضيًا)، "
                    + "والعودة لدقة سريعة عند عدم قبول جلسة التصوير.");
            toggle("camera_smart_processing", "Adaptive hardware photo processing",
                    "التحسين التلقائي للصور بواسطة عتاد الكاميرا",
                    "Optional HDR scene, high-quality noise reduction and sharpening "
                    + "only when Camera2 advertises support. Not a generative AI model.",
                    "HDR وتقليل الضجيج وتحسين الحواف فقط عند دعم عتاد Camera2. "
                    + "هذه معالجة تصوير وليست نموذج ذكاء اصطناعي توليدي.");
            toggle("camera_zoom_bar", "Zoom slider", "شريط التكبير",
                    "Show a precise zoom slider below camera controls",
                    "إظهار شريط تكبير دقيق أسفل أزرار الكاميرا");
            header("Camera2 video recorder", "مسجل الفيديو Camera2");
            toggle("video_stabilize", "Video stabilization (EIS)", "تثبيت الفيديو الإلكتروني",
                    "Use Camera2 EIS only if recording hardware advertises support",
                    "يستخدم EIS فقط على العدسات الداعمة في Camera2");
            toggle("video_pip", "Picture-in-picture while recording", "عرض PiP أثناء تسجيل الفيديو",
                    "Keep video recording in a visible Android PiP window (Android 8+)",
                    "متابعة التسجيل أثناء عرض نافذة Android العائمة (Android 8+)");
            header("Recording frame rate", "معدل إطارات التسجيل");
            videoFpsChoice(24);
            videoFpsChoice(30);
            videoFpsChoice(60);
            note("FPS is negotiated with Camera2 hardware and the H.264 encoder. "
                    + "Unsupported combinations fail safely; no FPS is invented. "
                    + "Video messages/PiP calls are separate Telegram features.",
                    "تُراجع قدرة Camera2 ومرمز H.264 قبل التسجيل. "
                    + "لا يُفترض دعم FPS غير متاح؛ ورسائل الفيديو ومكالمات PiP ميزات مستقلة.");
        }
    }
}
