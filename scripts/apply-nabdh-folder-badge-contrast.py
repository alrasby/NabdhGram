#!/usr/bin/env python3
"""Contrast-safe folder counter labels, using each actual rendered badge fill."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-folder-badge-contrast.py TELEGRAM_SOURCE")
path = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java"
source = path.read_text(encoding="utf-8")
anchor = "                canvas.drawRoundRect(rect, 11.5f * AndroidUtilities.density, 11.5f * AndroidUtilities.density, counterPaint);"
if source.count(anchor) != 1:
    raise SystemExit("Pinned FilterTabsView counter background draw anchor changed")
replacement = """                // A badge's fill is animated between active/inactive colors.
                // Derive its digits from the CURRENT painted fill, not from a
                // fixed turquoise tab title. Both candidates are theme colors,
                // including imported .attheme palettes and dark mode.
                if (counterText != null) {
                    final int badgeFill = counterPaint.getColor();
                    final int themeSurface = Theme.getColor(
                            Theme.key_windowBackgroundWhite, resourcesProvider);
                    final int themeInk = Theme.getColor(
                            Theme.key_windowBackgroundWhiteBlackText, resourcesProvider);
                    final float badgeLuma = (android.graphics.Color.red(badgeFill) * 0.2126f
                            + android.graphics.Color.green(badgeFill) * 0.7152f
                            + android.graphics.Color.blue(badgeFill) * 0.0722f);
                    final float surfaceLuma = (android.graphics.Color.red(themeSurface) * 0.2126f
                            + android.graphics.Color.green(themeSurface) * 0.7152f
                            + android.graphics.Color.blue(themeSurface) * 0.0722f);
                    final float inkLuma = (android.graphics.Color.red(themeInk) * 0.2126f
                            + android.graphics.Color.green(themeInk) * 0.7152f
                            + android.graphics.Color.blue(themeInk) * 0.0722f);
                    textCounterPaint.setColor(Math.abs(badgeLuma - surfaceLuma)
                            > Math.abs(badgeLuma - inkLuma) ? themeSurface : themeInk);
                }
""" + anchor
source = source.replace(anchor, replacement, 1)
# Keep the folder-strip measurements consistent after title shortening.
# Never use the cached allTabsWidth to measure a title that just changed.
measure_old = """                firstTab.setTitle(LocaleController.getString(R.string.FilterAllChats), null, false);
                int tabWidth = firstTab.getWidth(false);
                firstTab.setTitle(allTabsWidth > width ? LocaleController.getString(R.string.FilterAllChatsShort) : LocaleController.getString(R.string.FilterAllChats), null, false);
                int trueTabsWidth = allTabsWidth - tabWidth;
                trueTabsWidth += firstTab.getWidth(false);
                int prevWidth = additionalTabWidth;
                additionalTabWidth = trueTabsWidth < width ? (width - trueTabsWidth) / tabs.size() : 0;
                if (prevWidth != additionalTabWidth) {"""
measure_new = """                final String previousTitle = firstTab.title.toString();
                firstTab.setTitle(LocaleController.getString(R.string.FilterAllChats), null, false);
                int fullTabsWidth = 0;
                for (int i = 0; i < tabs.size(); i++) {
                    fullTabsWidth += tabs.get(i).getWidth(false) + dp(TAB_PADDING_WIDTH);
                }
                final boolean needsShortTitle = fullTabsWidth > width;
                firstTab.setTitle(needsShortTitle
                        ? LocaleController.getString(R.string.FilterAllChatsShort)
                        : LocaleController.getString(R.string.FilterAllChats), null, false);
                final boolean changedTitle = !android.text.TextUtils.equals(
                        previousTitle, firstTab.title);
                int trueTabsWidth = 0;
                for (int i = 0; i < tabs.size(); i++) {
                    trueTabsWidth += tabs.get(i).getWidth(false) + dp(TAB_PADDING_WIDTH);
                }
                allTabsWidth = trueTabsWidth;
                int prevWidth = additionalTabWidth;
                additionalTabWidth = trueTabsWidth < width ? (width - trueTabsWidth) / tabs.size() : 0;
                if (changedTitle || prevWidth != additionalTabWidth) {"""
if source.count(measure_old) != 1:
    raise SystemExit("Pinned FilterTabsView measurement anchor changed")
source = source.replace(measure_old, measure_new, 1)
path.write_text(source, encoding="utf-8")
print("PASS: native folder badge text adapts contrast to current animated badge fill")
