#!/usr/bin/env python3
"""Subtle rounded Glass surface for Telegram's message entry field.

Only changes the edit field drawable; does not alter message handling, attachments,
voice recording, send actions, text selection or keyboard behavior.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-chat-composer.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java"
s = p.read_text(encoding="utf-8")
anchor = """        messageEditText.setBackgroundDrawable(null);
        messageEditText.setTextColor(getThemedColor(Theme.key_chat_messagePanelText));"""
if s.count(anchor) != 1:
    raise SystemExit("Message entry background anchor changed")
replacement = """        // NabdhGram Glass: light, theme-aware input surface. Keep the
        // original edit field and all of its behavior unchanged.
        final int nabdhInputSurface = getThemedColor(Theme.key_chat_messagePanelBackground);
        final boolean nabdhDarkInput = android.graphics.Color.red(nabdhInputSurface)
                + android.graphics.Color.green(nabdhInputSurface)
                + android.graphics.Color.blue(nabdhInputSurface) < 360;
        android.graphics.drawable.GradientDrawable nabdhInputGlass =
                new android.graphics.drawable.GradientDrawable();
        nabdhInputGlass.setShape(android.graphics.drawable.GradientDrawable.RECTANGLE);
        nabdhInputGlass.setColor(nabdhDarkInput ? 0xFF203740 : 0xFFE5F3F2);
        nabdhInputGlass.setCornerRadius(dp(19));
        nabdhInputGlass.setStroke(dp(1), nabdhDarkInput ? 0xFF39727A : 0xFFBDDAD8);
        messageEditText.setBackground(nabdhInputGlass);
        // Restore Telegram's vertical insets: the EditText is measured
        // independently of the panel and must retain its 9/10dp padding.
        messageEditText.setPadding(0, dp(9), 0, dp(10));
        // Align the empty hint with the application language (RTL Arabic),
        // while FIRST_STRONG keeps mixed-direction typed text readable.
        messageEditText.setGravity((org.telegram.messenger.LocaleController.isRTL
                ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT)
                | android.view.Gravity.BOTTOM);
        messageEditText.setTextDirection(android.view.View.TEXT_DIRECTION_FIRST_STRONG);
        messageEditText.setTextColor(getThemedColor(Theme.key_chat_messagePanelText));"""
s=s.replace(anchor,replacement,1)
p.write_text(s,encoding="utf-8")
print("Glass message entry surface applied.")
