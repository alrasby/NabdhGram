package org.telegram.ui.Components;

import android.os.Build;

import com.google.mlkit.genai.common.FeatureStatus;
import com.google.mlkit.genai.common.DownloadCallback;
import com.google.mlkit.genai.common.GenAiException;
import com.google.mlkit.genai.prompt.Generation;
import com.google.mlkit.genai.prompt.GenerativeModel;
import com.google.mlkit.genai.prompt.GenerateContentResponse;
import com.google.mlkit.genai.prompt.java.GenerativeModelFutures;

import java.util.concurrent.TimeUnit;

/** Gemini Nano through supported Android AICore; no model bundled with Telegram. */
public final class NabdhAiNanoProvider {
    // Separate an AICore connection/setup failure from a genuine unsupported
    // feature. The Activity must never claim "unsupported" for either case.
    public static final int STATUS_CHECK_FAILED = -100;
    // A safe diagnostic category only: no model prompt, stack trace,
    // AICore exception text or Telegram data is retained or logged.
    private static volatile String lastDiagnostic = "NONE";
    public static String diagnosticCode() { return lastDiagnostic; }
    private NabdhAiNanoProvider() {}

    private static void close(GenerativeModel model) {
        if (model == null) return;
        try { model.close(); } catch (RuntimeException ignored) { }
    }

    /** Google AICore statuses: AVAILABLE, DOWNLOADABLE, DOWNLOADING, UNAVAILABLE. */
    public static int status() {
        if (Build.VERSION.SDK_INT < 26) return FeatureStatus.UNAVAILABLE;
        GenerativeModel model = null;
        try {
            model = Generation.INSTANCE.getClient();
            int result = GenerativeModelFutures.from(model)
                    .checkStatus().get(8, TimeUnit.SECONDS);
            lastDiagnostic = "NONE";
            return result;
        } catch (Exception | LinkageError failure) {
            // Preserve just the failure category; never expose exception
            // message, provider internals or text from the user.
            Throwable cause = failure instanceof java.util.concurrent.ExecutionException
                    && failure.getCause() != null ? failure.getCause() : failure;
            if (cause instanceof java.util.concurrent.TimeoutException)
                lastDiagnostic = "TIMEOUT";
            else if (cause instanceof SecurityException)
                lastDiagnostic = "PERMISSION";
            else if (cause instanceof LinkageError)
                lastDiagnostic = "API_INCOMPATIBLE";
            else if (cause instanceof java.util.concurrent.CancellationException)
                lastDiagnostic = "CANCELLED";
            else if (failure instanceof java.util.concurrent.ExecutionException)
                lastDiagnostic = "CLIENT_EXECUTION";
            else if (failure instanceof InterruptedException) {
                Thread.currentThread().interrupt();
                lastDiagnostic = "INTERRUPTED";
            } else
                lastDiagnostic = "SERVICE_UNAVAILABLE";
            return STATUS_CHECK_FAILED;
        } finally {
            close(model);
        }
    }

    public static boolean available() {
        return status() == FeatureStatus.AVAILABLE;
    }

    /** No model download occurs without an explicit user tap. */
    public interface DownloadProgress {
        void onStatus(String code);
    }

    public static int download(DownloadProgress progress) throws Exception {
        if (Build.VERSION.SDK_INT < 26) return FeatureStatus.UNAVAILABLE;
        GenerativeModel model = null;
        try {
            model = Generation.INSTANCE.getClient();
            GenerativeModelFutures futures = GenerativeModelFutures.from(model);
            int status = futures.checkStatus().get(8, TimeUnit.SECONDS);
            if (status != FeatureStatus.DOWNLOADABLE) return status;
            progress.onStatus("NANO_DOWNLOAD_STARTING");
            futures.download(new DownloadCallback() {
                @Override public void onDownloadStarted(long totalBytes) {
                    progress.onStatus("NANO_DOWNLOAD_STARTED");
                }
                @Override public void onDownloadProgress(long downloaded) {
                    progress.onStatus("NANO_DOWNLOAD_PROGRESS:" + downloaded);
                }
                @Override public void onDownloadCompleted() {
                    progress.onStatus("NANO_DOWNLOAD_COMPLETE");
                }
                @Override public void onDownloadFailed(GenAiException failure) {
                    progress.onStatus("NANO_DOWNLOAD_FAILED");
                }
            }).get(10, TimeUnit.MINUTES);
            return futures.checkStatus().get(8, TimeUnit.SECONDS);
        } finally {
            close(model);
        }
    }

    public static String infer(String prompt) throws Exception {
        if (Build.VERSION.SDK_INT < 26)
            throw new IllegalStateException("AICore requires Android 26+");
        GenerativeModel model = null;
        try {
            model = Generation.INSTANCE.getClient();
            GenerativeModelFutures futures = GenerativeModelFutures.from(model);
            if (futures.checkStatus().get(8, TimeUnit.SECONDS) != FeatureStatus.AVAILABLE)
                throw new IllegalStateException("Gemini Nano not available");
            GenerateContentResponse result = futures.generateContent(prompt)
                .get(75, TimeUnit.SECONDS);
            if (result == null || result.getCandidates() == null ||
                    result.getCandidates().isEmpty())
                throw new IllegalStateException("Gemini Nano produced no response");
            String value = result.getCandidates().get(0).getText();
            if (value == null || value.trim().isEmpty())
                throw new IllegalStateException("Gemini Nano returned no text");
            return value.length() > 6000 ? value.substring(0, 6000) : value;
        } finally {
            // Release AICore client before any Gemma fallback may be attempted.
            close(model);
        }
    }
}
