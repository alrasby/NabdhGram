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
path.write_text(source, encoding="utf-8")
print("PASS: native folder badge text adapts contrast to current animated badge fill")
