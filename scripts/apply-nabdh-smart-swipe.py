#!/usr/bin/env python3
"""Install Smart Swipe V1 on the pinned Telegram source after Glass card overlays.

Preserve native LEFT-swipe actions and Telegram's original account/dialog mutation paths.
RIGHT-swipe exposes the Smart Swipe palette; no automatic archive/pin/mute.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-smart-swipe.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
dialogs_path = ui / "DialogsActivity.java"
cell_path = ui / "Cells/DialogCell.java"
manifest_path = root / "TMessagesProj/src/main/AndroidManifest.xml"
dialogs = dialogs_path.read_text(encoding="utf-8")
cell = cell_path.read_text(encoding="utf-8")
manifest = manifest_path.read_text(encoding="utf-8")

def replace_once(data, old, new, desc):
    if data.count(old) != 1:
        raise SystemExit(f"Smart Swipe upstream anchor mismatch: {desc}, count={data.count(old)}")
    return data.replace(old, new, 1)

dialogs = replace_once(dialogs,
    "                    return makeMovementFlags(0, ItemTouchHelper.LEFT);\n",
    """                    // Preserve Telegram's LEFT action; the opposite direction opens
                    // a deliberate Smart Swipe palette. Folder rows retain native handling.
                    return makeMovementFlags(0, DialogObject.isFolderDialogId(dialogId)
                            ? ItemTouchHelper.LEFT : ItemTouchHelper.LEFT | ItemTouchHelper.RIGHT);
