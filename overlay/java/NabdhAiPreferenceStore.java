package org.telegram.ui.Components;

import android.content.Context;
import android.content.SharedPreferences;

/** Explicit preferences only. No chat readers, listeners, network, model training or tracking. */
public final class NabdhAiPreferenceStore {
    private static final String FILE = "nabdh_ai_explicit_v1";
    private NabdhAiPreferenceStore() {}
    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    public static boolean rememberEnabled(Context context) {
        return prefs(context).getBoolean("remember_explicit_feedback", false);
    }
    public static void setRememberEnabled(Context context, boolean enabled) {
        SharedPreferences.Editor edit = prefs(context).edit();
        edit.putBoolean("remember_explicit_feedback", enabled);
        if (!enabled) edit.remove("helpful_focus").remove("helpful_recap");
        edit.apply();
    }
    /** Only manually chosen report language; does not override Telegram UI language. */
    public static String outputLanguage(Context context) {
        String value = prefs(context).getString("report_language", "auto");
        return "ar".equals(value) || "en".equals(value) ? value : "auto";
    }
    public static void setOutputLanguage(Context context, String language) {
        if (!"auto".equals(language) && !"ar".equals(language) && !"en".equals(language))
            throw new IllegalArgumentException("Unsupported report language");
        prefs(context).edit().putString("report_language", language).apply();
    }
    public static boolean outputArabic(Context context, boolean fallback) {
        String selection = outputLanguage(context);
        return "ar".equals(selection) || ("auto".equals(selection) && fallback);
    }
    /** A user taps 'Useful'; never stores text, chat ID, sender or model prompts. */
    public static void explicitlyHelpful(Context context, int mode) {
        if (!rememberEnabled(context) || (mode != 0 && mode != 1)) return;
        String key = mode == 0 ? "helpful_focus" : "helpful_recap";
        SharedPreferences settings = prefs(context);
        int current = settings.getInt(key, 0);
        if (current < 10000) settings.edit().putInt(key, current + 1).apply();
    }
    public static void clear(Context context) {
        prefs(context).edit().clear().commit();
    }
}
