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
assert "Theme.getThemeFileValues(null, selected.assetName, null)" in preview
assert "palette.get(Theme.key_chat_inBubble" in preview
assert "palette.get(Theme.key_chat_outBubble" in preview
assert "if (!nabdhCanReadThemeFile(file)" in theme_source
assert "options.inJustDecodeBounds = true;" in theme_source
assert "options.outWidth * options.outHeight <= 24_000_000L" in theme_source
assert "AlertsCreator.createThemeCreateDialog" not in preview  # existing creation entry remains in ThemeActivity
# Phase 2: full preview with real local embedded asset wallpaper,
# bounded decode, explicit clone, and native persistent theme selection.
assert "nabdhBundledWallpaper(application, selected)" in preview
assert "context.getAssets().open(theme.assetName)" in preview
assert "total > 5 * 1024 * 1024" in preview
assert "android.graphics.BitmapFactory.decodeByteArray" in preview
assert "preview.setClipToOutline(true);" in preview
assert "!preview.isAttachedToWindow()" in preview
assert "bitmap.getAllocationByteCount()" in preview
assert "Utilities.globalQueue.postRunnable" in preview
assert "new android.widget.ScrollView(context)" in preview
assert "shown[0] = dialog.create();" in preview
assert '"Personal copy"' in preview
assert "Theme.getAssetFile(selected.assetName)" in preview
assert "Theme.applyThemeFile(" in preview
assert "new org.telegram.ui.Components.ThemeEditorView()" in preview
assert '"previousNightTheme" : "previousDayTheme"' in preview
assert "selectTheme(previous, null)" in preview
assert '"themeconfig"' in preview, "native Telegram themeconfig must remain the persistence source"
assert '"lastDarkTheme" : "lastDayTheme"' in preview
assert "Theme.switchThemeWithReveal(themeInfo, false, -1, from)" in preview
assert "Theme.setCurrentNightTheme(themeInfo)" in preview
assert "EmojiThemes.saveCustomTheme(themeInfo, themeInfo.currentAccentId)" in preview
# Final V2 gallery checks: do not mutate imported assets or change
# native selection. Defaults must come from Telegram's own registered IDs.
assert 'Theme.getTheme(night ? "Night" : "Blue")' in preview
assert 'selectTheme(defaultChoice, null)' in preview
assert 'nabdhRememberTheme(prefs, key, before);' in preview
assert 'previous.setCurrentAccentId(previousAccent);' in preview
assert 'content.addView(mock, 0, block);' in preview
assert '"Restore Telegram default theme"' in preview
assert 'for (int pos = cardName.indexOf(' in preview
assert 'Math.max(a, b)' in preview
assert 'TextUtils.ellipsize(first, textPaint, maxWidth' in preview
assert 'TextUtils.ellipsize(second, textPaint, maxWidth' in preview
assert 'Theme.getCurrentNightTheme() : Theme.getCurrentTheme()' in preview
assert "fixed.addView(mock, block)" in preview
assert "content.removeView(mock)" in preview
assert ".setView(fixed)" in preview
assert '"Name personal copy"' in preview
assert 'android.app.AlertDialog' not in preview
assert 'Theme.getColor(Theme.key_dialogTextBlack)' in preview
assert 'Theme.createEditTextDrawable(context, true)' in preview
assert 'String copyName = chosen + ".attheme";' in preview
assert "Theme.getTheme(copyName)" in preview
assert "nabdhInvalidThemeName(chosen)" in preview
assert 'String copyName = "Nabdh Personal "' not in preview
prefs = (root / "java/org/telegram/ui/Components/NabdhAppearancePrefs.java").read_text(encoding="utf-8")
surface = (root / "java/org/telegram/ui/Components/NabdhGlassRowDecoration.java").read_text(encoding="utf-8")
category = (root / "java/org/telegram/ui/NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
assert '"ui_style_v2"' in prefs
assert "DEFAULT_UI_STYLE = UI_HYBRID" in prefs
assert ".getInt(UI_STYLE, DEFAULT_UI_STYLE)" in prefs
assert 'putInt(UI_STYLE, style)' in prefs
assert 'NabdhAppearancePrefs.surfaceRadius()' in surface
assert 'NabdhAppearancePrefs.glassSurface()' in surface
assert 'NabdhAppearancePrefs.setUiStyle(context, which)' in category
print("PASS: exactly four owned themes retained, previews use stable palette and cached Paint; native selection preserved")

# Verify real locale resolution and shared style integration in generated source.
message_preview = (root / "java/org/telegram/ui/Cells/ThemePreviewMessagesCell.java").read_text(encoding="utf-8")
assert "nabdhMuscatPreviewLine()" in message_preview
assert "LocaleController.getInstance().getCurrentLocale()" in message_preview
assert "الوقت صباح هنا في مسقط" in message_preview
assert message_preview.index('"ar".equals(locale.getLanguage())') < message_preview.index("String nativeSample =")
