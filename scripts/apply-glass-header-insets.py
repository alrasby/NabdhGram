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
native_localized = 'items.add(UItem.asHeader(getString(R.string.SettingsExperimental)));'
if original.count(old) == 1:
    # Older Telegram baseline: manual Arabic fallback.
    new = """items.add(UItem.asHeader(
                    org.telegram.messenger.LocaleController.getInstance().getCurrentLocale() != null
                    && "ar".equals(org.telegram.messenger.LocaleController.getInstance()
                            .getCurrentLocale().getLanguage())
                            ? "خيارات تجريبية" : "Experimental"));"""
    settings.write_text(original.replace(old, new, 1), encoding="utf-8")
elif original.count(native_localized) == 1:
    # Telegram 13.2.2 already ships this label through its own locale
    # resources. Never overwrite a correctly localized upstream string.
    print("PASS: upstream Experimental header already localized")
else:
    raise SystemExit("Experimental settings heading anchor changed")
