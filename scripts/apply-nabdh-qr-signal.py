#!/usr/bin/env python3
"""Bridge Telegram's unauthenticated updateLoginToken into LoginActivity.

Keep the official upstream MTProto update processing untouched; observe the
server approval before passing the update on to Telegram's normal pipeline.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-qr-signal.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
n = root / "TMessagesProj/src/main/java/org/telegram/messenger/NotificationCenter.java"
c = root / "TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java"
notification = n.read_text(encoding="utf-8")
connection = c.read_text(encoding="utf-8")

old_event = "    public static final int didUpdateConnectionState = totalEvents++;"
new_event = old_event + """
    // QR login approval is emitted even before an account is authorized.
    public static final int nabdhQrTokenAccepted = totalEvents++;"""
if notification.count(old_event) != 1:
    raise SystemExit("Telegram notification event anchor changed")
notification = notification.replace(old_event, new_event, 1)

anchor = """                KeepAliveJob.finishJob();
                Utilities.stageQueue.postRunnable(() -> AccountInstance.getInstance(currentAccount).getMessagesController().processUpdates((TLRPC.Updates) message, false));"""
replacement = """                KeepAliveJob.finishJob();
                // Before login, the server signals QR approval with
                // updateLoginToken. Do not depend on an authenticated
                // MessagesController to deliver this special update.
                // Observe both the short-update and normal-update envelopes.
                boolean nabdhQrApproval = false;
                if (message instanceof TLRPC.TL_updateShort) {
                    nabdhQrApproval = ((TLRPC.TL_updateShort) message).update
                            instanceof org.telegram.tgnet.tl.TL_update.TL_updateLoginToken;
                } else if (message instanceof TLRPC.TL_updates) {
                    for (TLRPC.Update update : ((TLRPC.TL_updates) message).updates) {
                        if (update instanceof org.telegram.tgnet.tl.TL_update.TL_updateLoginToken) {
                            nabdhQrApproval = true;
                            break;
                        }
                    }
                } else if (message instanceof TLRPC.TL_updatesCombined) {
                    for (TLRPC.Update update : ((TLRPC.TL_updatesCombined) message).updates) {
                        if (update instanceof org.telegram.tgnet.tl.TL_update.TL_updateLoginToken) {
                            nabdhQrApproval = true;
                            break;
                        }
                    }
                }
                if (nabdhQrApproval) {
                    AndroidUtilities.runOnUIThread(() -> NotificationCenter.getInstance(currentAccount)
                            .postNotificationName(NotificationCenter.nabdhQrTokenAccepted));
                }
                Utilities.stageQueue.postRunnable(() -> AccountInstance.getInstance(currentAccount).getMessagesController().processUpdates((TLRPC.Updates) message, false));"""
if connection.count(anchor) != 1:
    raise SystemExit("Telegram incoming update processing anchor changed")
connection = connection.replace(anchor, replacement, 1)
n.write_text(notification, encoding="utf-8")
c.write_text(connection, encoding="utf-8")
print("PASS: QR login token acceptance notification bridged without changing native MTProto updates")
