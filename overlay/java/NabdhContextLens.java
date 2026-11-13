package org.telegram.ui.Components;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.DialogInterface;
import android.net.Uri;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * User-triggered LOCAL text utility. No model, storage, contacts, permissions
 * or network. This is intentionally not marketed as a model-generated answer.
 * Telegram's optional AI Editor, translation and voice transcription stay
 * in their native guarded workflows.
 */
public final class NabdhContextLens {
    public interface Apply {
        void use(String text);
    }
    private static final int LIMIT = 8000;
    private static final Pattern URL =
        Pattern.compile("(?i)(?:https?://|www\\.)[^\\s<>\\\"']+");
    private NabdhContextLens() {}

    private static boolean arabic() {
        return org.telegram.messenger.LocaleController.isRTL;
    }
    private static String label(String en, String ar) {
        return arabic() ? ar : en;
    }
    private static String bounded(CharSequence text) {
        if (text == null) return "";
        String s = text.toString().trim();
        return s.length() <= LIMIT ? s : s.substring(0, LIMIT);
    }
    public static boolean show(Context context, CharSequence original, Apply apply) {
        final String source = bounded(original);
        if (source.isEmpty()) return false;
        final String[] choices = {
            label("Quick summary (local)", "ملخص سريع (محلي)"),
            label("Extract tasks (local)", "استخراج المهام (محلي)"),
            label("Check link signals (local)", "فحص مؤشرات الروابط (محلي)"),
            label("Clean up text (local)", "تنسيق النص (محلي)"),
            label("Detect language (on-device ML)", "التعرّف على اللغة (نموذج محلي)"),
            label("Translation and voice options", "خيارات الترجمة والصوت")
        };
        new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
            .setTitle(label("Nabdh Context Lens", "عدسة نبض الذكية"))
            .setItems(choices, (dialog, which) -> {
                if (which == 4) {
                    detectLanguage(context, source);
                    return;
                }
                final String output;
                switch (which) {
                    case 0: output = summary(source); break;
                    case 1: output = tasks(source); break;
                    case 2: output = linkSignals(source); break;
                    case 3: output = cleanup(source); break;
                    default: output = label(
                        "Translation: use Telegram's Translate action on a selected message where supported. "
                        + "Voice: use Telegram's own transcription action when available. "
                        + "Cloud-backed features are managed by Telegram, not by this offline Lens.",
                        "للترجمة: استخدم خيار «ترجمة» الرسمي للرسائل المحددة عندما يتوفر. "
                        + "وللصوت: استخدم التفريغ الصوتي الأصلي عندما يكون متاحًا. "
                        + "هذه الخدمات الأصلية قد تستخدم خوادم Telegram؛ العدسة المحلية لا ترسل النص.");
                }
                org.telegram.ui.ActionBar.AlertDialog.Builder result =
                    new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                        .setTitle(choices[which])
                        .setMessage(output)
                        .setNegativeButton(label("Close", "إغلاق"), null);
                if (which == 3 && apply != null) {
                    result.setPositiveButton(label("Use in composer", "استخدام في المحادثة"),
                        (d, button) -> apply.use(output));
                } else if (which != 5) {
                    result.setPositiveButton(label("Copy result", "نسخ النتيجة"), (d, button) -> {
                        ClipboardManager cm = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
                        if (cm != null) cm.setPrimaryClip(ClipData.newPlainText("Nabdh Lens result", output));
                    });
                }
                result.show();
            })
            .setNegativeButton(label("Cancel", "إلغاء"), null)
            .show();
        return true;
    }

