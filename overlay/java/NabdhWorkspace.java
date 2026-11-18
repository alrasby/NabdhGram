package org.telegram.ui.Components;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.List;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Explicitly user-saved, local-only encrypted draft notes.
 *
 * AndroidKeyStore AES-256-GCM. NO fallback to plaintext, no network, no
 * background message scanning, no fake Telegram synchronization. User must
 * choose to save. Not valid for secret-chat auto-capture; those chats are
 * excluded at the composer entrypoint. Keystore errors never silently wipe.
 */
public final class NabdhWorkspace {
    private static final String FILE = "nabdh_workspace_encrypted_v1";
    private static final String DATA = "entries";
    private static final String ALIAS = "nabdhgram.workspace.v1.aesgcm";
    private static final int LIMIT = 40;
    private static final int MAX_ENTRY = 1600;
    private static final int IV_LENGTH = 12;

    public static final class Note {
        public final String text;
        public final String source;
        public final long createdAt;
        Note(String text, String source, long createdAt) {
            this.text = text;
            this.source = source;
            this.createdAt = createdAt;
        }
    }

    private NabdhWorkspace() { }

    private static SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (store.containsAlias(ALIAS)) {
            java.security.Key existing = store.getKey(ALIAS, null);
            if (!(existing instanceof SecretKey)) {
                throw new java.security.GeneralSecurityException("Workspace key is not a secret key");
            }
            return (SecretKey) existing;
        }
        KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .setRandomizedEncryptionRequired(true)
                .build());
        return generator.generateKey();
    }

    private static String encode(Context context, String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key());
        byte[] iv = cipher.getIV();
        if (iv == null || iv.length != IV_LENGTH) {
            throw new java.security.GeneralSecurityException("Unexpected AES-GCM IV");
        }
        byte[] encrypted = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));
        return Base64.encodeToString(iv, Base64.NO_WRAP) + "."
                + Base64.encodeToString(encrypted, Base64.NO_WRAP);
    }

    private static String decode(String stored) throws Exception {
        int dot = stored.indexOf('.');
        if (dot < 0) throw new java.security.GeneralSecurityException("Encrypted workspace envelope missing");
        byte[] iv = Base64.decode(stored.substring(0, dot), Base64.NO_WRAP);
        byte[] ciphertext = Base64.decode(stored.substring(dot + 1), Base64.NO_WRAP);
        if (iv.length != IV_LENGTH || ciphertext.length < 16) {
            throw new java.security.GeneralSecurityException("Encrypted workspace data malformed");
        }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, iv));
        return new String(cipher.doFinal(ciphertext), StandardCharsets.UTF_8);
    }

    private static JSONArray readJson(Context context) throws Exception {
        SharedPreferences prefs = context.getSharedPreferences(FILE, Context.MODE_PRIVATE);
        String stored = prefs.getString(DATA, null);
        if (stored == null) return new JSONArray();
        return new JSONArray(decode(stored));
    }

    private static void write(Context context, JSONArray notes) throws Exception {
        String envelope = encode(context, notes.toString());
        boolean saved = context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
                .edit().putString(DATA, envelope).commit();
        if (!saved) throw new java.io.IOException("Workspace persistence failed");
    }

    public static int save(Context context, CharSequence text, String source) throws Exception {
        String value = NabdhV1Engine.bounded(text);
        if (value.isEmpty()) throw new IllegalArgumentException("Empty note");
        if (value.length() > MAX_ENTRY) value = value.substring(0, MAX_ENTRY);
        JSONArray old = readJson(context);
        JSONArray next = new JSONArray();
        JSONObject fresh = new JSONObject();
        fresh.put("text", value);
        fresh.put("source", source == null ? "manual" : source);
        fresh.put("created", System.currentTimeMillis());
        next.put(fresh);
        for (int i = 0; i < old.length() && i < LIMIT - 1; i++) {
            JSONObject entry = old.optJSONObject(i);
            if (entry != null) next.put(entry);
        }
        write(context, next);
        return next.length();
    }

    public static List<Note> list(Context context) throws Exception {
        JSONArray notes = readJson(context);
        List<Note> out = new ArrayList<>();
        for (int i = 0; i < Math.min(notes.length(), LIMIT); i++) {
            JSONObject entry = notes.optJSONObject(i);
            if (entry != null) {
                out.add(new Note(entry.optString("text"), entry.optString("source"),
                        entry.optLong("created")));
            }
        }
        return out;
    }

    public static void delete(Context context, int index) throws Exception {
        JSONArray entries = readJson(context);
        if (index < 0 || index >= entries.length()) throw new IllegalArgumentException("Invalid note");
        JSONArray remaining = new JSONArray();
        for (int i = 0; i < entries.length(); i++) {
            if (i != index) remaining.put(entries.get(i));
        }
        write(context, remaining);
    }

    private static String label(boolean ar, String arText, String enText) {
        return ar ? arText : enText;
    }

    private static void error(Context context, boolean ar) {
        new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                .setTitle(label(ar, "تعذر فتح المساحة المحلية", "Local workspace unavailable"))
                .setMessage(label(ar,
                        "تعذر فك تشفير الملاحظات أو حفظها بأمان. لم تُحذف البيانات أو تُرسل.",
                        "Encrypted notes could not be opened or saved. No data was cleared or uploaded."))
                .setPositiveButton(label(ar, "موافق", "OK"), null).show();
    }

    public static boolean saveWithFeedback(Context context, CharSequence text, boolean ar) {
        try {
            int n = save(context, text, "manual-draft");
            new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                    .setTitle(label(ar, "حُفظت الملاحظة محليًا", "Note saved locally"))
                    .setMessage(label(ar, "الملاحظات مشفرة على هذا الجهاز. العدد: ",
                            "Encrypted on this device. Notes: ") + n)
                    .setPositiveButton(label(ar, "موافق", "OK"), null).show();
            return true;
        } catch (Exception error) {
            error(context, ar);
            return false;
        }
    }

    public static void show(Context context, boolean ar) {
        final List<Note> notes;
        try {
            notes = list(context);
        } catch (Exception e) {
            error(context, ar);
            return;
        }
        if (notes.isEmpty()) {
            new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                .setTitle(label(ar, "مساحة الرسائل", "Message Workspace"))
                .setMessage(label(ar, "لا توجد ملاحظات محفوظة محليًا.",
                        "No locally saved notes yet."))
                .setPositiveButton(label(ar, "إغلاق", "Close"), null).show();
            return;
        }
        String[] titles = new String[notes.size()];
        for (int i = 0; i < notes.size(); i++) {
            String v = notes.get(i).text.replace('\n', ' ').trim();
            titles[i] = (i + 1) + ". " + (v.length() > 65 ? v.substring(0, 65) + "…" : v);
        }
        new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
            .setTitle(label(ar, "ملاحظات محلية مشفرة", "Encrypted local notes"))
            .setItems(titles, (dialog, selected) -> {
                Note note = notes.get(selected);
                new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                    .setTitle(label(ar, "ملاحظة محفوظة", "Saved note"))
                    .setMessage(note.text)
                    .setPositiveButton(label(ar, "نسخ", "Copy"), (d, action) -> {
                        ClipboardManager clipboard = (ClipboardManager)
                                context.getSystemService(Context.CLIPBOARD_SERVICE);
                        if (clipboard != null) clipboard.setPrimaryClip(
                                ClipData.newPlainText("Nabdh local note", note.text));
                    })
                    .setNeutralButton(label(ar, "حذف", "Delete"), (d, action) ->
                        new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                            .setTitle(label(ar, "حذف هذه الملاحظة؟", "Delete this note?"))
                            .setMessage(label(ar, "سيُحذف النص المحفوظ محليًا فقط.",
                                    "Only the local saved note will be deleted."))
                            .setNegativeButton(label(ar, "إلغاء", "Cancel"), null)
                            .setPositiveButton(label(ar, "حذف", "Delete"), (confirm, which) -> {
                                try {
                                    delete(context, selected);
                                } catch (Exception error) {
                                    error(context, ar);
                                }
                            }).show()
                    )
                    .setNegativeButton(label(ar, "إغلاق", "Close"), null)
                    .show();
            })
            .setNegativeButton(label(ar, "إغلاق", "Close"), null)
            .show();
    }
}
