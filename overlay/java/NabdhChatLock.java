package org.telegram.ui.Components;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.os.SystemClock;
import android.text.InputType;
import android.widget.EditText;
import android.widget.Toast;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
import javax.crypto.KeyGenerator;
import javax.crypto.Mac;
import javax.crypto.SecretKey;

/**
 * Opt-in per-chat foreground gate. PIN digest keyed by AndroidKeyStore HMAC;
 * configuration lives under noBackupFilesDir. Never holds or reads messages.
 * This is NOT a replacement for Telegram's notification/OS privacy controls.
 */
public final class NabdhChatLock {
    private static final String KEY = "nabdhgram_chat_lock_hmac_v1";
    private static final String FILE = "nabdh_chatlock_v1.json";
    private static final long SESSION_MS = 30_000;
    private static final HashMap<String, Long> UNLOCKED = new HashMap<>();
    // Notification rendering may check the same dialog hundreds of times.
    // Cache the bounded 250-entry ID set rather than re-read/parse AtomicFile
    // on every notification, but revalidate disk metadata on each lookup.
    private static Set<String> cachedLocked;
    private static boolean cachedUnreadable;
    private static long cachedPrimaryTime = -1;
    private static long cachedPrimaryBytes = -1;
    private static long cachedBackupTime = -1;
    private static long cachedBackupBytes = -1;
    private static long blockedUntilElapsed;
    private NabdhChatLock() {}

