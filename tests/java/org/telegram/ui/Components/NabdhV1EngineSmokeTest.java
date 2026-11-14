package org.telegram.ui.Components;

/** Pure-Java offline regression checks, runnable with host JDK (no Android SDK). */
public final class NabdhV1EngineSmokeTest {
    private static void check(boolean pass, String why) {
        if (!pass) throw new AssertionError(why);
    }
    public static void main(String[] args) {
        String input = "يجب إغلاق المهمة 2026-11-15. هل نتفق على ذلك؟ تم الاتفاق اليوم.";
        String focus = NabdhV1Engine.focus(input, true);
        check(focus.contains("2026-11-15"), "date extraction");
        check(focus.contains("يجب إغلاق"), "task extraction");
        check(focus.contains("هل نتفق"), "Arabic question");
        check(focus.contains("تم الاتفاق"), "decision extraction");
        String recap = NabdhV1Engine.catchUp(input, true);
        check(recap.contains("عدد المقاطع"), "manual source scope");
        check(recap.contains("تم الاتفاق"), "recap decisions");
        String security = NabdhV1Engine.shield(
            "http://127.0.0.1/login and https://example.com/pay.pdf.exe", false);
        check(security.contains("Unencrypted HTTP"), "http warning");
        check(security.contains("Direct IP"), "IP host warning");
        check(security.contains("double extension"), "executable disguise warning");
        check(NabdhV1Engine.shield("hello", true).contains("لم تُكتشف"), "no url case");
        check(NabdhV1Engine.bounded(null).isEmpty(), "null safe");
        check(NabdhV1Engine.bounded("x".repeat(12000)).length() == 8000, "length cap");
        String edge = "x".repeat(7999) + "😀" + "abc";
        check(NabdhV1Engine.bounded(edge).length() == 7999, "surrogate-safe bound");
        check(!NabdhV1Engine.shield("https://example.com", false).contains("Verified safe"),
              "no unconditional URL safety guarantee");
        System.out.println("PASS: local Focus Lens, manual catch-up, Shield signals, bounds");
    }
}
