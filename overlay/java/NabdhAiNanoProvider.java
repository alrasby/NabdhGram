package org.telegram.ui.Components;

import android.os.Build;

import com.google.mlkit.genai.common.FeatureStatus;
import com.google.mlkit.genai.prompt.Generation;
import com.google.mlkit.genai.prompt.GenerateContentResponse;
import com.google.mlkit.genai.prompt.java.GenerativeModelFutures;

import java.util.concurrent.TimeUnit;

/** Gemini Nano through supported Android AICore, no model bundled in APK. */
public final class NabdhAiNanoProvider {
    private NabdhAiNanoProvider() {}
    private static GenerativeModelFutures client() {
        return GenerativeModelFutures.from(Generation.INSTANCE.getClient());
    }
    public static boolean available() {
        if (Build.VERSION.SDK_INT < 26) return false;
        try {
            return client().checkStatus().get(8, TimeUnit.SECONDS) == FeatureStatus.AVAILABLE;
        } catch (Exception | LinkageError unavailable) {
            return false;
        }
    }
    public static String infer(String prompt) throws Exception {
        if (Build.VERSION.SDK_INT < 26) throw new IllegalStateException("AICore requires Android 26+");
        GenerativeModelFutures model = client();
        if (model.checkStatus().get(8, TimeUnit.SECONDS) != FeatureStatus.AVAILABLE)
            throw new IllegalStateException("Gemini Nano is not ready");
        GenerateContentResponse result = model.generateContent(prompt).get(75, TimeUnit.SECONDS);
        if (result == null || result.getCandidates() == null || result.getCandidates().isEmpty())
            throw new IllegalStateException("Gemini Nano returned no response");
        String text = result.getCandidates().get(0).getText();
        if (text == null || text.trim().isEmpty())
            throw new IllegalStateException("No generated text");
        return text.length() > 6000 ? text.substring(0, 6000) : text;
    }
}
