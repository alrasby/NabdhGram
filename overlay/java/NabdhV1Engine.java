package org.telegram.ui.Components;

import java.net.IDN;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Transparent, offline-only V1 text signals. Never accesses Telegram messages,
 * device storage, network APIs or background services. Nothing is a model
 * generated summary, virus scan or verified-safe URL certification.
 */
public final class NabdhV1Engine {
    public static final int MAX_INPUT = 8000;
    private static final int MAX_ITEMS = 6;
    private static final Pattern URL = Pattern.compile(
            "(?i)(?:https?://|www\\.)[^\\s<>\"'\\u0000-\\u001f]+");
    private static final Pattern DATE = Pattern.compile(
            "\\b(?:20\\d{2}[-/]\\d{1,2}[-/]\\d{1,2}|\\d{1,2}[-/]\\d{1,2}[-/]\\d{2,4})\\b");
    private static final Pattern QUESTION = Pattern.compile(
            "(?iu)(?:[?؟]|\\b(?:what|when|why|where|how|which|should|can)\\b|(?:هل|متى|لماذا|كيف|أين|وين|كم|ماذا))");
    private static final Pattern TASK = Pattern.compile(
            "(?iu)(?:\\b(?:todo|need to|please|must|action required|remind)\\b|(?:يجب|يرجى|الرجاء|المطلوب|لا تنس|ضروري|مهمة))");
    private static final Pattern DECISION = Pattern.compile(
            "(?iu)(?:\\b(?:agreed|decided|approved|decision|confirmed)\\b|(?:قررنا|تم الاتفاق|اعتمدنا|تقرر|موافق))");
    private static final Pattern IP_ADDRESS = Pattern.compile(
            "(?i)^\\d{1,3}(?:\\.\\d{1,3}){3}$");

    private NabdhV1Engine() { }

    public static String bounded(CharSequence text) {
        if (text == null) return "";
        String raw = text.toString().trim();
        int end = Math.min(MAX_INPUT, raw.length());
        if (end < raw.length() && end > 0 && Character.isHighSurrogate(raw.charAt(end - 1))) end--;
        return raw.substring(0, end);
    }

    private static String lang(boolean ar, String arText, String enText) {
        return ar ? arText : enText;
    }

    private static String shortLine(String raw) {
        String s = raw.replaceAll("[\\t\\x0B\\f ]+", " ").trim();
        if (s.length() > 260) return s.substring(0, 259) + "…";
        return s;
    }

    private static List<String> sentences(String source) {
        String[] segments = bounded(source).split("(?<=[.!؟?؛])\\s+|[\\r\\n]+");
        List<String> result = new ArrayList<>();
        for (String value : segments) {
            String line = shortLine(value);
            if (!line.isEmpty()) result.add(line);
        }
        return result;
    }

    private static void extract(List<String> lines, Pattern match, StringBuilder out, int max) {
        int added = 0;
        for (String line : lines) {
            if (match.matcher(line).find()) {
                out.append("• ").append(line).append('\n');
                if (++added >= max) break;
            }
        }
        if (added == 0) out.append("—\n");
    }

    /** Local text classification, with source excerpts and no semantic AI claims. */
    public static String focus(CharSequence text, boolean ar) {
        List<String> lines = sentences(bounded(text));
        StringBuilder result = new StringBuilder(lang(ar,
                "عدسة التركيز — مقتطفات حرفية من النص المدخل، وليست تحليلًا توليديًا\n",
                "Focus Lens — source excerpts from your input; not generative AI\n"));
        result.append('\n').append(lang(ar, "مهام محتملة:\n", "Possible tasks:\n"));
        extract(lines, TASK, result, MAX_ITEMS);
        result.append('\n').append(lang(ar, "أسئلة محتملة:\n", "Possible questions:\n"));
        extract(lines, QUESTION, result, MAX_ITEMS);
        result.append('\n').append(lang(ar, "قرارات أو موافقات محتملة:\n", "Possible decisions:\n"));
        extract(lines, DECISION, result, MAX_ITEMS);
        result.append('\n').append(lang(ar, "تواريخ صريحة:\n", "Explicit dates:\n"));
        int count = 0;
        for (String line : lines) {
            Matcher m = DATE.matcher(line);
            while (m.find() && count < MAX_ITEMS) {
                result.append("• ").append(m.group()).append(" — ").append(line).append('\n');
                count++;
            }
            if (count >= MAX_ITEMS) break;
        }
        if (count == 0) result.append("—\n");
        return result.toString().trim();
    }