""", "movement flags")

dialogs = replace_once(dialogs, """                if (dialog == null) {
                    return;
                }

                if (!getMessagesController().isPromoDialog(dialogId, false)""",
    """                if (dialog == null) {
                    return;
                }
                if (direction == ItemTouchHelper.RIGHT) {
                    // ItemTouchHelper expects an adapter rebind after a completed swipe.
                    // The dialog is not removed or modified by merely opening the palette.
                    final int position = viewHolder.getAdapterPosition();
                    AndroidUtilities.runOnUIThread(() -> {
                        if (position >= 0 && position < parentPage.dialogsAdapter.getItemCount()) {
                            parentPage.dialogsAdapter.notifyItemChanged(position);
                        } else {
                            parentPage.dialogsAdapter.notifyDataSetChanged();
                        }
                        showNabdhSmartSwipeActions(dialogId);
                    }, 32);
                    return;
                }

                if (!getMessagesController().isPromoDialog(dialogId, false)""",
    "onSwiped RIGHT handling")

# Keep RIGHT as a cancellable "peek" instead of ItemTouchHelper's
# destructive full-width swipe animation. The palette opens on release.
dialogs = replace_once(dialogs,
    """        public float getSwipeThreshold(RecyclerView.ViewHolder viewHolder) {
            return 0.45f;
        }""",
    """        public float getSwipeThreshold(RecyclerView.ViewHolder viewHolder) {
            if (viewHolder.itemView instanceof DialogCell
                    && ((DialogCell) viewHolder.itemView).getTranslationX() > 0) {
                // Never complete the opposite direction as an off-screen swipe;
                // open the action palette after a short, cancellable reveal.
                return 1.1f;
            }
            return 0.45f;
        }""", "short opposite-direction swipe threshold")

dialogs = replace_once(dialogs,
    """            currentItemViewHolder = viewHolder;
            if (viewHolder != null && viewHolder.itemView instanceof DialogCell) {
                ((DialogCell) viewHolder.itemView).swipeCanceled = false;
            }
            super.onSelectedChanged(viewHolder, actionState);""",
    """            if (viewHolder == null && actionState == ItemTouchHelper.ACTION_STATE_IDLE
                    && currentItemViewHolder != null
                    && currentItemViewHolder.itemView instanceof DialogCell) {
                DialogCell peek = (DialogCell) currentItemViewHolder.itemView;
                if (peek.getTranslationX() > peek.getMeasuredWidth() * 0.22f) {
                    final long peekDialogId = peek.getDialogId();
                    if (!DialogObject.isFolderDialogId(peekDialogId)) {
                        // ItemTouchHelper recovers the cell to its starting position.
                        // Delay the sheet until the 230ms recovery has finished.
                        AndroidUtilities.runOnUIThread(
                                () -> showNabdhSmartSwipeActions(peekDialogId), 240);
                    }
                }
            }
            currentItemViewHolder = viewHolder;
            if (viewHolder != null && viewHolder.itemView instanceof DialogCell) {
                ((DialogCell) viewHolder.itemView).swipeCanceled = false;
            }
            super.onSelectedChanged(viewHolder, actionState);""",
    "open menu at swipe recovery")
cell = replace_once(cell,
    "drawRevealBackground = Math.abs(translationX) >= getMeasuredWidth() * 0.45f;",
    "drawRevealBackground = Math.abs(translationX) >= getMeasuredWidth() * (translationX > 0 ? 0.22f : 0.45f);",
    "direction-aware haptic threshold")

dialogs = replace_once(dialogs,
    """            if (animationType == ItemTouchHelper.ANIMATION_TYPE_SWIPE_CANCEL) {
                return 200;""",
    """            if (animationType == ItemTouchHelper.ANIMATION_TYPE_SWIPE_CANCEL) {
                return 230; // Soft return, respecting Telegram's own recovery animator.""",
    "swipe return duration")

palette = """
    // Smart Swipe V1: a deliberate action picker after the RIGHT reveal.
    // Never run destructive or state-changing actions just by dragging.
    private void showNabdhSmartSwipeActions(long dialogId) {
        if (getParentActivity() == null || actionBar.isActionModeShowed()) {
            return;
        }
        TLRPC.Dialog target = getMessagesController().dialogs_dict.get(dialogId);
        if (target == null || DialogObject.isFolderDialogId(dialogId)
                || getMessagesController().isPromoDialog(dialogId, false)) {
            return;
        }
        final boolean rtl = LocaleController.isRTL;
        final boolean muted = getMessagesController().isDialogMuted(dialogId, 0);
        final boolean pinned = isDialogPinned(target);
        final boolean archived = folderId != 0;
        CharSequence[] choices = new CharSequence[] {
                rtl ? "ذكّرني بهذه المحادثة" : "Remind me about this chat",
                muted ? (rtl ? "إلغاء الكتم" : "Unmute") : (rtl ? "كتم المحادثة" : "Mute"),
                pinned ? (rtl ? "إلغاء التثبيت" : "Unpin") : (rtl ? "تثبيت" : "Pin"),
                archived ? (rtl ? "إلغاء الأرشفة" : "Unarchive") : (rtl ? "أرشفة" : "Archive")
        };
        BottomSheet.Builder menu = new BottomSheet.Builder(getParentActivity());
        menu.setItems(choices, new int[] {0, 0, 0, 0}, (sheet, which) -> {
            if (which == 0) {
                showNabdhSwipeReminderOptions(dialogId);
                return;
            }
            TLRPC.Dialog current = getMessagesController().dialogs_dict.get(dialogId);
            if (current == null) {
                return;
            }
            ArrayList<Long> selected = new ArrayList<>();
            selected.add(dialogId);
            if (which == 1) {
                boolean nowMuted = getMessagesController().isDialogMuted(dialogId, 0);
                if (!nowMuted) {
                    NotificationsController.getInstance(currentAccount)
                            .setDialogNotificationsSettings(dialogId, 0,
                                    NotificationsController.SETTING_MUTE_FOREVER);
                } else {
                    canMuteCount = 0;
                    canUnmuteCount = 1;
                    performSelectedDialogsAction(selected, mute, true, false);
                }
            } else if (which == 2) {
                canPinCount = isDialogPinned(current) ? 0 : 1;
                performSelectedDialogsAction(selected, pin, true, false);
            } else if (which == 3) {
                canUnarchiveCount = folderId == 0 ? 0 : 1;
                performSelectedDialogsAction(selected, archive, true, false);
            }
        });
        showDialog(menu.create());
    }

    private void showNabdhSwipeReminderOptions(long dialogId) {
        if (getParentActivity() == null) {
            return;
        }
        final boolean rtl = LocaleController.isRTL;
        final long existing = NabdhSwipeReminder.getScheduledTime(getParentActivity(),
                currentAccount, dialogId);
        // Android 13+: never silently save a reminder that cannot notify.
        if (android.os.Build.VERSION.SDK_INT >= 33
                && getParentActivity().checkSelfPermission(
                        android.Manifest.permission.POST_NOTIFICATIONS)
                        != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            showDialog(new AlertDialog.Builder(getParentActivity())
                    .setTitle(rtl ? "إذن الإشعارات" : "Notification permission")
                    .setMessage(rtl ? "فعّل إشعارات نبض جرام من إعدادات النظام لاستخدام التذكيرات."
                                    : "Enable NabdhGram notifications in system settings to use reminders.")
                    .setPositiveButton(rtl ? "حسنًا" : "OK", null).create());
            return;
        }
        CharSequence[] times = existing > 0 ? new CharSequence[] {
                rtl ? "بعد 30 دقيقة" : "In 30 minutes",
                rtl ? "بعد ساعتين" : "In 2 hours",
                rtl ? "غدًا صباحًا" : "Tomorrow morning",
                rtl ? "اختيار موعد" : "Choose date and time",
                rtl ? "إلغاء التذكير" : "Cancel reminder"
        } : new CharSequence[] {
                rtl ? "بعد 30 دقيقة" : "In 30 minutes",
                rtl ? "بعد ساعتين" : "In 2 hours",
                rtl ? "غدًا صباحًا" : "Tomorrow morning",
                rtl ? "اختيار موعد" : "Choose date and time"
        };
        showDialog(new AlertDialog.Builder(getParentActivity())
                .setTitle(rtl ? "تذكير بالمحادثة" : "Chat reminder")
                .setItems(times, (dialog, which) -> {
                    if (which == 4) {
                        NabdhSwipeReminder.cancel(getParentActivity(), currentAccount, dialogId);
                        return;
                    }
                    if (which == 3) {
                        showNabdhCustomReminderPicker(dialogId);
                        return;
                    }
                    long when;
                    if (which == 0) {
                        when = System.currentTimeMillis() + 30 * 60_000L;
                    } else if (which == 1) {
                        when = System.currentTimeMillis() + 2 * 60 * 60_000L;
                    } else {
                        java.util.Calendar calendar = java.util.Calendar.getInstance();
                        calendar.add(java.util.Calendar.DAY_OF_YEAR, 1);
                        calendar.set(java.util.Calendar.HOUR_OF_DAY, 9);
                        calendar.set(java.util.Calendar.MINUTE, 0);
                        calendar.set(java.util.Calendar.SECOND, 0);
                        calendar.set(java.util.Calendar.MILLISECOND, 0);
                        when = calendar.getTimeInMillis();
                    }
                    NabdhSwipeReminder.schedule(getParentActivity(), currentAccount,
                            dialogId, when);
                }).create());
    }

    private void showNabdhCustomReminderPicker(long dialogId) {
        if (getParentActivity() == null) {
            return;
        }
        final java.util.Calendar chosen = java.util.Calendar.getInstance();
        android.app.DatePickerDialog dates = new android.app.DatePickerDialog(
                getParentActivity(), (view, year, month, day) -> {
            chosen.set(year, month, day);
            android.app.TimePickerDialog time = new android.app.TimePickerDialog(
                    getParentActivity(), (picker, hour, minute) -> {
                chosen.set(java.util.Calendar.HOUR_OF_DAY, hour);
                chosen.set(java.util.Calendar.MINUTE, minute);
                chosen.set(java.util.Calendar.SECOND, 0);
                chosen.set(java.util.Calendar.MILLISECOND, 0);
                if (chosen.getTimeInMillis() > System.currentTimeMillis()) {
                    NabdhSwipeReminder.schedule(getParentActivity(), currentAccount,
                            dialogId, chosen.getTimeInMillis());
                }
            }, chosen.get(java.util.Calendar.HOUR_OF_DAY),
                    chosen.get(java.util.Calendar.MINUTE), true);
            time.show();
        }, chosen.get(java.util.Calendar.YEAR),
                chosen.get(java.util.Calendar.MONTH),
                chosen.get(java.util.Calendar.DAY_OF_MONTH));
        dates.getDatePicker().setMinDate(System.currentTimeMillis() - 1000L);
        dates.show();
    }

"""
dialogs = replace_once(dialogs,
    "    private class SwipeController extends ItemTouchHelper.Callback {",
    palette + "    private class SwipeController extends ItemTouchHelper.Callback {",
    "smart swipe palette location")

# Native reveal Paint is kept behind the content. Explicitly draw the
# opposite-direction preview without changing Telegram's original LEFT canvas.
cell = replace_once(cell,
    "            float tx = getMeasuredWidth() + translationX;",
    """            // NabdhGram Smart Swipe: LEFT side action tray for opposite drag.
            // No allocations in onDraw; the rounded conversation card draws
            // later on its translated canvas, so its fill cannot flash.
            if (translationX > 0 && !isTopic) {
                canvas.save();
                final float revealed = Math.min(translationX, getMeasuredWidth());
                canvas.clipRect(0, 0, revealed, getMeasuredHeight());
                nabdhCardBounds.set(dp(7), dp(3), getMeasuredWidth() - dp(7),
                        getMeasuredHeight() - dp(3));
                nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);
                nabdhCardPaint.setColor(Theme.getColor(Theme.key_chats_archiveBackground,
                        resourcesProvider));
                canvas.drawRoundRect(nabdhCardBounds, dp(17), dp(17), nabdhCardPaint);
                nabdhCardPaint.setColor(android.graphics.Color.WHITE);
                nabdhCardPaint.setTextSize(dp(11));
                nabdhCardPaint.setTextAlign(android.graphics.Paint.Align.CENTER);
                nabdhCardPaint.setAlpha((int) (225 * Math.min(1f, revealed / dp(85))));
                final String[] labels = LocaleController.isRTL
                        ? new String[] {"ذكرني", "كتم", "تثبيت", "أرشفة"}
                        : new String[] {"Remind", "Mute", "Pin", "Archive"};
                for (int i = 0; i < labels.length; i++) {
                    canvas.drawText(labels[i], dp(29 + i * 47),
                            getMeasuredHeight() / 2f + dp(4), nabdhCardPaint);
                }
                nabdhCardPaint.setAlpha(255);
                nabdhCardPaint.setTextAlign(android.graphics.Paint.Align.LEFT);
                canvas.restore();
            }
            float tx = getMeasuredWidth() + translationX;""",
    "opposite swipe reveal")

cell = replace_once(cell,
    "    private boolean drawPinBackground;",
    """    // One haptic tick per gesture; resets only after the row returns to rest.
    private boolean nabdhSwipeHapticTriggered;
    private boolean drawPinBackground;""",
    "single-tick haptic state")
cell = replace_once(cell,
    """            currentRevealProgress = 0f;
            drawRevealBackground = false;
        }
        if (isSliding && !swipeCanceled) {""",
    """            currentRevealProgress = 0f;
            drawRevealBackground = false;
            nabdhSwipeHapticTriggered = false;
        }
        if (isSliding && !swipeCanceled) {""",
    "reset haptic at rest")

cell = replace_once(cell,
    """            if (prevValue != drawRevealBackground && archiveHidden == SharedConfig.archiveHidden) {
                try {
                    performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP, HapticFeedbackConstants.FLAG_IGNORE_GLOBAL_SETTING);""",
    """            if (!prevValue && drawRevealBackground && !nabdhSwipeHapticTriggered
                    && archiveHidden == SharedConfig.archiveHidden) {
                nabdhSwipeHapticTriggered = true;
                try {
                    // Respect system vibration preferences; one tick per gesture.
                    performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);""",
    "haptic threshold")

# A non-exported receiver receives system boot and its own explicit alarms.
manifest = replace_once(manifest, "</application>",
    """    <receiver android:name="org.telegram.ui.NabdhSwipeReminder"
              android:enabled="true"
              android:exported="false">
        <intent-filter>
            <action android:name="android.intent.action.BOOT_COMPLETED" />
        </intent-filter>
    </receiver>
</application>""", "alarm receiver manifest")
dialogs_path.write_text(dialogs, encoding="utf-8")
cell_path.write_text(cell, encoding="utf-8")
manifest_path.write_text(manifest, encoding="utf-8")
# Install the tested reminder implementation from the overlay repository.
reminder_asset = Path(__file__).resolve().parents[1] / "TMessagesProj/src/main/java/org/telegram/ui/NabdhSwipeReminder.java"
if not reminder_asset.is_file():
    raise SystemExit("Smart Swipe reminder source is missing from the overlay repository")
(ui / "NabdhSwipeReminder.java").write_bytes(reminder_asset.read_bytes())
print("NabdhGram Smart Swipe V1 source overlay installed.")
