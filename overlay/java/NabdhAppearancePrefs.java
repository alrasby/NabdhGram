package org.telegram.ui.Components;

import android.content.Context;
import android.content.SharedPreferences;
import org.telegram.messenger.R;

/** Small, strictly local appearance prefs. No remote or background work. */
public final class NabdhAppearancePrefs {
    private static final String STORE = "nabdh_appearance_packs_v1";
    private NabdhAppearancePrefs() {}

    public static boolean isDuotone(Context context) {
        return context.getSharedPreferences(STORE, Context.MODE_PRIVATE)
                .getBoolean("nabdh_duotone", false);
    }

    public static void setDuotone(Context context, boolean selected) {
        context.getSharedPreferences(STORE, Context.MODE_PRIVATE).edit()
                .putBoolean("nabdh_duotone", selected).apply();
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

    /** Actual drawable swaps only for the icons that NabdhGram owns. */
    public static int icon(Context context, int original) {
        if (!isDuotone(context)) return original;
        if (original == R.drawable.settings_privacy) return R.drawable.nabdh_alt_shield;
        if (original == R.drawable.settings_devices) return R.drawable.nabdh_alt_privacy;
        if (original == R.drawable.settings_folders) return R.drawable.nabdh_alt_productivity;
        if (original == R.drawable.settings_language) return R.drawable.nabdh_alt_language;
        if (original == R.drawable.settings_data) return R.drawable.nabdh_alt_network;
        if (original == R.drawable.settings_features) return R.drawable.nabdh_alt_ai;
        if (original == R.drawable.nabdh_tool_browser) return R.drawable.nabdh_alt_browser;
        if (original == R.drawable.nabdh_tool_camera) return R.drawable.nabdh_alt_camera;
        if (original == R.drawable.nabdh_tool_feed) return R.drawable.nabdh_alt_feed;
        if (original == R.drawable.nabdh_tool_lock) return R.drawable.nabdh_alt_lock;
        if (original == R.drawable.nabdh_tool_swipe) return R.drawable.nabdh_alt_swipe;
        return original;
    }
}
