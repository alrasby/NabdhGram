#!/usr/bin/env python3
"""Focused P0 checks for exactly four existing bundled Telegram themes.

Run against the generated pinned Telegram checkout, not only the overlay script.
Do not imply these source checks prove runtime apply/persistence.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-theme-previews.py TELEGRAM_SOURCE")

root = Path(sys.argv[1]) / "TMessagesProj/src/main"
theme_source = (root / "java/org/telegram/ui/ActionBar/Theme.java").read_text(encoding="utf-8")
preview = (root / "java/org/telegram/ui/Cells/ThemesHorizontalListCell.java").read_text(encoding="utf-8")
filenames = (
    "nabdh_siri_refined.attheme",
    "nabdh_soft_mint.attheme",
    "nabdh_dark.attheme",
    "nabdh_sand.attheme",
)
assert len(filenames) == 4 and len(set(filenames)) == 4
for filename in filenames:
    assert (root / "assets" / filename).is_file(), filename + ": missing bundled asset"
    assert (root / "assets" / filename).stat().st_size > 100, filename + ": incomplete asset"
    assert theme_source.count('themeInfo.assetName = "' + filename + '";') == 1, filename + ": registration mismatch"

assert preview.count("private final Paint nabdhPreviewPaint = new Paint(Paint.ANTI_ALIAS_FLAG);") == 1
assert "Paint miniPaint = nabdhPreviewPaint;" in preview
assert "Paint miniPaint = new Paint(Paint.ANTI_ALIAS_FLAG);" not in preview
assert "miniPaint.setColor(blend(oldInColor, inColor));" in preview
assert "miniPaint.setColor(blend(oldOutColor, outColor));" in preview
assert "int previewBackground = blend(oldBackColor, backColor);" in preview
assert "miniPaint.setColor(previewInk);" in preview

# Protect the generated Java against literal newlines inside quoted strings.
# Python triple-quoted overlay sources must emit Java \\n, not a raw line break.
assert ('Sample conversation' + chr(92) + 'n      Last message') in preview, \
    "generated Java preview must contain an escaped newline"
assert ('محادثة تجريبية' + chr(92) + 'n      آخر رسالة') in preview, \
    "generated Arabic preview must contain an escaped newline"
assert ('Sample conversation' + chr(10) + '      Last message') not in preview, \
    "unclosed Java string literal in generated theme preview"

# Original native Telegram selection and theme edit/create paths must still exist.
assert "button.setColor(" in preview
assert "showOptionsForTheme(themeInfo);" in preview
assert "themesDict.put(themeInfo.getKey(), themeInfo);" in theme_source
# Phase 1/2: tap on bundled themes opens a preview and only explicit Apply
# uses Telegram's native selectTheme. Imported and Telegram themes are untouched.
assert 'tapped.assetName.startsWith("nabdh_")' in preview
assert "nabdhPreviewBundledTheme(tapped, view1);" in preview
assert "selectTheme(tapped, view1);" in preview
assert 'setPositiveButton(arabic ? "تطبيق" : "Apply"' in preview
assert "selectTheme(selected, tapped);" in preview
assert "getSharedPreferences(\"nabdh_theme_gallery\"" in preview
assert "Theme.getTheme(prefs.getString(key, \"\"))" in preview
assert "selectTheme(previous, null)" in preview
assert "getPreviewBackgroundColor()" in preview
assert "getPreviewInColor()" in preview
assert "getPreviewOutColor()" in preview
assert "AlertsCreator.createThemeCreateDialog" not in preview  # existing creation entry remains in ThemeActivity
print("PASS: exactly four owned themes retained, previews use stable palette and cached Paint; native selection preserved")
