package org.telegram.ui.Components;

import android.graphics.Typeface;
import android.text.TextPaint;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;

/**
 * Central custom font bridge for *canvas-drawn* Telegram messages. TextViews
 * already use the global appearance walker. ChatMessageCell, file metadata,
 * captions, replies, forwards, timestamps and voice labels mostly use these
 * Theme TextPaint objects and therefore bypass TextView updates.
 *
 * Called after native chat resources are created AND on explicit font edits.
 * Never rewrites Telegram's monospace code paints or emoji glyph paints.
 */
public final class NabdhTypefaceManager {
    private NabdhTypefaceManager() {}

    private static void apply(TextPaint paint, Typeface typeface) {
        if (paint != null && typeface != null && paint.getTypeface() != typeface) {
            paint.setTypeface(typeface);
        }
    }

    public static void applyChatPaints() {
        final Typeface regular = AndroidUtilities.getTypeface("fonts/rregular.ttf");
        final Typeface medium = AndroidUtilities.getTypeface("fonts/rmedium.ttf");

        apply(Theme.chat_msgTextPaint, regular);
        apply(Theme.chat_replyTextPaint, regular);
        apply(Theme.chat_quoteTextPaint, regular);
        apply(Theme.chat_explanationTextPaint, regular);
        apply(Theme.chat_forwardNamePaint, medium);
        apply(Theme.chat_replyNamePaint, medium);
        apply(Theme.chat_namePaint, medium);
        apply(Theme.chat_topicTextPaint, medium);
        apply(Theme.chat_adminPaint, regular);
        apply(Theme.chat_titleLabelTextPaint, regular);
        apply(Theme.chat_infoPaint, regular);
        apply(Theme.chat_infoBoldPaint, medium);
        apply(Theme.chat_timePaint, regular);
        apply(Theme.chat_docNamePaint, medium);
        apply(Theme.chat_audioTitlePaint, medium);
        apply(Theme.chat_audioPerformerPaint, regular);
        apply(Theme.chat_audioTimePaint, regular);
        apply(Theme.chat_durationPaint, regular);
        apply(Theme.chat_contactNamePaint, medium);
        apply(Theme.chat_contactPhonePaint, regular);
        apply(Theme.chat_locationTitlePaint, medium);
        apply(Theme.chat_locationAddressPaint, regular);
        apply(Theme.chat_commentTextPaint, regular);
        apply(Theme.chat_contextResult_titleTextPaint, medium);
        apply(Theme.chat_contextResult_descriptionTextPaint, regular);
        apply(Theme.chat_msgGameTextPaint, regular);
        apply(Theme.chat_msgBotButtonPaint, medium);
        apply(Theme.chat_gamePaint, medium);
        apply(Theme.chat_shipmentPaint, regular);
        apply(Theme.chat_botButtonPaint, medium);
        apply(Theme.chat_actionTextPaint, medium);
        apply(Theme.chat_actionTextPaint2, medium);
        apply(Theme.chat_actionTextPaint3, medium);
        // Code: Theme.chat_msgTextCodePaint, chat_msgTextCode2Paint and
        // chat_msgTextCode3Paint stay MONOSPACE. Emoji paints stay native.
    }
}
