package org.telegram.ui;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.telegram.messenger.LocaleController;
import org.telegram.messenger.SharedConfig;
import org.telegram.messenger.NotificationsController;
import org.telegram.messenger.UserConfig;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.NabdhCompactSettings;
import org.telegram.ui.Components.NabdhToolUi;
import org.telegram.ui.Components.NabdhAppearancePrefs;

/**
 * Functional locally-applied selectors; never advertises undelivered third-party
 * emoji assets or global Telegram icon packs. Integrates native shared config.
 */
public final class NabdhAppearancePickerActivity extends Activity {
    public static final String EXTRA_KIND = "kind";
    public static final String ICON_PACKS = "icons";
    public static final String EMOJI_SETS = "emoji";
    public static final String NOTIFICATION_ICON = "notifications";

    private String kind;
    private LinearLayout items;

    private String local(String en, String ar) {
        return LocaleController.isRTL ? ar : en;
    }

    private int dp(int n) {
        return (int) (getResources().getDisplayMetrics().density * n + .5f);
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        kind = getIntent().getStringExtra(EXTRA_KIND);
        if (!ICON_PACKS.equals(kind) && !EMOJI_SETS.equals(kind)
                && !NOTIFICATION_ICON.equals(kind)) {
            finish();
            return;
        }
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        items = new LinearLayout(this);
        items.setOrientation(LinearLayout.VERTICAL);
        items.setPadding(dp(16), dp(10), dp(16), dp(28));
        items.setLayoutDirection(LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        items.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));
        scroll.addView(items);
        String title = ICON_PACKS.equals(kind)
                ? local("Icon style", "حزم الأيقونات")
                : EMOJI_SETS.equals(kind)
                    ? local("Emoji set", "حزمة الإيموجي")
                    : local("Notification icon", "أيقونة الإشعارات");
        NabdhToolUi.install(this, scroll, title);
        render();
    }

    private TextView note(String text) {
        TextView caption = new TextView(this);
        caption.setText(text);
        caption.setTextSize(13);
        caption.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        caption.setPadding(dp(5), dp(4), dp(5), dp(16));
        caption.setGravity(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT);
        return caption;
    }

    private void selection(String title, String subtitle, int icon,
                           boolean active, Runnable action) {
        NabdhCompactSettings.row(this, items,
                (active ? "✓  " : "") + title, subtitle, icon,
                () -> {
                    action.run();
                    render();
                });
    }

    private void previewIcons() {
        LinearLayout preview = new LinearLayout(this);
        preview.setOrientation(LinearLayout.HORIZONTAL);
        preview.setGravity(Gravity.CENTER);
        preview.setPadding(dp(6), dp(12), dp(6), dp(12));
        preview.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        int[] resources = {R.drawable.nabdh_tool_browser, R.drawable.nabdh_tool_camera,
                R.drawable.nabdh_tool_feed, R.drawable.nabdh_tool_lock,
                R.drawable.settings_language, R.drawable.settings_privacy};
        for (int original : resources) {
            ImageView image = new ImageView(this);
            image.setImageResource(NabdhAppearancePrefs.icon(this, original));
            image.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(25), 1);
            lp.setMarginStart(dp(3));
            lp.setMarginEnd(dp(3));
            preview.addView(image, lp);
        }
        items.addView(preview);
    }

    private void render() {
        items.removeAllViews();
        if (ICON_PACKS.equals(kind)) {
            items.addView(note(local(
                    "Icon selection applies to NabdhGram settings and tools. "
                    + "Telegram's own navigation icons remain unchanged.",
                    "تُطبّق حزمة الأيقونات على إعدادات نبض جرام وأدواته. "
                    + "أيقونات التنقل الأصلية في Telegram لا تتغير.")));
            boolean duotone = NabdhAppearancePrefs.isDuotone(this);
            NabdhCompactSettings.header(this, items,
                    local("Available icon styles", "أنماط الأيقونات المتاحة"));
            selection(local("Classic", "الكلاسيكية"),
                    local("Original outlined symbols", "أيقونات الحدود الأصلية"),
                    R.drawable.nabdh_tool_browser, !duotone,
                    () -> NabdhAppearancePrefs.setDuotone(this, false));
            selection(local("Nabdh Duotone", "نبض ثنائي اللون"),
                    local("Custom soft-filled symbols for NabdhGram",
                            "رموز خاصة بنبض جرام بتصميم ممتلئ وهادئ"),
                    R.drawable.nabdh_alt_browser, duotone,
                    () -> NabdhAppearancePrefs.setDuotone(this, true));
            previewIcons();
        } else if (EMOJI_SETS.equals(kind)) {
            items.addView(note(local("Only supported emoji engines are offered. "
                    + "Additional downloadable packs need verified licensed assets.",
                    "تظهر محركات الإيموجي المدعومة فعليًا فقط. "
                    + "الحزم القابلة للتنزيل تتطلب ملفات مرخّصة ومتحققًا منها.")));
            NabdhCompactSettings.header(this, items,
                    local("Emoji rendering", "عرض الإيموجي"));
            selection(local("Telegram", "Telegram"),
                    local("Telegram's bundled emojis · 😀 😉 😌 😨",
                            "الإيموجي المدمج في Telegram · 😀 😉 😌 😨"),
                    R.drawable.settings_chat, !SharedConfig.useSystemEmoji,
                    () -> applyEmoji(false));
            String manufacturer = android.os.Build.MANUFACTURER == null ? ""
                    : android.os.Build.MANUFACTURER.toLowerCase(java.util.Locale.ROOT);
            String vendor = manufacturer.contains("samsung") ? "Samsung"
                    : manufacturer.contains("google") ? "Google"
                    : local("Device", "الجهاز");
            selection(local("Android system · ", "نظام Android · ") + vendor,
                    local("Uses the emoji font actually installed on this device · 😀 😉 😌 😨",
                            "يستخدم خط الإيموجي المثبت فعليًا على الجهاز · 😀 😉 😌 😨"),
                    R.drawable.settings_language, SharedConfig.useSystemEmoji,
                    () -> applyEmoji(true));
        } else {
            items.addView(note(local(
                    "Status bar icons are monochrome. They are separate from the app launcher icon.",
                    "أيقونات شريط الحالة أحادية اللون، ومستقلة عن أيقونة تشغيل التطبيق.")));
            boolean nabdh = NabdhAppearancePrefs.useNabdhNotification(this);
            NabdhCompactSettings.header(this, items,
                    local("Status bar icon", "أيقونة شريط الحالة"));
            selection(local("Classic", "الكلاسيكية"),
                    local("Original Telegram-compatible status icon", "أيقونة الإشعارات الأصلية"),
                    R.drawable.notification, !nabdh,
                    () -> applyNotification(false));
            selection("NabdhGram",
                    local("Minimal NabdhGram monochrome emblem",
                            "رمز نبض جرام أحادي اللون"),
                    R.drawable.nabdh_notification_symbol, nabdh,
                    () -> applyNotification(true));
        }
    }

    private void applyEmoji(boolean system) {
        if (SharedConfig.useSystemEmoji == system) return;
        SharedConfig.useSystemEmoji = system;
        SharedConfig.saveConfig();
        org.telegram.messenger.NotificationCenter.getGlobalInstance().postNotificationName(
                org.telegram.messenger.NotificationCenter.didSetNewTheme, false, false);
    }

    private void applyNotification(boolean nabdh) {
        NabdhAppearancePrefs.setNabdhNotification(this, nabdh);
        try {
            // The project already exposes a local, read-preserving notifier refresh.
            NotificationsController.getInstance(UserConfig.selectedAccount)
                    .nabdhRefreshLockedNotifications();
        } catch (RuntimeException ignored) {
            // The setting still applies when a notification is posted later.
        }
    }
}
