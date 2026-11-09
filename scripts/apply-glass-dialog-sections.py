#!/usr/bin/env python3
"""Add visual pinned/all chat sections without inserting RecyclerView adapter rows.

Preserves Telegram dialog positions, sorting, drag-to-reorder and swipe actions.
Only applies to the default main chats list, not archive/search/picker views.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-dialog-sections.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
page = root / "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java"
s = page.read_text(encoding="utf-8")
anchor = "            viewPage.listView.setAdapter(viewPage.dialogsAdapter);"
if s.count(anchor) != 1:
    raise SystemExit(f"Unexpected DialogsActivity adapter anchor: {s.count(anchor)}")

# RecyclerView.ItemDecoration adds visual space but NEVER creates adapter rows,
# preserving the Telegram adapter's position-to-dialog mapping.
addition = r'''
            // NabdhGram Glass: visual section headers without adapter items.
            // Inserting adapter headers would break Telegram's fixPosition() mapping
            // used by drag/reorder; decoration preserves all existing indices.
            if (viewPage.dialogsType == DIALOGS_TYPE_DEFAULT && folderId == 0 && communityId == 0) {
                viewPage.listView.addItemDecoration(new RecyclerView.ItemDecoration() {
                    private final Paint labelPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
                    private final Paint pinnedGroupPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
                    {
                        labelPaint.setTextSize(dp(14));
                        labelPaint.setTypeface(android.graphics.Typeface.create(
                                "sans-serif-medium", android.graphics.Typeface.NORMAL));
                    }

                    private int sectionAt(int position) {
                        if (position == RecyclerView.NO_POSITION || position < 0) {
                            return 0;
                        }
                        Object current = viewPage.dialogsAdapter.getItem(position);
                        if (!(current instanceof TLRPC.Dialog)) {
                            return 0;
                        }
                        boolean pinned = ((TLRPC.Dialog) current).pinned;
                        Object previous = position > 0 ? viewPage.dialogsAdapter.getItem(position - 1) : null;
                        boolean wasPinned = previous instanceof TLRPC.Dialog
                                && ((TLRPC.Dialog) previous).pinned;
                        if (pinned && !wasPinned) return 1;
                        if (!pinned && wasPinned) return 2;
                        return 0;
                    }

                    @Override
                    public void getItemOffsets(Rect outRect, View view, RecyclerView parent, RecyclerView.State state) {
                        int position = parent.getChildAdapterPosition(view);
                        if (sectionAt(position) != 0) {
                            outRect.top = dp(34);
                        }
                    }

                    @Override
                    public void onDraw(Canvas canvas, RecyclerView parent, RecyclerView.State state) {
                        labelPaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
                        boolean rtl = org.telegram.messenger.LocaleController.isRTL;
                        labelPaint.setTextAlign(rtl ? Paint.Align.RIGHT : Paint.Align.LEFT);
                        float x = rtl ? parent.getWidth() - dp(20) : dp(20);
                        // Paint behind visible pinned rows; do not change adapter indices.
                        int groupTop = Integer.MAX_VALUE;
                        int groupBottom = Integer.MIN_VALUE;
                        for (int i = 0; i < parent.getChildCount(); i++) {
                            View child = parent.getChildAt(i);
                            int position = parent.getChildAdapterPosition(child);
                            Object item = position == RecyclerView.NO_POSITION
                                    ? null : viewPage.dialogsAdapter.getItem(position);
                            if (item instanceof TLRPC.Dialog && ((TLRPC.Dialog) item).pinned) {
                                groupTop = Math.min(groupTop, child.getTop());
                                groupBottom = Math.max(groupBottom, child.getBottom());
                            }
                        }
                        if (groupTop < groupBottom) {
                            int surface = Theme.getColor(Theme.key_windowBackgroundWhite);
                            boolean dark = android.graphics.Color.red(surface)
                                    + android.graphics.Color.green(surface)
                                    + android.graphics.Color.blue(surface) < 360;
                            pinnedGroupPaint.setColor(dark ? 0xFF103E46 : 0xFFE4F5F3);
                            canvas.drawRoundRect(dp(4), groupTop + dp(2),
                                    parent.getWidth() - dp(4), groupBottom - dp(2),
                                    dp(20), dp(20), pinnedGroupPaint);
                        }
                        for (int i = 0; i < parent.getChildCount(); i++) {
                            View child = parent.getChildAt(i);
                            int section = sectionAt(parent.getChildAdapterPosition(child));
                            if (section != 0) {
                                String title = context.getString(section == 1
                                        ? R.string.NabdhGlassPinnedChats : R.string.NabdhGlassOtherChats);
                                canvas.drawText(title, x, child.getTop() - dp(12), labelPaint);
                            }
                        }
                    }
                });
            }
'''
s = s.replace(anchor, anchor + addition, 1)
page.write_text(s, encoding="utf-8")

for locale, labels in [
    ("values", ("Pinned chats", "Other chats")),
    ("values-ar", ("المحادثات المثبتة", "بقية المحادثات")),
]:
    f = root / "TMessagesProj/src/main/res" / locale / "nabdhgram_settings.xml"
    xml = f.read_text(encoding="utf-8")
    if xml.count("</resources>") != 1:
        raise SystemExit(f"Unexpected resource closing tag: {f}")
    additions = (f'    <string name="NabdhGlassPinnedChats">{escape(labels[0])}</string>\n'
                 f'    <string name="NabdhGlassOtherChats">{escape(labels[1])}</string>\n')
    f.write_text(xml.replace("</resources>", additions + "</resources>", 1), encoding="utf-8")
print("NabdhGram Glass pinned/regular sections installed without changing adapter ordering.")