    /** Only the manually supplied excerpt is counted; no access to unread chats. */
    public static String catchUp(CharSequence text, boolean ar) {
        List<String> lines = sentences(bounded(text));
        if (lines.isEmpty()) return lang(ar, "لا يوجد نص لتحليله.", "No text supplied.");
        StringBuilder out = new StringBuilder(lang(ar,
                "مراجعة يدوية للمقتطف الملصق فقط، وليست ملخصًا للمحادثات غير المقروءة.\n",
                "Manual pasted-text recap only; unread chats were not accessed.\n"));
        out.append(lang(ar, "عدد المقاطع: ", "Text segments: ")).append(lines.size()).append('\n');
        out.append(lang(ar, "\nأبرز الأسطر:\n", "\nOpening excerpts:\n"));
        int shown = Math.min(3, lines.size());
        for (int i = 0; i < shown; i++) out.append("• ").append(lines.get(i)).append('\n');
        out.append('\n').append(lang(ar, "مهام ظاهرة:\n", "Visible tasks:\n"));
        extract(lines, TASK, out, MAX_ITEMS);
        out.append('\n').append(lang(ar, "قرارات ظاهرة:\n", "Visible decisions:\n"));
        extract(lines, DECISION, out, MAX_ITEMS);
        return out.toString().trim();
    }

    /**
     * Explicit pasted-text warning signals. Local keyword patterns can miss
     * sophisticated scams and can flag benign conversations. No hidden access
     * to chats, contacts, OTPs or message notifications.
     */
    public static String scam(CharSequence input, boolean ar) {
        String text = bounded(input);
        if (text.isEmpty()) return lang(ar,
                "أدخل نصًا لفحص مؤشرات الاحتيال محليًا.",
                "Enter text to check local scam signals.");
        StringBuilder out = new StringBuilder(lang(ar,
                "مؤشرات تحذير نصية أولية، وليست إثباتًا لوجود احتيال أو عدمه.\n",
                "Basic pasted-text warning signals; not proof of fraud or safety.\n"));
        Pattern code = Pattern.compile("(?iu)(?:\\b(?:otp|one.time code|verification code|login code|2fa code)\\b|رمز التحقق|كود التحقق|رمز الدخول|الرمز السري)");
        Pattern pressure = Pattern.compile("(?iu)(?:\\b(?:urgent|immediately|act now|limited time|account suspended|blocked account)\\b|فوراً|فورا|عاجل|حالاً|حالا|سيتم إيقاف حسابك|تعطيل حسابك)");
        Pattern financial = Pattern.compile("(?iu)(?:\\b(?:send money|bank transfer|gift card|payment required|wire transfer)\\b|تحويل بنكي|حوّل المبلغ|ارسل المبلغ|بطاقة هدايا|رسوم تفعيل)");
        Pattern impersonation = Pattern.compile("(?iu)(?:\\b(?:support team|official support|telegram admin|administrator)\\b|فريق الدعم|الدعم الرسمي|إدارة تليجرام|مسؤول تليجرام)");
        int count = 0;
        if (code.matcher(text).find()) {
            out.append(lang(ar, "⚠ ذكر رمز دخول أو تحقق: لا تشارك رموز حسابك مع أحد.\n",
                    "⚠ Verification/login code mentioned: never share your account code.\n"));
            count++;
        }
        if (pressure.matcher(text).find()) {
            out.append(lang(ar, "⚠ صياغة استعجال أو تهديد محتملة.\n",
                    "⚠ Potential urgency or account-threat pressure.\n"));
            count++;
        }
        if (financial.matcher(text).find()) {
            out.append(lang(ar, "⚠ طلب مالي أو تحويل محتمل؛ تحقق من المستفيد.\n",
                    "⚠ Potential payment or transfer request; verify the recipient.\n"));
            count++;
        }
        if (impersonation.matcher(text).find()) {
            out.append(lang(ar, "⚠ ادعاء صفة دعم أو إدارة؛ تحقق عبر قناة رسمية مستقلة.\n",
                    "⚠ Claimed support/admin identity; verify through an independent official channel.\n"));
            count++;
        }
        if (count == 0) out.append(lang(ar,
                "لم تُكتشف الأنماط البسيطة المحددة؛ هذا لا يعني أن الرسالة آمنة.",
                "No listed basic patterns found; this does not mean the message is safe."));
        return out.toString().trim();
    }

