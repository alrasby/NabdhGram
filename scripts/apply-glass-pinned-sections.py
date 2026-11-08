#!/usr/bin/env python3
"""Add visible pinned and regular chat headers to the default dialogs list.

Reuse Telegram's existing HeaderCell and ItemInternal.pinned state; never
reorder messages or create a second adapter. Restricted to the main dialog list.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-pinned-sections.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
p = root / "TMessagesProj/src/main/java/org/telegram/ui/Adapters/DialogsAdapter.java"
s = p.read_text(encoding="utf-8")
anchor = """        if (!messagesController.hiddenUndoChats.isEmpty()) {
            for (int i = 0; i < itemInternals.size(); ++i) {
                ItemInternal item = itemInternals.get(i);
                if (item.viewType == VIEW_TYPE_DIALOG && item.dialog != null && messagesController.isHiddenByUndo(item.dialog.id)) {
                    itemInternals.remove(i);
                    i--;
                }
            }
        }
    }

    public int getItemHeight(int position) {"""
if s.count(anchor) != 1:
    raise SystemExit("Pinned header injection anchor changed")
replacement = """        if (!messagesController.hiddenUndoChats.isEmpty()) {
            for (int i = 0; i < itemInternals.size(); ++i) {
                ItemInternal item = itemInternals.get(i);
                if (item.viewType == VIEW_TYPE_DIALOG && item.dialog != null && messagesController.isHiddenByUndo(item.dialog.id)) {
                    itemInternals.remove(i);
                    i--;
                }
            }
        }

        // NabdhGram Glass: visually separate pinned and ordinary chats.
        // Only the real home list, never forwarding/search/folders/selectors.
        if (dialogsType == DialogsActivity.DIALOGS_TYPE_DEFAULT && folderId == 0
                && requestPeerType == null && (filter == null || filter.isDefault())
                && !collapsedView && !isTransitionSupport && parentFragment != null
                && !parentFragment.isReplyTo) {
            int pinnedFirst = -1;
            int regularFirst = -1;
            boolean seenPinned = false;
            for (int i = 0; i < itemInternals.size(); ++i) {
                ItemInternal row = itemInternals.get(i);
                if (row.viewType != VIEW_TYPE_DIALOG || row.dialog == null || row.isFolder) {
                    continue;
                }
                if (row.pinned) {
                    if (pinnedFirst < 0) {
                        pinnedFirst = i;
                    }
                    seenPinned = true;
                } else if (seenPinned) {
                    regularFirst = i;
                    break;
                }
            }
            if (pinnedFirst >= 0 && regularFirst > pinnedFirst) {
                // Insert from the end to preserve original list indices and order.
                itemInternals.add(regularFirst, new ItemInternal(VIEW_TYPE_HEADER_3,
                        mContext.getString(org.telegram.messenger.R.string.NabdhGlassAllChats)));
                itemInternals.add(pinnedFirst, new ItemInternal(VIEW_TYPE_HEADER_3,
                        mContext.getString(org.telegram.messenger.R.string.NabdhGlassPinnedChats)));
            }
        }
    }

    public int getItemHeight(int position) {"""
s = s.replace(anchor, replacement, 1)
p.write_text(s, encoding="utf-8")

# The existing feature settings resources are created earlier in the workflow.
from xml.sax.saxutils import escape
for lang, pinned, regular in [
    ("values", "Pinned chats", "All chats"),
    ("values-ar", "المحادثات المثبتة", "جميع المحادثات"),
]:
    f = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    x = f.read_text(encoding="utf-8")
    if x.count("</resources>") != 1:
        raise SystemExit("NabdhGram strings resources changed: " + str(f))
    x = x.replace("</resources>",
        '    <string name="NabdhGlassPinnedChats">' + escape(pinned) + '</string>\n' +
        '    <string name="NabdhGlassAllChats">' + escape(regular) + '</string>\n</resources>')
    f.write_text(x, encoding="utf-8")
print("Installed pinned and regular chat headers on the main dialogs list.")
