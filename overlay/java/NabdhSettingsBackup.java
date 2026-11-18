package org.telegram.ui.Components;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * SAF-only, explicit export/import of a fixed non-sensitive preference allowlist.
 * Never exports Telegram sessions/keys, chat data, AI feedback or model consent.
 */
public final class NabdhSettingsBackup {
    private static final int SCHEMA_VERSION = 1;
    private static final int MAX_BYTES = 16384;
    private NabdhSettingsBackup() {}

    private static SharedPreferences appearance(Context c) {
        return c.getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE);
    }
    public static Intent exportIntent() {
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/json");
        intent.putExtra(Intent.EXTRA_TITLE, "NabdhGram-settings.json");
        return intent;
    }
    public static Intent importIntent() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/json");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        return intent;
    }
    private static JSONObject build(Context c) throws JSONException {
        SharedPreferences a = appearance(c);
        JSONObject body = new JSONObject();
        body.put("font_family", a.getString("font_family", "system-default"));
        body.put("ui_scale_percent", a.getInt("ui_scale_percent", 100));
        body.put("font_bold", a.getBoolean("font_bold", false));
        body.put("bubble_glass_style", a.getInt("bubble_glass_style", 1));
        body.put("lens_enabled", a.getBoolean("lens_enabled", true));
        body.put("monet_enabled", a.getBoolean("monet_enabled", false));
        body.put("voice_boost_enabled", c.getSharedPreferences(
                "nabdhgram_audio", Context.MODE_PRIVATE).getBoolean("voice_boost_enabled", false));
        body.put("report_language", NabdhAiPreferenceStore.outputLanguage(c));
        return new JSONObject().put("format", "NabdhGram-settings")
                .put("version", SCHEMA_VERSION).put("settings", body);
    }
    public static void write(Context c, Uri uri) throws IOException, JSONException {
        byte[] bytes = build(c).toString(2).getBytes(StandardCharsets.UTF_8);
        if (bytes.length > MAX_BYTES) throw new IOException("Settings backup unexpectedly large");
        try (OutputStream output = c.getContentResolver().openOutputStream(uri, "w")) {
            if (output == null) throw new IOException("Cannot write selected destination");
            output.write(bytes);
            output.flush();
        }
    }
    public static String read(Context c, Uri uri) throws IOException {
        try (InputStream stream = c.getContentResolver().openInputStream(uri)) {
            if (stream == null) throw new IOException("Cannot open selected settings backup");
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            byte[] buffer = new byte[1024];
            int n;
            while ((n = stream.read(buffer)) != -1) {
                if (output.size() + n > MAX_BYTES) throw new IOException("Settings file exceeds 16 KiB");
                output.write(buffer, 0, n);
            }
            return output.toString("UTF-8");
        }
    }
    private static final class Values {
        String font;
        String language;
        int uiScale;
        int glass;
        boolean bold, lens, monet, voice;
    }
    private static Values checked(String raw) throws JSONException {
        JSONObject object = new JSONObject(raw);
        if (!"NabdhGram-settings".equals(object.getString("format"))
                || object.getInt("version") != SCHEMA_VERSION)
            throw new JSONException("Unsupported settings backup version");
        JSONObject s = object.getJSONObject("settings");
        Values v = new Values();
        v.font = s.getString("font_family");
        v.language = s.getString("report_language");
        v.uiScale = s.getInt("ui_scale_percent");
        v.glass = s.getInt("bubble_glass_style");
        v.bold = s.getBoolean("font_bold");
        v.lens = s.getBoolean("lens_enabled");
        v.monet = s.getBoolean("monet_enabled");
        v.voice = s.getBoolean("voice_boost_enabled");
        if (!Arrays.asList("system-default", "readex-pro", "vazirmatn",
                "noto-sans-arabic", "tajawal", "rubik", "sans-serif", "serif").contains(v.font)
                || (!"auto".equals(v.language) && !"ar".equals(v.language)
                && !"en".equals(v.language))
                || v.uiScale < 85 || v.uiScale > 115
                || v.glass < 0 || v.glass > 2)
            throw new JSONException("Invalid or unsupported preference values");
        return v;
    }
    public static String preview(String raw, boolean arabic) throws JSONException {
        Values v = checked(raw);
        return (arabic ? "ستُستعاد إعدادات نبض جرام التالية فقط:\n" :
                "Only these NabdhGram settings will be restored:\n")
                + (arabic ? "الخط: " : "Font: ") + v.font + "\n"
                + (arabic ? "حجم الواجهة: " : "UI scale: ") + v.uiScale + "%\n"
                + (arabic ? "ثيم Glass: " : "Glass preset: ") + v.glass + "\n"
                + (arabic ? "تفضيل لغة النتائج: " : "Report language: ") + v.language + "\n\n"
                + (arabic ? "لن تُستعاد بيانات Telegram أو الجلسات أو الرسائل أو موافقات الذكاء.\n"
                          : "Telegram sessions, messages and AI consent are never imported.\n")
                + (arabic ? "قد تحتاج إلى إعادة فتح الإعدادات لرؤية التغييرات."
                          : "Reopen settings if appearance changes are not immediately visible.");
    }
    public static void restore(Context c, String raw) throws JSONException {
        Values v = checked(raw); // validate all fields BEFORE touching any preference
        SharedPreferences.Editor a = appearance(c).edit();
        a.putString("font_family", v.font)
         .putInt("ui_scale_percent", v.uiScale)
         .putBoolean("font_bold", v.bold)
         .putBoolean("lens_enabled", v.lens)
         .putBoolean("monet_enabled", v.monet && NabdhDynamicAccent.available(c));
        if (!a.commit()) throw new JSONException("Failed to save appearance settings");
        NabdhGlassStyle.choose(c, v.glass); // keep its in-memory cache in sync
        c.getSharedPreferences("nabdhgram_audio", Context.MODE_PRIVATE)
         .edit().putBoolean("voice_boost_enabled", v.voice).apply();
        NabdhAiPreferenceStore.setOutputLanguage(c, v.language); // never enables AI consent
        org.telegram.messenger.AndroidUtilities.mediumTypeface = null;
        org.telegram.ui.ActionBar.Theme.createChatResources(c, true);
        if (org.telegram.ui.LaunchActivity.instance != null)
            org.telegram.ui.LaunchActivity.instance.nabdhRefreshAllFonts();
    }
}