    /**
     * URL/filename heuristic signals; NO network lookup, phishing database,
     * MIME inference, permission bypass, APK execution or malware scan.
     */
    public static String shield(CharSequence input, boolean ar) {
        String source = bounded(input);
        Matcher links = URL.matcher(source);
        StringBuilder out = new StringBuilder(lang(ar,
                "نبض شيلد — مؤشرات محلية أولية فقط؛ لا تعني أمان الرابط أو كشف البرمجيات الخبيثة.\n",
                "NabdhShield — local warning signals only; not proof of safety or malware detection.\n"));
        int found = 0;
        while (links.find() && found < 8) {
            found++;
            String raw = links.group();
            // Exclude ordinary prose punctuation but not username or query chars.
            raw = raw.replaceFirst("[.,;،؛!?؟]+$", "");
            if (raw.isEmpty()) continue;
            String value = raw.startsWith("www.") ? "https://" + raw : raw;
            out.append('\n').append(raw).append('\n');
            List<String> flags = new ArrayList<>();
            try {
                URI uri = URI.create(value);
                String host = uri.getHost();
                if ("http".equalsIgnoreCase(uri.getScheme()))
                    flags.add(lang(ar, "اتصال غير مشفر HTTP", "Unencrypted HTTP"));
                if (uri.getRawUserInfo() != null)
                    flags.add(lang(ar, "بيانات مستخدم مضمنة في الرابط (@)", "Embedded username/password in URL (@)"));
                if (host == null || host.isEmpty()) {
                    flags.add(lang(ar, "تعذر تحديد اسم المضيف", "Could not parse host"));
                } else {
                    String ascii = IDN.toASCII(host, IDN.USE_STD3_ASCII_RULES);
                    if (ascii.toLowerCase(Locale.ROOT).contains("xn--"))
                        flags.add(lang(ar, "اسم مضيف بصيغة Punycode؛ راجع الهوية", "Punycode host: verify identity"));
                    if (IP_ADDRESS.matcher(host).matches())
                        flags.add(lang(ar, "رابط يستخدم عنوان IP مباشرًا", "Direct IP-address host"));
                }
                String path = uri.getPath() == null ? "" : uri.getPath().toLowerCase(Locale.ROOT);
                if (path.matches(".*\\.(pdf|png|jpg|jpeg|docx|xlsx)\\.(exe|apk|bat|scr|msi|cmd)$"))
                    flags.add(lang(ar, "امتداد تنفيذي متنكر كملف مستند/صورة", "Executable double extension disguised as document/image"));
                else if (path.matches(".*\\.(exe|apk|bat|scr|msi|cmd)$"))
                    flags.add(lang(ar, "رابط ملف قابل للتنفيذ؛ تحقق قبل التنزيل", "Executable download: verify before opening"));
            } catch (IllegalArgumentException error) {
                flags.add(lang(ar, "صيغة رابط غير واضحة", "Malformed URL syntax"));
            }
            if (flags.isEmpty()) out.append(lang(ar,
                    "لا توجد إشارات بسيطة مما نتحقق منه؛ هذا لا يثبت الأمان.",
                    "No basic signals detected; this does NOT mean safe."));
            else for (String flag : flags) out.append("⚠ ").append(flag).append('\n');
            out.append('\n');
        }
        if (found == 0) return lang(ar, "لم تُكتشف روابط HTTP/HTTPS في النص.", "No HTTP/HTTPS links in text.");
        return out.toString().trim();
    }
}
