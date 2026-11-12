#!/usr/bin/env python3
"""Apply rounded touch feedback to Telegram's contacts list, without changing data."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-contacts.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/ContactsActivity.java"
s = p.read_text(encoding="utf-8")
anchor = "        listView = new RecyclerListView(context);\n"
if s.count(anchor) != 1:
    raise SystemExit("Contacts list anchor changed")
s = s.replace(anchor, anchor + """        // NabdhGram Glass: use the existing Telegram selector with rounded
        // corners. No changes to contacts adapters, permissions or actions.
        listView.setSelectorRadius(17);
""", 1)
# The stock section decorator paints a single opaque WHITE wrapper behind
# every group, even though ContactsAdapter now draws independent Glass rows.
# Only disable the ornamental group background; leave the contacts adapter,
# indices, search and scroll handlers unchanged.
group = "        listView.setSections(true);"
if s.count(group) != 1:
    raise SystemExit("Contacts list section drawing changed")
s = s.replace(group, "        listView.disableSections();", 1)
p.write_text(s, encoding="utf-8")
print("Contacts standalone Glass rows without white section wrappers.")

# The RTL contacts badge is a SimpleTextView compound drawable.
# Give it enough intrinsic gap even with Readex Pro / Vazirmatn ascenders.
cell = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Cells/UserCell.java"
u = cell.read_text(encoding="utf-8")
needle = "        nameTextView.setTypeface(AndroidUtilities.bold());"
if u.count(needle) != 1:
    raise SystemExit("Contacts name badge spacing anchor changed")
u = u.replace(needle, """
        // Use the selected Regular typeface rather than forcing bold on all
        // contact names. Leave the native verification/premium drawable logic.
        nameTextView.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));
        nameTextView.setTextSize(15);
        nameTextView.setDrawablePadding(dp(13));""", 1)
cell.write_text(u, encoding="utf-8")
print("Contacts name/badge gap adjusted for RTL and variable fonts.")
