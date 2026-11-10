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
            // NabdhGram: section labels are decorations, never adapter rows.
            // Never wrap disjoint pinned dialogs in a single tinted rectangle.
            if (viewPage.dialogsType == DIALOGS_TYPE_DEFAULT && folderId == 0 && communityId == 0) {
                viewPage.listView.addItemDecoration(new RecyclerView.ItemDecoration() {
                    private final Paint labelPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
                    private long cachedAt;
                    private int cachedCount = -1;
                    private int firstPinned = -1;
                    private int firstOther = -1;

                    {
                        labelPaint.setTextSize(dp(13));
                        labelPaint.setTypeface(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rregular.ttf"));
                    }

                    private void updateSections() {
                        int count = viewPage.dialogsAdapter.getItemCount();
                        long now = android.os.SystemClock.uptimeMillis();
                        if (cachedCount == count && now - cachedAt < 180) return;
                        cachedAt = now;
                        cachedCount = count;
                        firstPinned = -1;
                        firstOther = -1;
                        int lastPinned = -1;
                        for (int i = 0; i < count; i++) {
                            Object item = viewPage.dialogsAdapter.getItem(i);
                            if (!(item instanceof TLRPC.Dialog)) continue;
                            TLRPC.Dialog dialog = (TLRPC.Dialog) item;
                            if (dialog.isFolder) continue; // archive has its own native row
                            if (dialog.pinned) {
                                if (firstPinned < 0) firstPinned = i;
                                lastPinned = i;
                            }
                        }
                        if (lastPinned >= 0) {
                            for (int i = lastPinned + 1; i < count; i++) {
                                Object item = viewPage.dialogsAdapter.getItem(i);
                                if (item instanceof TLRPC.Dialog
                                        && !((TLRPC.Dialog) item).isFolder
                                        && !((TLRPC.Dialog) item).pinned) {
                                    firstOther = i;
                                    break;
                                }
                            }
                        }
                    }

                    private int sectionAt(int position) {
                        if (position == RecyclerView.NO_POSITION || position < 0) return 0;
                        Object row = viewPage.dialogsAdapter.getItem(position);
                        if (!(row instanceof TLRPC.Dialog) || ((TLRPC.Dialog) row).isFolder) return 0;
                        updateSections();
                        // Exactly one label for the first pinned row, and one
                        // after the last pinned row. No per-group repetitions.
                        if (position == firstPinned) return 1;
                        if (position == firstOther) return 2;
                        return 0;
                    }

                    @Override
                    public void getItemOffsets(Rect outRect, View child, RecyclerView parent,
                            RecyclerView.State state) {
                        int section = sectionAt(parent.getChildAdapterPosition(child));
                        if (section != 0) outRect.top = dp(25);
                    }

                    @Override
                    public void onDraw(Canvas canvas, RecyclerView parent, RecyclerView.State state) {
                        labelPaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText));
                        boolean rtl = org.telegram.messenger.LocaleController.isRTL;
                        labelPaint.setTextAlign(rtl ? Paint.Align.RIGHT : Paint.Align.LEFT);
                        float x = rtl ? parent.getWidth() - dp(18) : dp(18);
                        for (int i = 0; i < parent.getChildCount(); i++) {
                            View child = parent.getChildAt(i);
                            int section = sectionAt(parent.getChildAdapterPosition(child));
                            if (section == 0) continue;
                            String title = context.getString(section == 1
                                    ? R.string.NabdhGlassPinnedChats : R.string.NabdhGlassOtherChats);
                            canvas.drawText(title, x, child.getTop() - dp(8), labelPaint);
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
