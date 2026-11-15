package org.telegram.ui.Components;

import android.content.Context;
import android.net.Uri;
import android.os.Build;
import com.google.mediapipe.tasks.genai.llminference.LlmInference;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;

/** Opt-in Gemma .task model installed from SAF after user verifies its SHA-256. */
public final class NabdhAiGemmaProvider {
    private static final long MIN = 30L * 1024 * 1024;
    private static final long MAX = 1_700L * 1024 * 1024;
    private NabdhAiGemmaProvider() {}

    private static File dir(Context context) { return context.getNoBackupFilesDir(); }
    private static File model(Context context) { return new File(dir(context), "nabdh_gemma_v1.task"); }
    private static File hashFile(Context context) { return new File(dir(context), "nabdh_gemma_v1.sha256"); }

    public static boolean available(Context context) {
        if (Build.VERSION.SDK_INT < 28 || Build.SUPPORTED_64_BIT_ABIS.length == 0)
            return false;
        File file = model(context), hash = hashFile(context);
        return file.isFile() && file.length() >= MIN && file.length() <= MAX &&
                hash.isFile() && hash.length() == 64;
    }

    public static synchronized String install(Context context, Uri source, String expected)
            throws Exception {
        if (Build.VERSION.SDK_INT < 28 || Build.SUPPORTED_64_BIT_ABIS.length == 0)
            throw new IllegalStateException("Gemma requires supported 64-bit Android 28+");
        if (expected == null || !expected.matches("(?i)[a-f0-9]{64}"))
            throw new IllegalArgumentException("Official SHA-256 is required");
        if (source == null || !"content".equals(source.getScheme()))
            throw new IllegalArgumentException("Select a model with the Android document picker");
        expected = expected.toLowerCase(Locale.ROOT);
        File incoming = new File(dir(context), "nabdh_gemma_v1.partial");
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        long count = 0;
        boolean good = false;
        try (InputStream in = context.getContentResolver().openInputStream(source);
             FileOutputStream out = new FileOutputStream(incoming)) {
            if (in == null) throw new java.io.IOException("Model could not be read");
            byte[] buffer = new byte[256 * 1024];
            int n;
            while ((n = in.read(buffer)) != -1) {
                count += n;
                if (count > MAX) throw new IllegalArgumentException("Model too large");
                digest.update(buffer, 0, n);
                out.write(buffer, 0, n);
            }
            out.getFD().sync();
            good = count >= MIN;
        } finally {
            if (!good) incoming.delete();
        }
        if (!good) throw new IllegalArgumentException("Model is too small");
        StringBuilder actual = new StringBuilder(64);
        for (byte b : digest.digest()) actual.append(String.format(Locale.ROOT, "%02x", b & 255));
        if (!MessageDigest.isEqual(expected.getBytes(StandardCharsets.US_ASCII),
                                   actual.toString().getBytes(StandardCharsets.US_ASCII))) {
            incoming.delete();
            throw new SecurityException("Gemma SHA-256 mismatch");
        }
        // Remove stale sidecar before replacing model; an interrupted import fails closed.
        hashFile(context).delete();
        if (!incoming.renameTo(model(context))) {
            incoming.delete();
            throw new java.io.IOException("Failed to commit checked model");
        }
        try (FileOutputStream sidecar = new FileOutputStream(hashFile(context))) {
            sidecar.write(expected.getBytes(StandardCharsets.US_ASCII));
            sidecar.getFD().sync();
        }
        return actual.toString();
    }

    public static synchronized void remove(Context context) {
        hashFile(context).delete();
        model(context).delete();
        new File(dir(context), "nabdh_gemma_v1.partial").delete();
    }

    public static String infer(Context context, String prompt) throws Exception {
        if (!available(context)) throw new IllegalStateException("Install a verified Gemma model first");
        LlmInference.LlmInferenceOptions options = LlmInference.LlmInferenceOptions.builder()
                .setModelPath(model(context).getAbsolutePath())
                .setMaxTokens(512)
                .build();
        LlmInference inference = null;
        try {
            inference = LlmInference.createFromOptions(context, options);
            String response = inference.generateResponse(prompt);
            if (response == null || response.trim().isEmpty())
                throw new IllegalStateException("Gemma returned no content");
            return response.length() > 6000 ? response.substring(0, 6000) : response;
        } finally {
            if (inference != null) inference.close();
        }
    }
}
