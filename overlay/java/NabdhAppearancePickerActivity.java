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
import org.telegram.messenger.NabdhEmojiPacks;
import org.telegram.messenger.Emoji;
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
    private String emojiAvailabilityError;

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
            String style = NabdhAppearancePrefs.iconStyle(this);
            NabdhCompactSettings.header(this, items,
                    local("Available icon styles", "أنماط الأيقونات المتاحة"));
            selection(local("Classic", "الكلاسيكية"),
                    local("Telegram-inspired original symbols", "الرموز الأصلية المتناسقة مع Telegram"),
                    R.drawable.nabdh_tool_browser, NabdhAppearancePrefs.CLASSIC.equals(style),
                    () -> NabdhAppearancePrefs.setIconStyle(this, NabdhAppearancePrefs.CLASSIC));
            selection(local("Nabdh Duotone", "نبض ثنائية اللون"),
                    local("Soft-filled Glass symbols", "أيقونات ناعمة بلمسات Glass"),
                    R.drawable.nabdh_alt_browser, NabdhAppearancePrefs.DUOTONE.equals(style),
                    () -> NabdhAppearancePrefs.setIconStyle(this, NabdhAppearancePrefs.DUOTONE));
            selection(local("Nabdh Linear", "نبض الخطية"),
                    local("Fine geometric outlines", "خطوط هندسية دقيقة وعصرية"),
                    R.drawable.nabdh_linear_browser, NabdhAppearancePrefs.LINEAR.equals(style),
                    () -> NabdhAppearancePrefs.setIconStyle(this, NabdhAppearancePrefs.LINEAR));
            selection(local("Nabdh Bold", "نبض المصمتة"),
                    local("Strong, softly filled geometric symbols",
                            "رموز هندسية بارزة بتعبئة ناعمة"),
                    R.drawable.nabdh_bold_browser, NabdhAppearancePrefs.BOLD.equals(style),
                    () -> NabdhAppearancePrefs.setIconStyle(this, NabdhAppearancePrefs.BOLD));
            previewIcons();
        } else if (EMOJI_SETS.equals(kind)) {
            items.addView(note(local(
                    "Twemoji 17.0.3 is included inside NabdhGram. Switching between "
                    + "Telegram, Twemoji and Android uses no network or additional downloads. "
                    + "Third-party Twemoji artwork is licensed CC BY 4.0.",
                    "حزمة Twemoji 17.0.3 مدمجة بالكامل داخل نبض جرام. "
                    + "التبديل بين Telegram وTwemoji وAndroid لا يحتاج إنترنت أو تنزيلات. "
                    + "ترخيص رسومات Twemoji هو CC BY 4.0.")));
            if (emojiAvailabilityError != null) {
                items.addView(note(emojiAvailabilityError));
            }
            String chosen = NabdhEmojiPacks.selected();
            NabdhCompactSettings.header(this, items,
                    local("Emoji artwork", "رسومات الإيموجي"));
            selection("Telegram",
                    local("Original bundled Telegram emoji", "إيموجي Telegram الأصلي المدمج"),
                    R.drawable.settings_chat, NabdhEmojiPacks.TELEGRAM.equals(chosen),
                    () -> applyEmojiPack(NabdhEmojiPacks.TELEGRAM));
            selection("Twemoji 17",
                    local("Complete bundled Twemoji 17 artwork · CC BY 4.0",
                            "رسومات Twemoji 17 المدمجة · ترخيص CC BY 4.0"),
                    R.drawable.settings_language, NabdhEmojiPacks.TWEMOJI.equals(chosen),
                    () -> applyEmojiPack(NabdhEmojiPacks.TWEMOJI));
            selection(local("Android system", "نظام Android"),
                    local("Uses device emoji font", "يستخدم خط الإيموجي المثبت على جهازك"),
                    R.drawable.settings_language, NabdhEmojiPacks.SYSTEM.equals(chosen),
                    () -> applyEmojiPack(NabdhEmojiPacks.SYSTEM));
            TextView samples = new TextView(this);
            samples.setTextSize(29);
            samples.setGravity(Gravity.CENTER);
            samples.setPadding(dp(6), dp(18), dp(6), dp(10));
            samples.setText(Emoji.replaceEmoji("😀 😍 😂 ❤️ 👍 🇴🇲 🐱 🌷",
                    samples.getPaint().getFontMetricsInt(), true));
            items.addView(samples);
            items.addView(note(local(
                    "Graphics © Twemoji contributors, CC BY 4.0. "
                    + "Source: jdecked/twemoji v17.0.3. Files are bundled unmodified; "
                    + "unavailable variants retain Telegram's native artwork.",
                    "الرسومات © مساهمو Twemoji بترخيص CC BY 4.0. "
                    + "المصدر: jdecked/twemoji v17.0.3. الصور مدمجة دون تعديل، "
                    + "والرموز غير المتوفرة تستخدم رسم Telegram الأصلي.")));
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

    private void applyEmojiPack(String pack) {
        if (NabdhEmojiPacks.selected().equals(pack)) return;
        if (!NabdhEmojiPacks.isReady(pack)) {
            emojiAvailabilityError = local(
                    "Bundled Twemoji assets are missing in this build.",
                    "ملفات Twemoji المدمجة غير متوفرة في هذا البناء.");
            return;
        }
        emojiAvailabilityError = null;
        NabdhEmojiPacks.choose(this, pack);
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
