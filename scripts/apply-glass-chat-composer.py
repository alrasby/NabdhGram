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
        // Preserve upstream 0px horizontal padding. Telegram dynamically
        // reserves space for bot commands, emoji and attachment controls.
        // Telegram controls editable text gravity and its custom hint separately.
        // Avoid forcing RIGHT: it distorts bot placeholders with custom Arabic fonts.
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

# Keep Telegram's own measured bot-menu margins instead of adding new
# offsets that compress Arabic hint rendering in its native EditText.
bot_icon_anchor = "((MarginLayoutParams) emojiButton.getLayoutParams()).leftMargin = dp(10) + (botCommandsMenuButton == null ? 0 : botCommandsMenuButton.getMeasuredWidth());"
bot_field_anchor = "((MarginLayoutParams) messageEditText.getLayoutParams()).leftMargin = dp(57) + (botCommandsMenuButton == null ? 0 : botCommandsMenuButton.getMeasuredWidth());"
if s.count(bot_icon_anchor) != 1 or s.count(bot_field_anchor) != 1:
    raise SystemExit("Telegram bot menu composer margins changed: fail closed")

# ROOT CAUSE of Arabic 'القائمة' over 'الرسالة' in bot chats:
# BotCommandsMenuView creates a wide ALIGN_NORMAL StaticLayout. An RTL run's
# first glyph is drawn at getLineLeft(0) (near the RIGHT of that wide layout),
# but Telegram measures the button using only getLineWidth(0), then draws
# without subtracting lineLeft. Because the chat composer has clipChildren(false)
# the misplaced label escapes the bot button and overlays the input hint.
# Normalize the glyph origin to the button's measured text slot; do not change
# the dimensions, EditText, bot commands semantics or touch targets.
bot_menu = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/bots/BotCommandsMenuView.java"
bot_source = bot_menu.read_text(encoding="utf-8")
bot_draw_anchor = "canvas.translate(AndroidUtilities.dp(34), (getMeasuredHeight() - menuTextLayout.getHeight()) / 2f);"
bot_draw_fix = """// Align the first glyph with the measured text slot for both RTL and LTR.
                // ALIGN_NORMAL RTL StaticLayout stores its glyphs far to the right
                // within a 60%-of-screen layout, not at x=0.
                canvas.clipRect(0, 0, getMeasuredWidth(), getMeasuredHeight());
                canvas.translate(AndroidUtilities.dp(34) - menuTextLayout.getLineLeft(0),
                        (getMeasuredHeight() - menuTextLayout.getHeight()) / 2f);"""
if bot_source.count(bot_draw_anchor) != 1:
    raise SystemExit("BotCommandsMenuView RTL draw anchor changed; refusing unsafe patch")
bot_menu.write_text(bot_source.replace(bot_draw_anchor, bot_draw_fix, 1), encoding="utf-8")

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
            // EditTextBoldCursor caches a hint StaticLayout created with old
            // glyph advances. A Typeface replacement alone leaves stale
            // advances in the hint, causing Arabic letters to overlap.
            final boolean hadHint = messageEditText.getHintLayoutEx() != null;
            messageEditText.setTypeface(chosen, bold
                    ? android.graphics.Typeface.BOLD : android.graphics.Typeface.NORMAL);
            if (hadHint) {
                // Rebuild with the NEW paint, without changing user text.
                messageEditText.setHintText("", false);
                updateFieldHint(false);
            }
            nabdhAppliedComposerFamily = appearanceKey;
        }
    }

    public void onResume() {
        isPaused = false;
        nabdhRefreshComposerFont();"""
s = s.replace(resume_anchor, resume_replacement, 1)
p.write_text(s,encoding="utf-8")
print("Glass message entry surface applied.")
