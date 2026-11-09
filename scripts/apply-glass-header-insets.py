#!/usr/bin/env python3
"""Give UniversalRecyclerView section headers consistent safe horizontal insets."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-header-insets.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Components/UniversalAdapter.java"
s = p.read_text(encoding="utf-8")
old = "view = new HeaderCell(context, resourcesProvider);"
if s.count(old) != 1:
    raise SystemExit("UniversalAdapter default section header anchor changed")
s = s.replace(old, "view = new HeaderCell(context, 24, resourcesProvider);", 1)
old = "view = new HeaderCell(context, Theme.key_windowBackgroundWhiteBlackText, 17, 15, false, resourcesProvider);"
if s.count(old) != 1:
    raise SystemExit("UniversalAdapter black header anchor changed")
s = s.replace(old, "view = new HeaderCell(context, Theme.key_windowBackgroundWhiteBlackText, 24, 15, false, resourcesProvider);", 1)
p.write_text(s, encoding="utf-8")
print("Universal settings section headers now have consistent 24dp insets.")
