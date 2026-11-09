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
            for (int i = 0; i < itemInternals.size(); ++i) {
                ItemInternal row = itemInternals.get(i);
                if (row.viewType != VIEW_TYPE_DIALOG || row.dialog == null || row.isFolder) {
                    continue;
                }
                if (row.pinned && pinnedFirst < 0) {
                    pinnedFirst = i;
                }
                if (!row.pinned && regularFirst < 0) {
                    regularFirst = i;
                }
            }
            // Telegram normally puts pinned chats before regular chats.
            // If another list mode violates that assumption, avoid misleading
            // section labels rather than pretending the list is regrouped.
            boolean ordered = pinnedFirst < 0 || regularFirst < 0
                    || pinnedFirst < regularFirst;
            // Folder-specific lists and transient reorder states can have
            // pinned dialogs after ordinary ones. Avoid incorrect sections.
            if (regularFirst >= 0) {
                for (int i = regularFirst + 1; i < itemInternals.size(); ++i) {
                    ItemInternal row = itemInternals.get(i);
                    if (row.viewType == VIEW_TYPE_DIALOG && row.dialog != null
                            && !row.isFolder && row.pinned) {
                        ordered = false;
                        break;
                    }
                }
            }
            // Insert from the end to preserve original dialog indices.
            if (ordered && regularFirst >= 0 && (pinnedFirst < 0 || regularFirst > pinnedFirst)) {
                itemInternals.add(regularFirst, new ItemInternal(VIEW_TYPE_HEADER_3,
                        mContext.getString(org.telegram.messenger.R.string.NabdhGlassAllChats)));
            }
            if (ordered && pinnedFirst >= 0) {
                itemInternals.add(pinnedFirst, new ItemInternal(VIEW_TYPE_HEADER_3,
                        mContext.getString(org.telegram.messenger.R.string.NabdhGlassPinnedChats)));
            }
        }
    }

    public int getItemHeight(int position) {"""
s = s.replace(anchor, replacement, 1)
# Style only the two added headers; reuse upstream HeaderCell and RTL logic.
header_anchor = """            case VIEW_TYPE_HEADER_3: {
                HeaderCell cell = (HeaderCell) holder.itemView;
                cell.setText((String) getItem(i));
                break;
            }"""
if s.count(header_anchor) != 1:
    raise SystemExit("HeaderCell bind anchor changed")
s = s.replace(header_anchor, """            case VIEW_TYPE_HEADER_3: {
                HeaderCell cell = (HeaderCell) holder.itemView;
                String heading = (String) getItem(i);
                cell.setText(heading);
                boolean nabdhHeading = dialogsType == DialogsActivity.DIALOGS_TYPE_DEFAULT && folderId == 0
                        && (heading.equals(mContext.getString(org.telegram.messenger.R.string.NabdhGlassPinnedChats))
                        || heading.equals(mContext.getString(org.telegram.messenger.R.string.NabdhGlassAllChats)));
                if (nabdhHeading) {
                    int base = Theme.getColor(Theme.key_windowBackgroundWhite);
                    boolean dark = android.graphics.Color.red(base) + android.graphics.Color.green(base)
                            + android.graphics.Color.blue(base) < 360;
                    android.graphics.drawable.GradientDrawable bg = new android.graphics.drawable.GradientDrawable();
                    bg.setColor(dark ? 0xFF103D44 : 0xFFE4F6F4);
                    bg.setCornerRadius(AndroidUtilities.dp(15));
                    bg.setStroke(AndroidUtilities.dp(1), dark ? 0xFF287C84 : 0xFFBADFDD);
                    cell.setBackground(bg);
                    cell.setTextColor(dark ? 0xFF72E5DE : 0xFF087C83);
                    cell.setPadding(AndroidUtilities.dp(8), 0, AndroidUtilities.dp(8), 0);
                } else {
                    cell.setBackground(null);
                    cell.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueHeader));
                    cell.setPadding(0, 0, 0, 0);
                }
                break;
            }""", 1)
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
    # The Glass settings overlay already defines NabdhGlassPinnedChats.
    # Reuse it instead of creating a duplicate Android string resource.
    import xml.etree.ElementTree as ET
    existing = [e.attrib.get("name") for e in ET.fromstring(x).findall("string")]
    if existing.count("NabdhGlassPinnedChats") != 1:
        raise SystemExit("Existing Glass pinned heading must occur exactly once: " + str(f))
    if "NabdhGlassAllChats" in existing:
        raise SystemExit("Glass all-chats heading unexpectedly exists: " + str(f))
    x = x.replace("</resources>",
        '    <string name="NabdhGlassAllChats">' + escape(regular) + '</string>\n</resources>')
    f.write_text(x, encoding="utf-8")
print("Installed pinned and regular chat headers on the main dialogs list.")
