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
p.write_text(s, encoding="utf-8")
print("Contacts rounded selector applied.")
