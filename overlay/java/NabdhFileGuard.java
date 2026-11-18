package org.telegram.ui.Components;

import java.util.Locale;

/**
 * On-demand, offline, bounded file-signature checks. This is NOT an antivirus
 * engine, reputation system, or intercept of Telegram file opening.
 * The Android caller reads only the first 16 bytes of a user-chosen document.
 */
public final class NabdhFileGuard {
    private NabdhFileGuard() { }

    private static boolean bytes(byte[] b, int... values) {
        if (b == null || b.length < values.length) return false;
        for (int i = 0; i < values.length; i++) {
            if ((b[i] & 0xff) != values[i]) return false;
        }
        return true;
    }

    public static String signature(byte[] b) {
        if (bytes(b, 0x25, 0x50, 0x44, 0x46, 0x2d)) return "PDF";
        if (bytes(b, 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)) return "PNG";
        if (bytes(b, 0xff, 0xd8, 0xff)) return "JPEG";
        if (bytes(b, 0x47, 0x49, 0x46, 0x38, 0x37, 0x61)
                || bytes(b, 0x47, 0x49, 0x46, 0x38, 0x39, 0x61)) return "GIF";
        if (bytes(b, 0x50, 0x4b, 0x03, 0x04)
                || bytes(b, 0x50, 0x4b, 0x05, 0x06)
                || bytes(b, 0x50, 0x4b, 0x07, 0x08)) return "ZIP";
        if (bytes(b, 0x7f, 0x45, 0x4c, 0x46)) return "ELF";
        if (bytes(b, 0x4d, 0x5a)) return "MZ";
        return "UNKNOWN";
    }

    public static String inspect(String displayName, String mime, byte[] header, boolean arabic) {
        String name = displayName == null ? "" : displayName.trim();
        if (name.length() > 180) name = name.substring(0, 180);
        String lower = name.toLowerCase(Locale.ROOT);
        String type = signature(header);
        StringBuilder out = new StringBuilder(arabic
                ? "تحليل محلي يدوي لأول بايتات الملف فقط. لا يتحقق من سلامة الملف أو خلوه من البرمجيات الضارة.\n"
                : "Manual offline header check only. This does not verify the file is safe or malware-free.\n");
        out.append(arabic ? "توقيع البداية: " : "Header signature: ").append(type).append('\n');
        boolean mismatch =
                (lower.endsWith(".pdf") && !"PDF".equals(type))
                || (lower.endsWith(".png") && !"PNG".equals(type))
                || ((lower.endsWith(".jpg") || lower.endsWith(".jpeg")) && !"JPEG".equals(type))
                || (lower.endsWith(".gif") && !"GIF".equals(type))
                || (lower.endsWith(".zip") && !"ZIP".equals(type))
                || (lower.endsWith(".apk") && !"ZIP".equals(type));
        boolean executable = "ELF".equals(type) || "MZ".equals(type);
        if (mismatch) out.append(arabic
                ? "⚠ نوع الملف لا يطابق الامتداد الظاهر؛ تحقق قبل فتحه.\n"
                : "⚠ File header does not match its displayed extension; verify before opening.\n");
        if (executable) out.append(arabic
                ? "⚠ وُجد توقيع ملف تنفيذي. لا تشغّله من مصدر غير موثوق.\n"
                : "⚠ Executable header detected. Never run untrusted executables.\n");
        if ("ZIP".equals(type) && (lower.endsWith(".pdf") || lower.endsWith(".png")
                || lower.endsWith(".jpg") || lower.endsWith(".jpeg"))) {
            out.append(arabic
                    ? "⚠ قد تكون حزمة ZIP أو APK متنكرة بمظهر مستند أو صورة.\n"
                    : "⚠ This could be a ZIP/APK package disguised as a document or image.\n");
        }
        if (mime != null && mime.equalsIgnoreCase("application/pdf") && !"PDF".equals(type)) {
            out.append(arabic
                    ? "⚠ نوع MIME المُعلن PDF لا يطابق توقيع البداية.\n"
                    : "⚠ Declared PDF MIME type conflicts with file signature.\n");
        }
        if (!mismatch && !executable) {
            out.append(arabic
                    ? "لم يظهر تعارض معروف في هذا الفحص المحدود؛ هذا ليس إثبات أمان.\n"
                    : "No known mismatch found by this limited check; NOT a safety certification.\n");
        }
        if ("UNKNOWN".equals(type)) out.append(arabic
                ? "توقيع غير معروف؛ يجب التحقق يدويًا.\n"
                : "Unrecognized signature; review manually.\n");
        return out.toString().trim();
    }
}
