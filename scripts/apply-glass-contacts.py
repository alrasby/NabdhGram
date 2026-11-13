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
# IMPORTANT: preserve Telegram's native Contacts section decorator and all
# offsets/fast scroll/clip behavior; hiding the decorator itself previously
# coincided with the app restarting on Contacts. Suppress ONLY its opaque
# background paint, since ContactsAdapter paints individual Glass cells.
legacy_group = "        listView.setSections(true);"
current_group = "        listView.setSections();"
if s.count(legacy_group) == 1:
    group = legacy_group
elif s.count(current_group) == 1:
    # Telegram 13.2.x updates the sticky section API and sets the section
    # type separately. Keep that native setup; only suppress its opaque fill.
    group = current_group
else:
    raise SystemExit("Telegram Contacts section initialization changed")
s = s.replace(group, group + "\n        listView.nabdhHideSectionBackgroundOnly();", 1)
p.write_text(s, encoding="utf-8")

# The shared Glass engine (apply-glass-settings-surfaces.py) owns
# nabdhHideSectionBackgroundOnly(), so there is exactly ONE Java declaration.
print("Contacts sections preserved; the shared engine suppresses group fill.")

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
