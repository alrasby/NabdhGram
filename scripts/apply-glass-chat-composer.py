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
# Telegram 13.2.x migrated text color assignments to ThemeBind; keep
# those bindings intact so user-installed themes still update the composer.
new_theme_bind_anchor = """        messageEditText.setBackgroundDrawable(null);
        ThemeBind.textColor(messageEditText, Theme.key_chat_messagePanelText, resourcesProvider);"""
if s.count(anchor) != 1 and s.count(new_theme_bind_anchor) != 1:
    raise SystemExit("Message entry background anchor changed")
replacement = """        // NabdhGram: Telegram already paints the entire message panel capsule.
        // Do not paint a second bright rounded rectangle inside the EditText;
        // it overlaps the hint and breaks dark/imported themes.
        messageEditText.setBackgroundDrawable(null);
        // Small text insets inside the native composer retain its height and
        // attachment/emoji/voice hit targets. All touch/send logic remains native.
        messageEditText.setPadding(dp(6), dp(9), dp(6), dp(10));
        messageEditText.setGravity((org.telegram.messenger.LocaleController.isRTL
                ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT)
                | android.view.Gravity.BOTTOM);
        messageEditText.setTextDirection(android.view.View.TEXT_DIRECTION_FIRST_STRONG);
        messageEditText.setSupportRtlHint(true);
        nabdhRefreshComposerFont();
        messageEditText.setTextColor(getThemedColor(Theme.key_chat_messagePanelText));"""
if s.count(anchor) == 1:
    s = s.replace(anchor, replacement, 1)
else:
    # The new API owns text-color updates; don't also call setTextColor()
    # here, which could override live ThemeBind color updates.
    bound_replacement = replacement.replace(
        "messageEditText.setTextColor(getThemedColor(Theme.key_chat_messagePanelText));",
        "ThemeBind.textColor(messageEditText, Theme.key_chat_messagePanelText, resourcesProvider);", 1)
    s = s.replace(new_theme_bind_anchor, bound_replacement, 1)

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
        boolean bold = getContext().getSharedPreferences(
                "nabdhgram_appearance", android.content.Context.MODE_PRIVATE)
                .getBoolean("font_bold", false);
        String appearanceKey = family + ":" + bold;
        if (appearanceKey.equals(nabdhAppliedComposerFamily)) {
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
            messageEditText.setTypeface(chosen, bold
                    ? android.graphics.Typeface.BOLD : android.graphics.Typeface.NORMAL);
            nabdhAppliedComposerFamily = appearanceKey;
        }
    }

    public void onResume() {
        isPaused = false;
        nabdhRefreshComposerFont();"""
s = s.replace(resume_anchor, resume_replacement, 1)
p.write_text(s,encoding="utf-8")
print("Glass message entry surface applied.")
