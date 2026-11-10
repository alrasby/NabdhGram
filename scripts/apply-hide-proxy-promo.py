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
    private long nabdhLastProxyPromoId;

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
        // MTProxy promotion is normally placed at the top of the dialog list.
        for (int i = 0; i < Math.min(visible.size(), 5); ++i) {
            TLRPC.Dialog candidate = visible.get(i);
            if (candidate != null && controller.isPromoDialog(candidate.id, false)) {
                if (candidate.id != nabdhLastProxyPromoId) {
                    nabdhLastProxyPromoId = candidate.id;
                    controller.hidePromoDialog();
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
print("MTProxy promotional peers dismissed through Telegram native API only.")
