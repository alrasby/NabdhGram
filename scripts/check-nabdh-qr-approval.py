#!/usr/bin/env python3
"""Fail-closed checks for Telegram QR acceptance signal -> re-export -> auth success.

Source contract only, not proof that Telegram issued a real acceptance signal.
"""
from pathlib import Path
import sys

def check(root):
    root = Path(root)
    ui = root / "TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java"
    conn = root / "TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java"
    event = root / "TMessagesProj/src/main/java/org/telegram/messenger/NotificationCenter.java"
    auth = ui.read_text(encoding="utf-8")
    c = conn.read_text(encoding="utf-8")
    n = event.read_text(encoding="utf-8")
    checks = {
        "Telegram QR signal is named and unique": n.count("public static final int nabdhQrTokenAccepted = totalEvents++;") == 1,
        "Short server update detection": "message instanceof TLRPC.TL_updateShort" in c
            and "TL_update.TL_updateLoginToken" in c,
        "Batch server update detection": "message instanceof TLRPC.TL_updates" in c
            and "message instanceof TLRPC.TL_updatesCombined" in c,
        "Unauth update delivered without destroying original processor":
            "postNotificationName(NotificationCenter.nabdhQrTokenAccepted)" in c
            and "getMessagesController().processUpdates((TLRPC.Updates) message, false)" in c,
        "QR observer registered": "addWeakObserver(this, NotificationCenter.nabdhQrTokenAccepted)" in auth,
        "QR observer removed": "removeObserver(this, NotificationCenter.nabdhQrTokenAccepted)" in auth,
        "QR accepted update handled": "id == NotificationCenter.nabdhQrTokenAccepted && account == currentAccount" in auth
            and "nabdhOnQrAccepted();" in auth,
        "QR accepted signal re-exports token": "private void nabdhOnQrAccepted()" in auth
            and "nabdhQrApprovalPending = true;" in auth
            and "nabdhRequestQrToken();" in auth,
        "Pending acceptance processed after in-flight request":
            "if (nabdhQrApprovalPending && error == null" in auth
            and "nabdhQrApprovalPending = false;" in auth,
        "Existing QR success and 2FA retained":
            "TL_auth_loginTokenSuccess" in auth
            and "SESSION_PASSWORD_NEEDED" in auth
            and "TL_auth_importLoginToken" in auth,
        "No auth secrets logged": "FileLog.d(url)" not in auth and "FileLog.d(token.token)" not in auth,
    }
    for label, ok in checks.items():
        print(("PASS" if ok else "FAIL") + ": " + label)
    if not all(checks.values()):
        raise SystemExit("QR accepted-login native contract failed")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check-nabdh-qr-approval.py TELEGRAM_SOURCE")
    check(sys.argv[1])
