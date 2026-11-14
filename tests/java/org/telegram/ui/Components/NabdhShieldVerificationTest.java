package org.telegram.ui.Components;

/** Deterministic, synthetic regression fixtures; NOT a real-world accuracy study. */
public final class NabdhShieldVerificationTest {
    private static int count;
    private static void check(boolean ok, String id) {
        count++;
        if (!ok) throw new AssertionError("NabdhShield verification: " + id);
    }
    private static void contains(String actual, String value, String id) {
        check(actual.contains(value), id + " missing: " + value);
    }
    public static void main(String[] args) {
        contains(NabdhV1Engine.shield("http://example.test/a", false),
                "Unencrypted HTTP", "http");
        contains(NabdhV1Engine.shield("https://user:pass@example.test/a", false),
                "Embedded username/password", "userinfo");
        contains(NabdhV1Engine.shield("https://xn--e1afmkfd.test/", false),
                "Punycode host", "punycode");
        contains(NabdhV1Engine.shield("https://192.0.2.2/test", false),
                "Direct IP-address host", "ip");
        contains(NabdhV1Engine.shield("https://files.test/photo.jpg.exe", false),
                "double extension", "double-extension");
        contains(NabdhV1Engine.shield("https://files.test/update.apk", false),
                "Executable download", "apk");
        contains(NabdhV1Engine.shield("https://ordinary.example/path", false),
                "does NOT mean safe", "https-is-not-proof");
        contains(NabdhV1Engine.shield("https://ordinary.example/path", true),
                "لا يثبت الأمان", "arabic-no-false-safety");
        contains(NabdhV1Engine.shield("just a friendly greeting", false),
                "No HTTP/HTTPS links", "empty-links");
        contains(NabdhV1Engine.scam("Urgent: send your OTP now", false),
                "Verification/login code", "otp");
        contains(NabdhV1Engine.scam("Urgent: send your OTP now", false),
                "urgency", "urgency");
        contains(NabdhV1Engine.scam("Send money by bank transfer", false),
                "payment or transfer", "payment");
        contains(NabdhV1Engine.scam("Official support team requests a code", false),
                "support/admin identity", "impersonation");
        contains(NabdhV1Engine.scam("أرسل رمز التحقق فورا", true),
                "رمز دخول", "arabic-otp");
        contains(NabdhV1Engine.scam("أرسل رمز التحقق فورا", true),
                "استعجال", "arabic-urgency");
        contains(NabdhV1Engine.scam("تحويل بنكي عاجل", true),
                "طلب مالي", "arabic-payment");
        contains(NabdhV1Engine.scam("رسالة عادية من صديق", true),
                "لا يعني أن الرسالة آمنة", "arabic-no-false-safety");
        contains(NabdhV1Engine.scam("Normal friendly message", false),
                "does not mean the message is safe", "en-no-false-safety");
        check(NabdhV1Engine.scam("Normal friendly message", false).equals(
                NabdhV1Engine.scam("Normal friendly message", false)),
                "deterministic-output");
        byte[] pdf = new byte[]{'%', 'P', 'D', 'F', '-'};
        byte[] png = new byte[]{(byte) 0x89, 'P', 'N', 'G', 13, 10, 26, 10};
        byte[] zip = new byte[]{'P', 'K', 3, 4};
        byte[] elf = new byte[]{0x7f, 'E', 'L', 'F'};
        byte[] exe = new byte[]{'M', 'Z'};
        check("PDF".equals(NabdhFileGuard.signature(pdf)), "pdf-magic");
        check("PNG".equals(NabdhFileGuard.signature(png)), "png-magic");
        check("ZIP".equals(NabdhFileGuard.signature(zip)), "zip-magic");
        check("ELF".equals(NabdhFileGuard.signature(elf)), "elf-magic");
        check("MZ".equals(NabdhFileGuard.signature(exe)), "exe-magic");
        check("UNKNOWN".equals(NabdhFileGuard.signature(new byte[0])), "empty-magic");
        contains(NabdhFileGuard.inspect("invoice.pdf", "application/pdf", zip, false),
                "does not match", "zip-masked-pdf");
        contains(NabdhFileGuard.inspect("image.png", "image/png", elf, false),
                "Executable header", "elf-masked-png");
        contains(NabdhFileGuard.inspect("invoice.pdf", "application/pdf", pdf, false),
                "NOT a safety certification", "matching-magic-is-not-safety");
        contains(NabdhFileGuard.inspect("invoice.pdf", "application/pdf", png, false),
                "Declared PDF MIME type conflicts", "mime-mismatch");
        contains(NabdhFileGuard.inspect("image.png", null, new byte[0], true),
                "توقيع غير معروف", "arabic-unknown-file");
        contains(NabdhFileGuard.inspect("image.png", null, new byte[0], true),
                "هذا ليس إثبات أمان", "arabic-no-file-safety-cert");
        System.out.println("PASS: " + count + " synthetic NabdhShield assertions");
        System.out.println("NOTE: unit regressions are not real-world precision/recall");
    }
}
