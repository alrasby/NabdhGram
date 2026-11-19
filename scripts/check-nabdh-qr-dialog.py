#!/usr/bin/env python3
"""Guard NabdhGram's QR dialog lifecycle against pinned Telegram changes.

This is a source-level regression check, not a replacement for device logcat
and an interactive QR authentication test.
"""
from pathlib import Path
import sys


def check(text):
    required = (
        "showDialog(dialog, dismissed -> {",
        "if (nabdhQrDialog == dialog) nabdhStopQrLogin();",
        "nabdhQrButton.setOnClickListener(view -> {",
        "catch (RuntimeException exception)",
        "nabdhStopQrLogin();",
        "nabdhRequestQrToken();",
        "RequestFlagWithoutLogin",
        "TL_auth_exportLoginToken",
        "TL_auth_importLoginToken",
        "TL_auth_loginTokenSuccess",
        "indexOfChild(phoneOutlineView)",
        "addView(nabdhQrButton, phoneInputIndex + 1,",
        "ApplicationLoader.isNetworkOnline()",
        "NabdhQrLoginOffline",
        "nabdhWatchQrRequest(generation);",
        "NABDH_QR_TIMEOUT_MS = 20000L",
        "nabdhCancelQrTimeout();",
        "NabdhQrLoginTimeout",
    )
    for marker in required:
        if text.count(marker) < 1:
            raise ValueError("QR lifecycle/auth contract missing: " + marker)
    if text.find("addView(nabdhQrButton, phoneInputIndex + 1,") < 0:
        raise ValueError("QR sign-in must appear immediately below phone entry")
    if "dialog.setOnDismissListener(ignored ->" in text:
        raise ValueError("Telegram BaseFragment overwrites that QR dismiss listener")
    if text.count("showDialog(dialog, dismissed -> {") != 1:
        raise ValueError("QR dialog must use one owner-managed dismiss hook")
    if "FileLog.d(url)" in text or "FileLog.d(token.token)" in text:
        raise ValueError("Sensitive QR token logging must not be enabled")
    return True


def self_test():
    fixture = "\n".join((
        "showDialog(dialog, dismissed -> {",
        "if (nabdhQrDialog == dialog) nabdhStopQrLogin();",
        "nabdhQrButton.setOnClickListener(view -> {",
        "catch (RuntimeException exception)",
        "nabdhStopQrLogin();",
        "nabdhRequestQrToken();",
        "RequestFlagWithoutLogin",
        "TL_auth_exportLoginToken",
        "TL_auth_importLoginToken",
        "TL_auth_loginTokenSuccess",
        "indexOfChild(phoneOutlineView)",
        "addView(nabdhQrButton, phoneInputIndex + 1,",
        "ApplicationLoader.isNetworkOnline()",
        "NabdhQrLoginOffline",
        "nabdhWatchQrRequest(generation);",
        "NABDH_QR_TIMEOUT_MS = 20000L",
        "nabdhCancelQrTimeout();",
        "NabdhQrLoginTimeout",
    ))
    check(fixture)
    for bad in (
        fixture.replace("showDialog(dialog, dismissed -> {", "showDialog(dialog);"),
        fixture + "\ndialog.setOnDismissListener(ignored ->",
        fixture + "\nFileLog.d(url)",
    ):
        try:
            check(bad)
        except ValueError:
            continue
        raise AssertionError("QR lifecycle regression was accepted")
    print("PASS: QR lifecycle regression detection self-test")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 2:
        src = Path(sys.argv[1])
        if not src.is_file():
            raise SystemExit("No generated Telegram LoginActivity found")
        check(src.read_text(encoding="utf-8"))
        print("PASS: generated Telegram QR dialog lifecycle and token safety guards")
    else:
        raise SystemExit("Usage: check-nabdh-qr-dialog.py --self-test | LOGIN_ACTIVITY_JAVA")
