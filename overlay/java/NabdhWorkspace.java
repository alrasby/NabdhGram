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
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.ActionBar.BaseFragment;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Explicitly user-saved, local-only encrypted notes and tasks.
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
    static final int MAX_ENTRY = 1600;
    private static final int IV_LENGTH = 12;

    public static final class Note {
        public final String text;
        public final String source;
        public final long createdAt;
        final String id;
        final int account;
        final long ownerId;
        final long dialogId;
        final int messageId;
        final boolean task;
        final boolean done;

        Note(JSONObject entry) {
            text = entry.optString("text");
            source = entry.optString("source");
            createdAt = entry.optLong("created");
            id = entry.optString("id");
            account = entry.optInt("account", -1);
            ownerId = entry.optLong("owner");
            dialogId = entry.optLong("dialog");
            messageId = entry.optInt("message");
            task = entry.optBoolean("task");
            done = entry.optBoolean("done");
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
        return save(context, text, source, -1, 0, 0, 0, false);
    }

    static synchronized int save(Context context, CharSequence text, String source,
                                 int account, long ownerId, long dialogId, int messageId, boolean task)
            throws Exception {
        String value = NabdhV1Engine.bounded(text);
        if (value.isEmpty()) throw new IllegalArgumentException("Empty note");
        if (value.length() > MAX_ENTRY) value = value.substring(0, MAX_ENTRY);
        JSONArray old = readJson(context);
        JSONArray next = new JSONArray();
        JSONObject fresh = new JSONObject();
        fresh.put("text", value);
        fresh.put("source", source == null ? "manual" : source);
        fresh.put("created", System.currentTimeMillis());
        fresh.put("id", UUID.randomUUID().toString());
        if (account >= 0) {
            fresh.put("account", account);
            fresh.put("owner", ownerId);
            fresh.put("dialog", dialogId);
            fresh.put("message", messageId);
            fresh.put("task", task);
        }
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
                out.add(new Note(entry));
            }
        }
        return out;
    }

    private static synchronized void update(Context context, Note note, boolean delete)
            throws Exception {
        JSONArray entries = readJson(context);
        for (int i = 0; i < entries.length(); i++) {
            JSONObject entry = entries.getJSONObject(i);
            boolean matches = note.id.isEmpty()
                    ? entry.optString("id").isEmpty() && entry.optLong("created") == note.createdAt
                        && note.text.equals(entry.optString("text")) && note.source.equals(entry.optString("source"))
                    : note.id.equals(entry.optString("id"));
            if (!matches) continue;
            if (delete) {
                entries.remove(i);
            } else {
                entry.put("done", !entry.optBoolean("done"));
            }
            write(context, entries);
            return;
        }
        throw new IllegalStateException("Workspace entry is no longer available");
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
        show(context, ar, null);
    }

    public static void show(Context context, boolean ar, BaseFragment fragment) {
        final List<Note> notes = new ArrayList<>();
        try {
            for (Note note : list(context)) {
                if (visible(fragment, note)) {
                    notes.add(note);
                }
            }
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
            Note note = notes.get(i);
            titles[i] = (note.task ? (note.done ? "✓ " : "□ ") : "")
                    + (v.length() > 65 ? v.substring(0, 65) + "…" : v);
        }
        new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
            .setTitle(label(ar, "ملاحظات محلية مشفرة", "Encrypted local notes"))
            .setItems(titles, (dialog, selected) -> {
                Note note = notes.get(selected);
                showNote(context, ar, fragment, note);
            })
            .setNegativeButton(label(ar, "إغلاق", "Close"), null)
            .show();
    }

    private static boolean visible(BaseFragment fragment, Note note) {
        return note.account < 0 || (fragment != null && note.ownerId != 0
                && note.account == fragment.getCurrentAccount()
                && note.ownerId == fragment.getUserConfig().getClientUserId()
                && NabdhMessageTools.canAccess(fragment, note.dialogId));
    }

    private static void showNote(Context context, boolean ar, BaseFragment fragment, Note note) {
        if (!visible(fragment, note)) return;
        List<String> titles = new ArrayList<>();
        List<Runnable> actions = new ArrayList<>();
        if (fragment != null && note.messageId > 0) {
            titles.add(label(ar, "فتح الرسالة الأصلية", "Open original message"));
            actions.add(() -> NabdhMessageTools.openMessage(fragment, note.dialogId, note.messageId));
        }
        if (note.task) {
            titles.add(note.done ? label(ar, "إعادة فتح المهمة", "Reopen task")
                    : label(ar, "إكمال المهمة", "Complete task"));
            actions.add(() -> {
                try {
                    update(context, note, false);
                    show(context, ar, fragment);
                } catch (Exception error) {
                    error(context, ar);
                }
            });
        }
        titles.add(label(ar, "نسخ", "Copy"));
        actions.add(() -> {
            ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard != null) clipboard.setPrimaryClip(ClipData.newPlainText("Nabdh local note", note.text));
        });
        titles.add(label(ar, "حذف", "Delete"));
        actions.add(() -> new AlertDialog.Builder(context)
                .setTitle(label(ar, "حذف العنصر المحلي؟", "Delete local item?"))
                .setNegativeButton(label(ar, "إلغاء", "Cancel"), null)
                .setPositiveButton(label(ar, "حذف", "Delete"), (dialog, which) -> {
                    try {
                        update(context, note, true);
                    } catch (Exception error) {
                        error(context, ar);
                    }
                }).show());
        new AlertDialog.Builder(context)
                .setTitle(note.task ? label(ar, "مهمة محفوظة", "Saved task") : label(ar, "ملاحظة محفوظة", "Saved note"))
                .setMessage(note.text)
                .setItems(titles.toArray(new String[0]), (dialog, which) -> {
                    if (visible(fragment, note)) actions.get(which).run();
                })
                .setNegativeButton(label(ar, "إغلاق", "Close"), null)
                .show();
    }

}
