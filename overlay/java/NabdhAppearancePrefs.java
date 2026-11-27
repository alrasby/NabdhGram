package org.telegram.ui.Components;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.R;

/** Private, theme-aware first-party icon styles. Telegram navigation is untouched. */
public final class NabdhAppearancePrefs {
    private static final String STORE = "nabdh_appearance_packs_v1";
    public static final String CLASSIC = "classic";
    public static final String DUOTONE = "duotone";
    public static final String LINEAR = "linear";
    public static final String BOLD = "bold";
    // Independent from Telegram themeconfig and from icon_style.
    private static final String UI_STYLE = "ui_style_v2";
    public static final int UI_CLASSIC = 0, UI_MATERIAL = 1, UI_GLASS = 2, UI_HYBRID = 3;
    private static volatile int cachedUiStyle = -1;
    public static int uiStyle() {
        int value = cachedUiStyle;
        if (value >= 0) return value;
        Context context = org.telegram.messenger.ApplicationLoader.applicationContext;
        if (context == null) return UI_CLASSIC;
        value = context.getSharedPreferences(STORE, Context.MODE_PRIVATE)
                .getInt(UI_STYLE, UI_CLASSIC);
        cachedUiStyle = value >= 0 && value <= UI_HYBRID ? value : UI_CLASSIC;
        return cachedUiStyle;
    }
    public static void setUiStyle(Context context, int style) {
        if (style < 0 || style > 3) throw new IllegalArgumentException("Invalid UI style");
        context.getSharedPreferences(STORE, Context.MODE_PRIVATE).edit().putInt(UI_STYLE, style).apply();
        cachedUiStyle = style;
    }
    public static boolean glassSurface() { return uiStyle() >= UI_GLASS; }
    public static int surfaceRadius() {
        switch (uiStyle()) {
            case UI_CLASSIC: return 0;
            case UI_MATERIAL: return 16;
            case UI_GLASS: return 24;
            default: return 20;
        }
    }
    private NabdhAppearancePrefs() {}

    public static String iconStyle(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(STORE, Context.MODE_PRIVATE);
        String style = prefs.getString("icon_style", null);
        if (style == null) {
            // Users of V1 already selected Nabdh Duotone via this boolean.
            return prefs.getBoolean("nabdh_duotone", false) ? DUOTONE : CLASSIC;
        }
        return isValid(style) ? style : CLASSIC;
    }

    private static boolean isValid(String style) {
        return CLASSIC.equals(style) || DUOTONE.equals(style)
                || LINEAR.equals(style) || BOLD.equals(style);
    }

    public static void setIconStyle(Context context, String style) {
        if (!isValid(style)) throw new IllegalArgumentException("Invalid icon pack");
        context.getSharedPreferences(STORE, Context.MODE_PRIVATE).edit()
                .putString("icon_style", style)
                .putBoolean("nabdh_duotone", DUOTONE.equals(style)).apply();
    }

    /** Backward compatibility with V1 preference code and existing user installs. */
    public static boolean isDuotone(Context context) {
        return DUOTONE.equals(iconStyle(context));
    }
    public static void setDuotone(Context context, boolean on) {
        setIconStyle(context, on ? DUOTONE : CLASSIC);
    }

    public static boolean useNabdhNotification(Context context) {
        return context.getSharedPreferences(STORE, Context.MODE_PRIVATE)
                .getBoolean("nabdh_notification", false);
    }
    public static void setNabdhNotification(Context context, boolean selected) {
        context.getSharedPreferences(STORE, Context.MODE_PRIVATE).edit()
                .putBoolean("nabdh_notification", selected).apply();
    }
    public static int notificationIcon(Context context) {
        return useNabdhNotification(context)
                ? R.drawable.nabdh_notification_symbol : R.drawable.notification;
    }

    /** Only NabdhGram-owned settings/tool icons; retain Telegram native icons. */
    public static int icon(Context context, int original) {
        String style = iconStyle(context);
        if (CLASSIC.equals(style)) return original;
        if (original == R.drawable.settings_privacy) return choose(style,
                R.drawable.nabdh_alt_shield, R.drawable.nabdh_linear_shield, R.drawable.nabdh_bold_shield);
        if (original == R.drawable.settings_devices) return choose(style,
                R.drawable.nabdh_alt_privacy, R.drawable.nabdh_linear_privacy, R.drawable.nabdh_bold_privacy);
        if (original == R.drawable.settings_folders) return choose(style,
                R.drawable.nabdh_alt_productivity, R.drawable.nabdh_linear_productivity, R.drawable.nabdh_bold_productivity);
        if (original == R.drawable.settings_language) return choose(style,
                R.drawable.nabdh_alt_language, R.drawable.nabdh_linear_language, R.drawable.nabdh_bold_language);
        if (original == R.drawable.settings_data) return choose(style,
                R.drawable.nabdh_alt_network, R.drawable.nabdh_linear_network, R.drawable.nabdh_bold_network);
        if (original == R.drawable.settings_features) return choose(style,
                R.drawable.nabdh_alt_ai, R.drawable.nabdh_linear_ai, R.drawable.nabdh_bold_ai);
        if (original == R.drawable.nabdh_tool_browser) return choose(style,
                R.drawable.nabdh_alt_browser, R.drawable.nabdh_linear_browser, R.drawable.nabdh_bold_browser);
        if (original == R.drawable.nabdh_tool_camera) return choose(style,
                R.drawable.nabdh_alt_camera, R.drawable.nabdh_linear_camera, R.drawable.nabdh_bold_camera);
        if (original == R.drawable.nabdh_tool_feed) return choose(style,
                R.drawable.nabdh_alt_feed, R.drawable.nabdh_linear_feed, R.drawable.nabdh_bold_feed);
        if (original == R.drawable.nabdh_tool_lock) return choose(style,
                R.drawable.nabdh_alt_lock, R.drawable.nabdh_linear_lock, R.drawable.nabdh_bold_lock);
        if (original == R.drawable.nabdh_tool_swipe) return choose(style,
                R.drawable.nabdh_alt_swipe, R.drawable.nabdh_linear_swipe, R.drawable.nabdh_bold_swipe);
        return original;
    }

    private static int choose(String style, int duotone, int linear, int bold) {
        return LINEAR.equals(style) ? linear : BOLD.equals(style) ? bold : duotone;
    }
}
