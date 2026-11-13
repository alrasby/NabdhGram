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
s = s.replace(old, "view = new HeaderCell(context, 32, resourcesProvider);", 1)
old = "view = new HeaderCell(context, Theme.key_windowBackgroundWhiteBlackText, 17, 15, false, resourcesProvider);"
if s.count(old) != 1:
    raise SystemExit("UniversalAdapter black header anchor changed")
s = s.replace(old, "view = new HeaderCell(context, Theme.key_windowBackgroundWhiteBlackText, 32, 15, false, resourcesProvider);", 1)
p.write_text(s, encoding="utf-8")
print("Universal settings section headers now have consistent 24dp insets.")

# Experimental is upstream Telegram feature-gated, not a NabdhGram feature.
# Localize only its heading and retain the upstream setting actions intact.
settings = p.parent.parent / "SettingsActivity.java"
original = settings.read_text(encoding="utf-8")
old = 'items.add(UItem.asHeader("Experimental"));'
if original.count(old) != 1:
    raise SystemExit("Experimental settings heading anchor changed")
new = """items.add(UItem.asHeader(
                    org.telegram.messenger.LocaleController.getInstance().getCurrentLocale() != null
                    && "ar".equals(org.telegram.messenger.LocaleController.getInstance()
                            .getCurrentLocale().getLanguage())
                            ? "خيارات تجريبية" : "Experimental"));"""
settings.write_text(original.replace(old, new, 1), encoding="utf-8")
