#!/usr/bin/env python3
"""Generated-Java QA gate for profile press masking and single-layer chat input.

This cannot replace Android screenshots. Exact native-source assertions catch
the two regressions before starting Gradle's full C++ build.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-profile-composer-visual-fixes.py TELEGRAM_SOURCE")
ui = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"


def check(test, label):
    if not test:
        raise SystemExit("FAIL: " + label)


about = (ui / "Cells/AboutLinkCell.java").read_text(encoding="utf-8")
profile = (ui / "ProfileActivity.java").read_text(encoding="utf-8")
composer = (ui / "Components/ChatActivityEnterView.java").read_text(encoding="utf-8")

check(about.count("rippleBackground = new android.graphics.drawable.RippleDrawable(") == 1
      and "nabdhMask.setCornerRadius(org.telegram.messenger.AndroidUtilities.dp(20))" in about
      and about.count("org.telegram.messenger.AndroidUtilities.dp(10)") >= 2
      and about.count("org.telegram.messenger.AndroidUtilities.dp(2)") >= 2,
      "profile biography ripple mask is not inset to rounded Glass card")
check("if (container.getBackground() != null)" in about
      and "container.setBackground(rippleBackground);" in about
      and "if (!nabdhProfileGlass && viewAlpha > 0)" in about,
      "profile link/expansion/shadow original behavior is not preserved")
check(profile.count(".setRoundRadius(") >= 3
      and profile.count("NabdhGlassRowDecoration.isGlassCard(view)") >= 6
      and profile.count("NabdhGlassRowDecoration.newProfileScrim()") == 3,
      "profile long-press menu clone not clipped to the Glass card")

check("messageEditText.setBackgroundDrawable(null);" in composer
      and "messageEditText.setBackground(nabdhInputGlass)" not in composer
      and "nabdhInputGlass.setCornerRadius" not in composer
      and "nabdhComposerSurface" not in composer,
      "message editor has duplicate bright pill over native Telegram input panel")
check("messageEditText.setPadding(0, dp(9), 0, dp(10));" in composer
      and "messageEditText.setPadding(dp(6)" not in composer
      and "messageEditText.setSupportRtlHint(true)" in composer
      and "messageEditText.setGravity(Gravity.BOTTOM);" in composer
      and "messageEditText.setGravity((org.telegram" not in composer
      and "messageEditText.setTextDirection(android.view.View.TEXT_DIRECTION_FIRST_STRONG);" not in composer
      and "leftMargin = dp(10) + (botCommandsMenuButton" in composer
      and "leftMargin = dp(57) + (botCommandsMenuButton" in composer
      and "leftMargin = dp(66) + (botCommandsMenuButton" not in composer,
      "native bot menu margins, gravity and RTL custom hint support missing")
check("messageEditText.getHintLayoutEx() != null" in composer
      and 'messageEditText.setHintText("", false);' in composer
      and "updateFieldHint(false);" in composer,
      "typeface refresh fails to recreate the cached Arabic hint StaticLayout")
check("ThemeBind.textColor(messageEditText, Theme.key_chat_messagePanelText, resourcesProvider)" in composer
      and "nabdhRefreshComposerFont();" in composer
      and "messageEditText.setTypeface(chosen, bold" in composer,
      "native live-theme binding or immediate font refresh changed")
bot_menu = (ui / "bots/BotCommandsMenuView.java").read_text(encoding="utf-8")
check("menuTextLayout.getLineLeft(0)" in bot_menu
      and "canvas.translate(AndroidUtilities.dp(34) - menuTextLayout.getLineLeft(0)" in bot_menu
      and "canvas.clipRect(0, 0, getMeasuredWidth(), getMeasuredHeight())" in bot_menu
      and "menuTextWidth = menuTextLayout.getLineCount() > 0 ? menuTextLayout.getLineWidth(0)" in bot_menu
      and "if (expanded)" in bot_menu,
      "Arabic bot menu label must stay inside its measured button, never overlap message hint")
print("PASS: rounded Profile Glass press effects and one native-theme chat composer")
