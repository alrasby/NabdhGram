#!/usr/bin/env python3
"""Generated native-source contract for chat-settings screenshot regressions.

This test is deliberately narrow. A passing contract requires Android build and
physical AR/EN, LTR/RTL, day/night and theme QA before release.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-chat-settings-visual-fixes.py TELEGRAM_SOURCE")
ui = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"


def load(name):
    return (ui / name).read_text(encoding="utf-8")


def check(ok, text):
    if not ok:
        raise SystemExit("FAIL: " + text)


theme = load("ThemeActivity.java")
check(theme.count("if (holder.getItemViewType() == TYPE_APP_ICON) {") == 1,
      "icon picker clipping must remain limited to TYPE_APP_ICON")
check("holder.itemView.setClipToOutline(true);" in theme
      and "Math.max(insetX, view.getWidth() - insetX)" in theme
      and "AndroidUtilities.dp(20)" in theme,
      "inset Glass clipping/rounding is missing")

list_ui = load("Cells/ChatListCell.java")
check("int color = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText);" in list_ui,
      "chat-list sample is not high-contrast in the current theme")
check("Color.argb(a == 0 ? 200 : 145" in list_ui
      and "Color.argb(i == 0 ? 210 : 155" in list_ui,
      "mock conversation elements have regressed to low contrast")
check("didSelectChatType(isThreeLines)" in list_ui,
      "native two/three-line selection no longer works")

textcheck = load("Cells/TextCheckCell.java")
check(textcheck.count("Gravity.LEFT | Gravity.CENTER_VERTICAL, 22, 0, 22, 0") == 2,
      "TextCheckCell toggles are not both physically left-aligned")
check(textcheck.count("70, 0, padding, 0") == 2
      and "70, 35, padding, 0" in textcheck,
      "TextCheckCell LTR text gutter may overlap fixed-left switches")

textcheck2 = load("Cells/TextCheckCell2.java")
check("Gravity.LEFT | Gravity.CENTER_VERTICAL, 22, 0, 22, 0" in textcheck2
      and "LayoutHelper.createFrame(76, LayoutHelper.MATCH_PARENT, Gravity.LEFT)" in textcheck2,
      "expandable switch or its hit target is mirrored")
check("collapseViewContainer.setTranslationX(textView.getRight() + dp(8));" in textcheck2
      and "collapseViewContainer.setTranslationX(textView.getLeft() - collapseViewContainer.getMeasuredWidth() - dp(8));" in textcheck2,
      "upstream disclosure arrow translation must be preserved")

notifications = load("Cells/NotificationsCheckCell.java")
check("Gravity.LEFT | Gravity.CENTER_VERTICAL, 21, 0, 21, 0" in notifications
      and notifications.count("80,") >= 3,
      "switch rows missing left gutter in notifications/settings")
check("Gravity.RIGHT | Gravity.CENTER_VERTICAL, 8, 0, 8, 0" in notifications,
      "native with-image icon may overlap left switch")

check("addView(imageView, LayoutHelper.createFrame(29, 29, Gravity.RIGHT | Gravity.CENTER_VERTICAL" in textcheck
      and "((MarginLayoutParams)textView.getLayoutParams()).leftMargin = AndroidUtilities.dp(70)" in textcheck,
      "Icon-bearing TextCheckCell could overlap fixed-left toggle")

textcell = load("Cells/TextCell.java")
check(textcell.count("Gravity.LEFT | Gravity.CENTER_VERTICAL, 22, 0, 22, 0") == 2
      and "viewLeft = dp(22);" in textcell,
      "TextCell smooth-transitions switch must be physically left in both locales")
check("checkBox != null && checkBox.getVisibility() == VISIBLE ? 75" in textcell
      and "imageView.getVisibility() == VISIBLE ? 56 : 0" in textcell,
      "LTR TextCell title/icon clearance may overlap switch")

lite = load("LiteModeSettingsActivity.java")
check("Gravity.CENTER_VERTICAL | Gravity.LEFT, 19, 0, 19, 0" in lite,
      "Power Saver toggle not fixed left")
check("x > dp(19 + 37 + 19)" in lite,
      "Power Saver expanded-row hit target not moved with switch")
check("Gravity.RIGHT, 20, 0, 20, 0" in lite
      and "LocaleController.isRTL ? 8 : 64" in lite,
      "Power Saver icon/text layout risks colliding with left switch")
check("LiteMode.toggleFlag(item.flags, !value)" in lite,
      "Power Saver original toggle path modified")

print("PASS: source regressions for clipped icon strip, visible list previews, and left toggles")
