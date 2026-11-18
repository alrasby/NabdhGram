#!/usr/bin/env python3
"""Check NabdhGram is directly below Telegram Language, not inside Help.

Does not change/duplicate Telegram's native rows, categories or click handlers.
"""
from pathlib import Path
import sys

LANGUAGE = (
    "items.add(SettingCell.Factory.of(10, IconBackgroundColors.PURPLE.top, "
    "IconBackgroundColors.PURPLE.bottom, R.drawable.settings_language, "
    "getString(R.string.SettingsLanguage), LocaleController.getCurrentLanguageName()));"
)
NABDH = "items.add(SettingCell.Factory.of(80, IconBackgroundColors.CYAN.top,"
HELP = "items.add(UItem.asHeader(getString(R.string.SettingsHelp)));"
SHADOW = "items.add(UItem.asShadow(null));"
CLICK = "case 80:\n                presentSettingFragment(new NabdhGramSettingsActivity());"

def verify(s):
    if s.count(LANGUAGE) != 1 or s.count(NABDH) != 1:
        raise ValueError("Expected exactly one native Language and one NabdhGram row")
    if s.count(CLICK) != 1:
        raise ValueError("Lost or duplicated NabdhGram Settings click route")
    lang = s.index(LANGUAGE)
    nabdh = s.index(NABDH)
    next_sep = s.find(SHADOW, lang + len(LANGUAGE))
    if next_sep < 0 or not (lang < nabdh < next_sep):
        raise ValueError("NabdhGram Settings must be directly after Language")
    gap = s[lang + len(LANGUAGE):nabdh]
    if "items.add(" in gap or "asHeader(" in gap:
        raise ValueError("Unexpected Settings row or header separates Language and NabdhGram")
    if s.find(HELP, nabdh) < 0:
        raise ValueError("NabdhGram row must occur before Help, not inside Help")
    if "R.drawable.settings_features" not in s[nabdh:next_sep]:
        raise ValueError("NabdhGram should use native feature icon")

def selftest():
    snippet = ("\n" + LANGUAGE + "\n" + NABDH + "\n"
               + "                IconBackgroundColors.CYAN.bottom, R.drawable.settings_features,\n"
               + "                getString(R.string.NabdhGramSettingsTitle),"
               + " getString(R.string.NabdhGramFeaturesStatus)));\n"
               + SHADOW + "\n" + HELP + "\n" + CLICK + "\n")
    verify(snippet)
    try:
        verify(snippet.replace(LANGUAGE + "\n" + NABDH, NABDH + "\n" + LANGUAGE))
        raise AssertionError("wrong order not detected")
    except ValueError:
        pass
    try:
        verify(snippet.replace(NABDH, NABDH + "\n" + NABDH))
        raise AssertionError("duplicated row not detected")
    except ValueError:
        pass
    try:
        verify(snippet.replace(LANGUAGE + "\n" + NABDH, LANGUAGE + "\n"
                               + "items.add(UItem.asHeader(99));\n" + NABDH))
        raise AssertionError("intervening header not detected")
    except ValueError:
        pass
    print("PASS: main Settings native language -> NabdhGram, exactly one row, before Help")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        selftest()
    elif len(sys.argv) == 2:
        f = Path(sys.argv[1]) / (
            "TMessagesProj/src/main/java/org/telegram/ui/SettingsActivity.java")
        verify(f.read_text(encoding="utf-8"))
        print("PASS: NabdhGram Settings immediately below Telegram Language")
    else:
        raise SystemExit("Usage: check-nabdh-settings-entry.py TELEGRAM_SOURCE|--self-test")