    private static void detectLanguage(Context context, String text) {
        // Telegram already bundles com.google.mlkit:language-id:17.0.6.
        // Run its real ML model only after explicit user action; its Task is
        // asynchronous, text is not logged, and the client is always closed.
        final com.google.mlkit.nl.languageid.LanguageIdentifier classifier =
            com.google.mlkit.nl.languageid.LanguageIdentification.getClient();
        final String sample = text.substring(0, Math.min(text.length(), 512));
        classifier.identifyLanguage(sample).addOnCompleteListener(task -> {
            try {
                if (context instanceof android.app.Activity &&
                        ((android.app.Activity) context).isFinishing()) return;
                final String result;
                if (!task.isSuccessful()) {
                    result = label("Language model unavailable on this device.",
                                   "نموذج التعرف على اللغة غير متاح على هذا الجهاز.");
                } else {
                    String code = task.getResult();
                    if (code == null || "und".equals(code)) {
                        result = label("Language could not be determined.",
                                       "تعذر تحديد اللغة بثقة.");
                    } else {
                        java.util.Locale locale = java.util.Locale.forLanguageTag(code);
                        result = locale.getDisplayLanguage(
                            arabic() ? new java.util.Locale("ar") : java.util.Locale.ENGLISH)
                            + " (" + code + ")";
                    }
                }
                new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                    .setTitle(label("On-device language recognition",
                                    "التعرف المحلي على اللغة"))
                    .setMessage(result)
                    .setPositiveButton(label("OK", "موافق"), null)
                    .show();
            } finally {
                classifier.close();
            }
        });
    }

    static String summary(String source) {
        String[] sentences = source.split("(?<=[.!؟?؛؛。])\\s+|[\\r\\n]+");
        StringBuilder out = new StringBuilder();
        for (String part : sentences) {
            String p = part.trim();
            if (p.isEmpty()) continue;
            if (out.length() > 0) out.append("\n");
            out.append(p);
            if (out.length() >= 300 || out.toString().split("\n").length >= 3) break;
        }
        return label("Extractive preview (not a generated AI summary):\n",
                     "مقتطف تلقائي وليس تلخيصًا بنموذج ذكاء اصطناعي:\n") + out;
    }

    static String tasks(String source) {
        String[] lines = source.split("[\\r\\n]+|(?<=[.!؟?])\\s+");
        StringBuilder out = new StringBuilder();
        int count = 0;
        for (String line : lines) {
            String s = line.trim();
            String normalized = s.toLowerCase(Locale.ROOT);
            if (s.isEmpty() || !(normalized.contains("يجب") || normalized.contains("يرجى")
                || normalized.contains("المطلوب") || normalized.contains("لا تنس")
                || normalized.contains("مهمة") || normalized.contains("need to")
                || normalized.contains("please ") || normalized.contains("todo")
                || normalized.contains("remember to") || normalized.contains("must "))) continue;
            if (++count > 8) break;
            out.append("• ").append(s).append("\n");
        }
        return count > 0 ? out.toString().trim() :
            label("No explicit action sentences found.", "لم تُكتشف مهام صريحة في النص.");
    }

    static String cleanup(String source) {
        // Spacing/punctuation only: never invent, send or change the meaning.
        return source.replaceAll("[\\t ]+", " ")
            .replaceAll(" *([،؛,.!?؟]) *", "$1 ")
            .replaceAll("\\n{3,}", "\n\n").trim();
    }

    static String linkSignals(String source) {
        Matcher m = URL.matcher(source);
        StringBuilder out = new StringBuilder();
        int count = 0;
        while (m.find() && count < 8) {
            count++;
            String link = m.group();
            Uri uri = Uri.parse(link.startsWith("www.") ? "https://" + link : link);
            String host = uri.getHost();
            StringBuilder flags = new StringBuilder();
            if (link.startsWith("http://")) flags.append(" HTTP");
            if (link.contains("@")) flags.append(" @");
            if (host == null || host.isEmpty()) flags.append(" invalid-host");
            else {
                if (host.contains("xn--")) flags.append(" punycode");
                if (host.matches("[0-9.]+")) flags.append(" numeric-host");
            }
            out.append(link).append("\n");
            out.append(flags.length() == 0
                ? label("No simple risk signals detected.", "لا توجد مؤشرات بسيطة واضحة.")
                : label("Review:", "راجع المؤشرات:") + flags)
                .append("\n\n");
        }
        if (count == 0) return label("No URLs found.", "لم تُكتشف روابط.");
        return out + label(
            "Heuristic hints ONLY: cannot detect malware or certify any link as safe. Do not enter passwords on unknown sites.",
            "مؤشرات أولية فقط: ليست فحص فيروسات ولا إثبات أمان للرابط. تجنب إدخال كلمات المرور في مواقع مجهولة.");
    }
}
