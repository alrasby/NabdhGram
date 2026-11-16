package org.telegram.ui.Components;

import android.content.Context;

/** V1 release visibility gate only. Backlog features retain their source,
 * resources, IDs and activation routes for a future, tested release.
 * Never gates native Telegram messaging, login, calls or background services.
 */
public final class NabdhFeatureGates {
    private static final String FILE = "nabdhgram_release_feature_gates";
    private NabdhFeatureGates() {}

    public static boolean visible(int id) {
        // These two detail pages contain only disclosures, not a usable action.
        // 203 = redundant preview help; 401 = translation settings placeholder.
        // Native Telegram preview/translation features are NOT disabled.
        return id != 203 && id != 401;
    }
    public static boolean verifiedAiChat(Context context) {
        return context != null && context.getSharedPreferences(
                FILE, Context.MODE_PRIVATE).getBoolean("tested_ai_inference", false);
    }
    /** Called only after a real, non-status local inference result is delivered. */
    public static void noteVerifiedAiInference(Context context) {
        if (context != null) context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
                .edit().putBoolean("tested_ai_inference", true).apply();
    }
}