    private static String id(int account, long dialog) { return account + ":" + dialog; }
    private static AtomicFile location(Context context) {
        return new AtomicFile(new File(context.getNoBackupFilesDir(), FILE));
    }
    private static JSONObject read(Context context) {
        File primary = new File(context.getNoBackupFilesDir(), FILE);
        File backup = new File(context.getNoBackupFilesDir(), FILE + ".bak");
        if (!primary.exists() && !backup.exists()) return new JSONObject();
        try (FileInputStream input = location(context).openRead()) {
            byte[] raw = new byte[(int) Math.min(65_536, input.available())];
            int size = input.read(raw);
            if (size <= 0) throw new java.io.IOException("Empty chat-lock state");
            JSONObject decoded = new JSONObject(
                    new String(raw, 0, size, StandardCharsets.UTF_8));
            if (!decoded.has("pin") || !decoded.has("dialogs"))
                throw new java.io.IOException("Malformed chat-lock state");
            return decoded;
        } catch (Exception unreadable) {
            // Never treat a damaged lock file as "no locks". Fail closed.
            JSONObject blocked = new JSONObject();
            try { blocked.put("_unreadable", true); } catch (Exception ignored) {}
            return blocked;
        }
    }
    private static void save(Context context, JSONObject json) throws Exception {
        AtomicFile file = location(context);
        FileOutputStream out = file.startWrite();
        try {
            out.write(json.toString().getBytes(StandardCharsets.UTF_8));
            out.flush();
            file.finishWrite(out);
            cachedLocked = null; // Read back from committed AtomicFile on next check.
        } catch (Exception failure) {
            file.failWrite(out);
            throw failure;
        }
    }
    private static SecretKey secret() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        SecretKey existing = (SecretKey) store.getKey(KEY, null);
        if (existing != null) return existing;
        KeyGenerator maker = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_HMAC_SHA256, "AndroidKeyStore");
        maker.init(new KeyGenParameterSpec.Builder(KEY,
                KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_VERIFY)
                .setDigests(KeyProperties.DIGEST_SHA256).build());
        return maker.generateKey();
    }
    private static byte[] mac(String pin) throws Exception {
        Mac signer = Mac.getInstance("HmacSHA256");
        signer.init(secret());
        return signer.doFinal(("NabdhChatLock|v1|" + pin).getBytes(StandardCharsets.UTF_8));
    }
    private static String hex(byte[] data) {
        StringBuilder s = new StringBuilder(data.length * 2);
        for (byte b : data) s.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
        return s.toString();
    }
    private static byte[] decode(String hex) {
        if (hex == null || hex.length() != 64) return new byte[0];
        byte[] out = new byte[32];
        try {
            for (int i = 0; i < out.length; i++)
                out[i] = (byte) Integer.parseInt(hex.substring(i*2,i*2+2),16);
            return out;
        } catch (Exception e) { return new byte[0]; }
    }

    public static synchronized boolean configured(Context context) {
        JSONObject state = read(context);
        return state.optBoolean("_unreadable") ||
               state.optString("pin", "").length() == 64;
    }
    public static synchronized void setPin(Context context, String pin) throws Exception {
        if (configured(context)) throw new IllegalStateException("PIN already configured");
        if (pin == null || !pin.matches("[0-9]{6,12}"))
            throw new IllegalArgumentException("Use 6–12 digits");
        JSONObject info = new JSONObject();
        info.put("pin", hex(mac(pin)));
        info.put("dialogs", new JSONArray());
        save(context, info);
    }
    public static synchronized boolean verify(Context context, String pin) {
        JSONObject info = read(context);
        long now = System.currentTimeMillis();
        // Wall time survives device reboot; monotonic time prevents shortening
        // a rate-limit lockout by changing the wall clock during this process.
        if (info.optBoolean("_unreadable") ||
                SystemClock.elapsedRealtime() < blockedUntilElapsed ||
                now < info.optLong("blockedUntil", 0)) return false;
        boolean match = false;
        try {
            match = MessageDigest.isEqual(decode(info.optString("pin")), mac(pin));
            if (match) {
                info.put("failures", 0);
                info.put("blockedUntil", 0);
                blockedUntilElapsed = 0;
            } else {
                int count = Math.min(100, info.optInt("failures", 0) + 1);
                info.put("failures", count);
                if (count >= 5) {
                    info.put("blockedUntil", now + 60_000);
                    blockedUntilElapsed = SystemClock.elapsedRealtime() + 60_000;
                }
            }
            save(context, info);
        } catch (Exception ignored) { return false; }
        return match;
    }
    public static synchronized boolean isLocked(Context context, int account, long dialog) {
        if (dialog == 0) return false;
        final File primary = new File(context.getNoBackupFilesDir(), FILE);
        final File backup = new File(context.getNoBackupFilesDir(), FILE + ".bak");
        final long primaryTime = primary.lastModified();
        final long primaryBytes = primary.length();
        final long backupTime = backup.lastModified();
        final long backupBytes = backup.length();
        if (cachedLocked == null || cachedPrimaryTime != primaryTime ||
                cachedPrimaryBytes != primaryBytes || cachedBackupTime != backupTime ||
                cachedBackupBytes != backupBytes) {
            JSONObject state = read(context);
            cachedUnreadable = state.optBoolean("_unreadable");
            Set<String> fresh = new HashSet<>();
            if (!cachedUnreadable && state.optString("pin", "").length() == 64) {
                JSONArray list = state.optJSONArray("dialogs");
                if (list != null) for (int i = 0; i < list.length(); i++) {
                    fresh.add(list.optString(i));
                }
            }
            cachedLocked = fresh;
            cachedPrimaryTime = primary.lastModified();
            cachedPrimaryBytes = primary.length();
            cachedBackupTime = backup.lastModified();
            cachedBackupBytes = backup.length();
        }
        // Malformed/truncated lock state is never interpreted as unlocked.
        return cachedUnreadable || cachedLocked.contains(id(account, dialog));
    }
    public static synchronized void setLocked(Context context, int account, long dialog,
                                               boolean enabled) throws Exception {
        JSONObject info = read(context);
        if (info.optString("pin", "").length() != 64)
            throw new IllegalStateException("Set a PIN first");
        JSONArray list = info.optJSONArray("dialogs");
        Set<String> entries = new HashSet<>();
        if (list != null) for (int i = 0; i < list.length(); i++) entries.add(list.optString(i));
        if (enabled) entries.add(id(account, dialog)); else entries.remove(id(account, dialog));
        if (entries.size() > 250) throw new IllegalStateException("Too many locks");
        JSONArray changed = new JSONArray();
        for (String key : entries) changed.put(key);
        info.put("dialogs", changed);
        save(context, info);
        UNLOCKED.remove(id(account, dialog));
    }
    public static synchronized boolean isUnlocked(int account, long dialog) {
        Long expires = UNLOCKED.get(id(account, dialog));
        if (expires == null) return false;
        if (expires > SystemClock.elapsedRealtime()) return true;
        UNLOCKED.remove(id(account, dialog));
        return false;
    }
    private static synchronized void grant(int account, long dialog) {
        UNLOCKED.put(id(account, dialog), SystemClock.elapsedRealtime() + SESSION_MS);
    }

    /** Each background/navigation pause ends the local unlock session. */
    public static synchronized void revoke(int account, long dialog) {
        UNLOCKED.remove(id(account, dialog));
    }

    public static void authenticate(Activity activity, int account, long dialog,
                                    Runnable allowed, Runnable cancelled) {
        if (activity == null || activity.isFinishing()) { cancelled.run(); return; }
        if (!isLocked(activity, account, dialog)) { allowed.run(); return; }
        if (isUnlocked(account, dialog)) { allowed.run(); return; }
        EditText input = new EditText(activity);
        input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        input.setSingleLine(true);
        input.setHint("6–12 digits");
        input.setPadding(35, 22, 35, 22);
        new AlertDialog.Builder(activity)
            .setTitle("Unlock this chat")
            .setView(input)
            .setCancelable(false)
            .setNegativeButton("Back", (d, which) -> cancelled.run())
            .setPositiveButton("Unlock", (d, which) -> {
                String pin = input.getText().toString();
                input.getText().clear();
                if (verify(activity, pin)) {
                    grant(account, dialog);
                    allowed.run();
                } else {
                    Toast.makeText(activity,
                        "Incorrect PIN or temporarily locked", Toast.LENGTH_SHORT).show();
                    authenticate(activity, account, dialog, allowed, cancelled);
                }
            }).show();
    }
}
