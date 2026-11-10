#!/usr/bin/env python3
"""Dismiss only MTProxy-promoted chat rows using Telegram's own hidePromoDialog.

Do not alter other sponsored messages, PSAs, dialog ordering, swipe gestures,
Telegram connectivity or network transport.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-hide-proxy-promo.py TELEGRAM_SOURCE")
path = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java"
source = path.read_text(encoding="utf-8")

anchor = "    @Override\n    public void onResume() {"
if source.count(anchor) != 1:
    raise SystemExit("DialogsActivity resume hook changed")
helper = """    // Telegram itself manages promotional MTProxy peers and exposes
    // hidePromoDialog(); do not remove adapter rows or suppress PSA notices.
    // Remember the last handled peer to avoid repeated RPCs on list updates.
    private long nabdhLastProxyPromoAttemptAt;

    private void nabdhHideProxySponsorIfPresent() {
        if (folderId != 0 || communityId != 0 || viewPages == null
                || viewPages[0] == null
                || viewPages[0].dialogsType != DIALOGS_TYPE_DEFAULT) {
            return;
        }
        MessagesController controller = getMessagesController();
        if (controller.promoDialogType != MessagesController.PROMO_TYPE_PROXY) return;
        java.util.ArrayList<TLRPC.Dialog> visible =
                getDialogsArray(currentAccount, DIALOGS_TYPE_DEFAULT, 0, false);
        if (visible == null) return;
        // MTProxy promotion can move below pinned and archived rows.
        // Search every loaded row, never only the first five; only Telegram's
        // own promo flag qualifies. A user-pinned chat does not.
        for (int i = 0; i < visible.size(); ++i) {
            TLRPC.Dialog candidate = visible.get(i);
            if (candidate != null && controller.isPromoDialog(candidate.id, false)) {
                // Telegram may reintroduce the same sponsor after reconnect.
                // Re-attempt its native dismissal on reload and app resume,
                // with a 15-second guard against repeated requests.
                long now = android.os.SystemClock.elapsedRealtime();
                if (nabdhLastProxyPromoAttemptAt == 0
                        || now - nabdhLastProxyPromoAttemptAt >= 15000L) {
                    nabdhLastProxyPromoAttemptAt = now;
                    controller.hidePromoDialog();
                    // Telegram's own swipe-to-dismiss flow refreshes the
                    // adapter immediately after hidePromoDialog(). Without
                    // this, the promo cell remains visible until a reload.
                    android.os.Handler handler = new android.os.Handler(
                            android.os.Looper.getMainLooper());
                    handler.post(() -> {
                        if (viewPages != null && viewPages[0] != null
                                && getParentActivity() != null) {
                            viewPages[0].updateList(true);
                        }
                    });
                }
                return;
            }
        }
    }

"""
source = source.replace(anchor, helper + anchor, 1)

resume = "    public void onResume() {\n        super.onResume();"
if source.count(resume) != 1:
    raise SystemExit("DialogsActivity resume body changed")
source = source.replace(resume,
                        resume + "\n        nabdhHideProxySponsorIfPresent();", 1)

reload = "        if (id == NotificationCenter.dialogsNeedReload) {"
if source.count(reload) != 1:
    raise SystemExit("DialogsActivity reload branch changed")
source = source.replace(reload,
                        reload + "\n            nabdhHideProxySponsorIfPresent();", 1)

path.write_text(source, encoding="utf-8")
print("MTProxy promotional peers dismissed from loaded dialogs via Telegram native API.")
