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

    // A new generation is emitted only after a deliberate font/weight/chat-size
    // edit. Cached MessageObject layouts can detect the change cheaply.
    private static volatile int fontGeneration;

    public static int generation() {
        return fontGeneration;
    }

    public static void invalidateMessageLayouts() {
        fontGeneration++;
    }

    // Telegram draws its chat-list rows using canvas TextPaint, not TextView.
    // Preserve original paint metrics across consecutive scale changes.
    private static final java.util.WeakHashMap<TextPaint, Float> dialogBaseSizes =
            new java.util.WeakHashMap<>();
    private static final java.util.WeakHashMap<TextPaint, Float> dialogAppliedSizes =
            new java.util.WeakHashMap<>();

    private static synchronized void scaleDialogPaint(TextPaint paint, int percent) {
        if (paint == null) return;
        Float original = dialogBaseSizes.get(paint);
        Float previous = dialogAppliedSizes.get(paint);
        if (original == null || previous != null &&
                Math.abs(previous - paint.getTextSize()) > 0.5f) {
            // Telegram itself may replace the paint's native size after a
            // theme/configuration change. Rebase rather than multiplying it.
            original = paint.getTextSize();
            dialogBaseSizes.put(paint, original);
        }
        float next = original * percent / 100f;
        if (Math.abs(next - paint.getTextSize()) > 0.1f) paint.setTextSize(next);
        dialogAppliedSizes.put(paint, next);
    }

    public static void applyDialogPaints() {
        android.content.Context context =
                org.telegram.messenger.ApplicationLoader.applicationContext;
        if (context == null) return;
        android.content.SharedPreferences prefs = context.getSharedPreferences(
                "nabdhgram_appearance", android.content.Context.MODE_PRIVATE);
        int percent = Math.max(85, Math.min(115,
                prefs.getInt("ui_scale_percent", 100)));
        Typeface regular = AndroidUtilities.getTypeface("fonts/rregular.ttf");
        Typeface medium = AndroidUtilities.getTypeface("fonts/rmedium.ttf");
        if (Theme.dialogs_namePaint != null) {
            for (TextPaint paint : Theme.dialogs_namePaint) {
                apply(paint, medium);
                scaleDialogPaint(paint, percent);
            }
        }
        if (Theme.dialogs_nameEncryptedPaint != null) {
            for (TextPaint paint : Theme.dialogs_nameEncryptedPaint) {
                apply(paint, medium);
                scaleDialogPaint(paint, percent);
            }
        }
        if (Theme.dialogs_messagePaint != null) {
            for (TextPaint paint : Theme.dialogs_messagePaint) {
                apply(paint, regular);
                scaleDialogPaint(paint, percent);
            }
        }
        if (Theme.dialogs_messagePrintingPaint != null) {
            for (TextPaint paint : Theme.dialogs_messagePrintingPaint) {
                apply(paint, regular);
                scaleDialogPaint(paint, percent);
            }
        }
        apply(Theme.dialogs_messageNamePaint, medium);
        apply(Theme.dialogs_searchNamePaint, medium);
        apply(Theme.dialogs_searchNameEncryptedPaint, medium);
        scaleDialogPaint(Theme.dialogs_messageNamePaint, percent);
        scaleDialogPaint(Theme.dialogs_searchNamePaint, percent);
        scaleDialogPaint(Theme.dialogs_searchNameEncryptedPaint, percent);
        scaleDialogPaint(Theme.dialogs_countTextPaint, percent);
        scaleDialogPaint(Theme.dialogs_countTextPaint2, percent);
        scaleDialogPaint(Theme.dialogs_timePaint, percent);
        scaleDialogPaint(Theme.dialogs_timePaintBold, percent);
        scaleDialogPaint(Theme.dialogs_timePaintBoldAccent, percent);
        scaleDialogPaint(Theme.dialogs_archiveTextPaint, percent);
        scaleDialogPaint(Theme.dialogs_archiveTextPaintSmall, percent);
    }

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
