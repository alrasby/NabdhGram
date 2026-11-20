#!/usr/bin/env python3
"""Use readable theme-aware icon colors for the chats selection action bar only."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-selection-toolbar.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java"
s = p.read_text(encoding="utf-8")
def change(before, after, count=1):
    global s
    actual = s.count(before)
    if actual != count:
        raise SystemExit(f"Selection bar upstream anchor changed: {before[:75]} ({actual}/{count})")
    s = s.replace(before, after)

# The light Glass selection scrim was paired with Telegram's always-white
# actionBarActionModeDefaultIcon. Bind the foreground to the actual theme text
# color, which remains legible in both light and dark imported .attheme files.
change("ThemeBind.actionBarItemsColor(actionBar, Theme.key_actionBarActionModeDefaultIcon, getResourceProvider(), true);",
       "ThemeBind.actionBarItemsColor(actionBar, Theme.key_windowBackgroundWhiteBlackText, getResourceProvider(), true);")
change("ThemeBind.colorFilter(actionModeCloseView, Theme.key_actionBarActionModeDefaultIcon, getResourceProvider(), PorterDuff.Mode.MULTIPLY);",
       "ThemeBind.colorFilter(actionModeCloseView, Theme.key_windowBackgroundWhiteBlackText, getResourceProvider(), PorterDuff.Mode.MULTIPLY);")
change("selectedDialogsCountTextView.setTextColor(getThemedColor(Theme.key_actionBarActionModeDefaultIcon));",
       "selectedDialogsCountTextView.setTextColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText));", 2)
change("new ThemeDescription(selectedDialogsCountTextView, ThemeDescription.FLAG_TEXTCOLOR, null, null, null, null, Theme.key_actionBarActionModeDefaultIcon)",
       "new ThemeDescription(selectedDialogsCountTextView, ThemeDescription.FLAG_TEXTCOLOR, null, null, null, null, Theme.key_windowBackgroundWhiteBlackText)")
change("actionBar.setItemsColor(ColorUtils.blendARGB(getThemedColor(Theme.key_actionBarActionModeDefaultIcon), getThemedColor(Theme.key_actionBarActionModeDefaultIcon), searchAnimationProgress), true);",
       "actionBar.setItemsColor(getThemedColor(Theme.key_windowBackgroundWhiteBlackText), true);")
p.write_text(s, encoding="utf-8")
print("PASS: chats selection toolbar uses adaptive theme foreground, callbacks unchanged")
