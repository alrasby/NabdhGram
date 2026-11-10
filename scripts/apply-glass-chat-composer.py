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
        final int nabdhInputAccent = getThemedColor(Theme.key_chat_messagePanelText);
        android.graphics.drawable.GradientDrawable nabdhInputGlass =
                new android.graphics.drawable.GradientDrawable();
        nabdhInputGlass.setShape(android.graphics.drawable.GradientDrawable.RECTANGLE);
        // Resolve the editable surface from the active Telegram palette.
        // No hard-coded mint/dark background: imported themes remain visible.
        nabdhInputGlass.setColor(nabdhInputSurface);
        nabdhInputGlass.setCornerRadius(dp(19));
        nabdhInputGlass.setStroke(dp(1), android.graphics.Color.argb(65,
                android.graphics.Color.red(nabdhInputAccent),
                android.graphics.Color.green(nabdhInputAccent),
                android.graphics.Color.blue(nabdhInputAccent)));
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
        // EditTextBoldCursor draws hints on its own canvas, independently
        // of Android TextView gravity. Enable its native RTL hint positioning.
        messageEditText.setSupportRtlHint(true);
        nabdhRefreshComposerFont();
        messageEditText.setTextColor(getThemedColor(Theme.key_chat_messagePanelText));"""
s=s.replace(anchor,replacement,1)

resume_anchor = """    public void onResume() {
        isPaused = false;"""
if s.count(resume_anchor) != 1:
    raise SystemExit("ChatActivityEnterView resume anchor changed")
resume_replacement = """    // Read persisted typography for both the message and its localized hint.
    // Refresh on return to an existing chat, not just on initial construction.
    private String nabdhAppliedComposerFamily;

    private void nabdhRefreshComposerFont() {
        if (messageEditText == null) {
            return;
        }
        String family = getContext().getSharedPreferences(
                "nabdhgram_appearance", android.content.Context.MODE_PRIVATE)
                .getString("font_family", "system-default");
        if (family.equals(nabdhAppliedComposerFamily)) {
            return;
        }
        android.graphics.Typeface chosen;
        if ("system-default".equals(family)) {
            chosen = android.graphics.Typeface.DEFAULT;
        } else if ("sans-serif".equals(family) || "serif".equals(family)) {
            chosen = android.graphics.Typeface.create(family, android.graphics.Typeface.NORMAL);
        } else {
            String filename = "vazirmatn".equals(family) ? "Vazirmatn.ttf"
                    : "noto-sans-arabic".equals(family) ? "NotoSansArabic.ttf"
                    : "tajawal".equals(family) ? "Tajawal.ttf"
                    : "rubik".equals(family) ? "Rubik.ttf" : "ReadexPro.ttf";
            chosen = org.telegram.messenger.AndroidUtilities.getTypeface("fonts/" + filename);
        }
        if (chosen != null) {
            messageEditText.setTypeface(chosen);
            nabdhAppliedComposerFamily = family;
        }
    }

    public void onResume() {
        isPaused = false;
        nabdhRefreshComposerFont();"""
s = s.replace(resume_anchor, resume_replacement, 1)
p.write_text(s,encoding="utf-8")
print("Glass message entry surface applied.")
