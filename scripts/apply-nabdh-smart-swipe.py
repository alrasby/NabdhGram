#!/usr/bin/env python3
"""Smart Swipe V1.1: independent RIGHT touch recognizer; LEFT remains Telegram native.

A held RIGHT card displays four actual child buttons. A custom SpringAnimation
controls only RIGHT swipes. Never give RIGHT to ItemTouchHelper: this caused
stuck translations and unresponsive rows in the previous implementation.
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

def once(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit("Smart Swipe upstream anchor mismatch: " + label +
                         " count=" + str(text.count(old)))
    return text.replace(old, new, 1)

# Preflight must fail if someone accidentally merges the previous gesture
# implementation into this script later.
if "ItemTouchHelper.LEFT | ItemTouchHelper.RIGHT" in dialogs:
    raise SystemExit("Smart Swipe cannot coexist with native RIGHT ItemTouchHelper")

# Add a dedicated touch listener BEFORE ItemTouchHelper is attached. It only
# intercepts clear rightward drags after touch slop and rejects vertical moves.
dialogs = once(dialogs,
    "            viewPage.itemTouchhelper = new ItemTouchHelper(viewPage.swipeController);",
    """            installNabdhSmartSwipe(viewPage);
            viewPage.itemTouchhelper = new ItemTouchHelper(viewPage.swipeController);""",
    "independent listener before native ItemTouchHelper")

dialogs = once(dialogs,
    "            viewPage.listView.setOnItemClickListener((view, position, x, y) -> {",
    """            viewPage.listView.setOnItemClickListener((view, position, x, y) -> {
                // The chat-row click handler must not consume a just-finished
                // action-tray tap or horizontal swipe.
                if (android.os.SystemClock.uptimeMillis() < nabdhIgnoreItemClicksUntil
                        || view instanceof DialogCell
                        && ((DialogCell) view).getTranslationX() > dp(8)) {
                    return;
                }""", "suppress chat opening immediately after Smart Swipe")

palette = """
    private long nabdhIgnoreItemClicksUntil;

    private void nabdhRunSmartAction(long dialogId, int action) {
        if (getParentActivity() == null || actionBar.isActionModeShowed()) return;
        TLRPC.Dialog dialog = getMessagesController().dialogs_dict.get(dialogId);
        if (dialog == null || DialogObject.isFolderDialogId(dialogId)
                || getMessagesController().isPromoDialog(dialogId, false)) return;
        if (action == 0) {
            showNabdhSwipeReminderOptions(dialogId);
            return;
        }
        ArrayList<Long> selected = new ArrayList<>();
        selected.add(dialogId);
        if (action == 1) {
            if (!getMessagesController().isDialogMuted(dialogId, 0)) {
                NotificationsController.getInstance(currentAccount)
                        .setDialogNotificationsSettings(dialogId, 0,
                                NotificationsController.SETTING_MUTE_FOREVER);
            } else {
                canMuteCount = 0;
                canUnmuteCount = 1;
                performSelectedDialogsAction(selected, mute, true, false);
            }
        } else if (action == 2) {
            canPinCount = isDialogPinned(dialog) ? 0 : 1;
            performSelectedDialogsAction(selected, pin, true, false);
        } else if (action == 3) {
            canUnarchiveCount = dialog.folder_id == 0 ? 0 : 1;
            performSelectedDialogsAction(selected, archive, true, false);
        }
    }

    private void installNabdhSmartSwipe(ViewPage page) {
        final Runnable[] stopSwipeOnScroll = new Runnable[1];
        page.listView.addOnItemTouchListener(new RecyclerView.OnItemTouchListener() {
            private DialogCell candidate;
            private DialogCell expanded;
            private androidx.dynamicanimation.animation.SpringAnimation spring;
            private float downX, downY, startingX;
            private boolean dragging;
            private boolean consumedDown;
            private int pressedAction = -1;
            private float actionDownX, actionDownY;
            {
                stopSwipeOnScroll[0] = () -> {
                    if (spring != null) spring.cancel();
                    if (expanded != null) {
                        expanded.nabdhClearSmartSwipeActions();
                        expanded.setTranslationX(0f);
                        expanded = null;
                    }
                    if (candidate != null) {
                        candidate.nabdhClearSmartSwipeActions();
                        candidate.setTranslationX(0f);
                        candidate = null;
                    }
                    dragging = false;
                    consumedDown = false;
                };
            }

            private void settle(DialogCell row, float target) {
                if (row == null) return;
                if (spring != null) spring.cancel();
                spring = new androidx.dynamicanimation.animation.SpringAnimation(row,
                        new androidx.dynamicanimation.animation.FloatPropertyCompat<DialogCell>(
                                "nabdhSmartSwipeX") {
                            @Override public float getValue(DialogCell value) {
                                return value.getTranslationX();
                            }
                            @Override public void setValue(DialogCell value, float x) {
                                value.setTranslationX(x);
                            }
                        });
                androidx.dynamicanimation.animation.SpringForce force =
                        new androidx.dynamicanimation.animation.SpringForce(target);
                force.setStiffness(550f);
                force.setDampingRatio(0.88f);
                spring.setSpring(force);
                spring.setMinimumVisibleChange(0.7f);
                if (android.os.Build.VERSION.SDK_INT >= 26
                        && !android.animation.ValueAnimator.areAnimatorsEnabled()) {
                    row.setTranslationX(target);
                    return;
                }
                spring.start();
            }

            private void close() {
                if (expanded != null) {
                    DialogCell old = expanded;
                    expanded = null;
                    old.nabdhClearSmartSwipeActions();
                    settle(old, 0f);
                }
            }

            @Override public boolean onInterceptTouchEvent(RecyclerView recycler,
                    android.view.MotionEvent event) {
                int action = event.getActionMasked();
                if (action == android.view.MotionEvent.ACTION_DOWN) {
                    consumedDown = false;
                    pressedAction = -1;
                    dragging = false;
                    candidate = null;
                    downX = event.getX();
                    downY = event.getY();
                    if (actionBar.isActionModeShowed() || onlySelect
                            || !allowSwipeDuringCurrentTouch || communityId != 0
                            || slidingView != null
                            || waitingForScrollFinished || rightFragmentTransitionInProgress
                            || rightSlidingDialogContainer.hasFragment()
                            || filterTabsView != null && filterTabsView.isEditing()
                            || waitingForDialogsAnimationEnd(page)) {
                        close();
                        return false;
                    }
                    if (expanded != null) {
                        // The list owns click/long-press handlers even when buttons
                        // are children of DialogCell. Fully consume tray touches.
                        page.listView.cancelClickRunnables(true);
                        nabdhIgnoreItemClicksUntil =
                                android.os.SystemClock.uptimeMillis() + 450L;
                        consumedDown = true;
                        actionDownX = event.getX();
                        actionDownY = event.getY();
                        float cx = event.getX() - expanded.getLeft();
                        float cy = event.getY() - expanded.getTop();
                        if (expanded.getParent() != recycler
                                || cx < dp(7) || cx >= dp(219) || cy < dp(3)
                                || cy > expanded.getHeight() - dp(3)
                                || expanded.getTranslationX() < dp(140)) {
                            close();
                            return true; // Outside tap dismisses without chat opening.
                        }
                        pressedAction = expanded.nabdhSmartActionAt(cx, cy);
                        if (pressedAction >= 0) expanded.nabdhSetSmartPressed(pressedAction);
                        return true;
                    }
                    if (downX <= dp(24)
                            || downX >= recycler.getWidth() - dp(24)) return false;
                    android.view.View child = recycler.findChildViewUnder(downX, downY);
                    if (!(child instanceof DialogCell)) return false;
                    DialogCell row = (DialogCell) child;
                    long id = row.getDialogId();
                    if (DialogObject.isFolderDialogId(id)
                            || getMessagesController().isPromoDialog(id, false)
                            || getMessagesController().dialogs_dict.get(id) == null
                            || page.dialogsType != DIALOGS_TYPE_DEFAULT
                            && page.dialogsType != DIALOGS_TYPE_FOLDER1
                            && page.dialogsType != DIALOGS_TYPE_FOLDER2) return false;
                    candidate = row;
                    startingX = row.getTranslationX();
                    return false;
                }
                if (action == android.view.MotionEvent.ACTION_MOVE && candidate != null) {
                    float dx = event.getX() - downX;
                    float dy = event.getY() - downY;
                    int slop = android.view.ViewConfiguration.get(
                            recycler.getContext()).getScaledTouchSlop();
                    if (((startingX > 0 && dx < -slop)
                            || (startingX == 0 && dx > slop))
                            && Math.abs(dx) > Math.abs(dy) * 1.5f
                            && Math.abs(dy) < dp(36)) {
                        dragging = true;
                        nabdhIgnoreItemClicksUntil =
                                android.os.SystemClock.uptimeMillis() + 450L;
                        page.listView.cancelClickRunnables(true);
                        if (spring != null) spring.cancel();
                        recycler.getParent().requestDisallowInterceptTouchEvent(true);
                        return true;
                    }
                    if (Math.abs(dy) > slop * 1.5f
                            || (startingX == 0 && dx < -slop)) {
                        candidate = null;
                    }
                }
                if (action == android.view.MotionEvent.ACTION_UP
                        || action == android.view.MotionEvent.ACTION_CANCEL) candidate = null;
                return false;
            }

            @Override public void onTouchEvent(RecyclerView recycler,
                    android.view.MotionEvent event) {
                int action = event.getActionMasked();
                if (consumedDown) {
                    final int slop = android.view.ViewConfiguration.get(
                            recycler.getContext()).getScaledTouchSlop();
                    float dx = event.getX() - actionDownX;
                    float dy = event.getY() - actionDownY;
                    if (expanded != null && pressedAction >= 0
                            && action == android.view.MotionEvent.ACTION_MOVE
                            && dx < -slop) {
                        if (spring != null) spring.cancel();
                        expanded.setTranslationX(Math.max(0f, dp(212) + dx));
                    }
                    if (action == android.view.MotionEvent.ACTION_UP
                            || action == android.view.MotionEvent.ACTION_CANCEL) {
                        DialogCell row = expanded;
                        int actionIndex = pressedAction;
                        boolean click = org.telegram.ui.Components.NabdhCardGeometry.acceptTap(
                                action == android.view.MotionEvent.ACTION_UP, dx, dy, slop,
                                actionIndex, row == null ? -1 : row.nabdhSmartActionAt(
                                        event.getX() - row.getLeft(), event.getY() - row.getTop()));
                        if (row != null) row.nabdhSetSmartPressed(-1);
                        consumedDown = false;
                        pressedAction = -1;
                        if (row != null && row.getParent() == recycler
                                && actionIndex >= 0 && click) {
                            // Delegate to a real TextView.performClick(), not to
                            // RecyclerListView's underlying item click handler.
                            row.nabdhPerformSmartAction(actionIndex);
                        } else if (row != null && row.getTranslationX() < dp(135)) {
                            close();
                        } else if (row != null) {
                            settle(row, dp(212));
                        }
                    }
                    return;
                }
                if (candidate == null || !dragging) return;
                if (action == android.view.MotionEvent.ACTION_MOVE) {
                    float dx = event.getX() - downX;
                    candidate.setTranslationX(Math.max(0f,
                            Math.min(dp(212), startingX + dx)));
                } else if (action == android.view.MotionEvent.ACTION_UP
                        || action == android.view.MotionEvent.ACTION_CANCEL) {
                    DialogCell row = candidate;
                    boolean open = action == android.view.MotionEvent.ACTION_UP
                            && row.getTranslationX() > (startingX > 0 ? dp(135) : dp(68))
                            && row.getParent() == recycler;
                    candidate = null;
                    dragging = false;
                    if (open) {
                        if (expanded != null && expanded != row) close();
                        expanded = row;
                        final long dialogId = row.getDialogId();
                        TLRPC.Dialog current = getMessagesController().dialogs_dict.get(dialogId);
                        if (current == null) {
                            expanded = null;
                            row.nabdhClearSmartSwipeActions();
                            settle(row, 0f);
                            return;
                        }
                        row.nabdhSetSmartSwipeActions(index -> {
                            if (row.getDialogId() == dialogId) {
                                close();
                                nabdhRunSmartAction(dialogId, index);
                            }
                        }, getMessagesController().isDialogMuted(dialogId, 0),
                                isDialogPinned(current), current.folder_id != 0);
                        settle(row, dp(212));
                    } else {
                        settle(row, 0f);
                    }
                }
            }

            @Override public void onRequestDisallowInterceptTouchEvent(boolean disallow) {
                // No global interception; native vertical and LEFT remain untouched.
            }
        });
        page.listView.addOnScrollListener(new RecyclerView.OnScrollListener() {
            @Override public void onScrollStateChanged(RecyclerView rv, int state) {
                // RecyclerView recycles rows while scrolling; clear inline buttons.
                if (state == RecyclerView.SCROLL_STATE_DRAGGING
                        && stopSwipeOnScroll[0] != null) {
                    stopSwipeOnScroll[0].run();
                }
            }
        });
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
                    .setPositiveButton(rtl ? "إعدادات الإشعارات" : "Notification settings",
                            (d, w) -> {
                        android.content.Intent settings = new android.content.Intent(
                                android.provider.Settings.ACTION_APP_NOTIFICATION_SETTINGS);
                        settings.putExtra(android.provider.Settings.EXTRA_APP_PACKAGE,
                                getParentActivity().getPackageName());
                        getParentActivity().startActivity(settings);
                    }).setNegativeButton(rtl ? "إلغاء" : "Cancel", null).create());
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
        // Use native Telegram AlertDialog, but compose custom themed Glass
        // options instead of the plain platform list visible in the test video.
        final android.content.Context context = getParentActivity();
        final int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        final int background = Theme.getColor(Theme.key_dialogBackground);
        final int foreground = Theme.getColor(Theme.key_dialogTextBlack);
        android.widget.LinearLayout options = new android.widget.LinearLayout(context);
        options.setOrientation(android.widget.LinearLayout.VERTICAL);
        options.setPadding(dp(16), dp(6), dp(16), dp(14));
        options.setLayoutDirection(rtl
                ? android.view.View.LAYOUT_DIRECTION_RTL
                : android.view.View.LAYOUT_DIRECTION_LTR);
        final AlertDialog chooser = new AlertDialog.Builder(context)
                .setTitle(rtl ? "تذكير بالمحادثة" : "Chat reminder")
                .setView(options)
                .setNegativeButton(rtl ? "إغلاق" : "Close", null).create();
        chooser.setBackgroundColor(background);
        for (int i = 0; i < times.length; i++) {
            final int option = i;
            android.widget.TextView item = new android.widget.TextView(context);
            item.setText(times[i]);
            item.setTextColor(i == 4 ? accent : foreground);
            item.setTextSize(15);
            item.setGravity(android.view.Gravity.CENTER_VERTICAL
                    | (rtl ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT));
            item.setPadding(dp(16), 0, dp(16), 0);
            item.setMinHeight(dp(49));
            item.setContentDescription(times[i]);
            android.graphics.drawable.GradientDrawable capsule =
                    new android.graphics.drawable.GradientDrawable();
            capsule.setColor(nabdhSwipeBlend(background, accent, 0.075f));
            capsule.setCornerRadius(dp(14));
            capsule.setStroke(dp(1), nabdhSwipeBlend(background, accent, 0.22f));
            item.setBackground(new android.graphics.drawable.RippleDrawable(
                    android.content.res.ColorStateList.valueOf(
                            android.graphics.Color.argb(35,
                                    android.graphics.Color.red(accent),
                                    android.graphics.Color.green(accent),
                                    android.graphics.Color.blue(accent))),
                    capsule, null));
            android.widget.LinearLayout.LayoutParams params =
                    new android.widget.LinearLayout.LayoutParams(
                            android.view.ViewGroup.LayoutParams.MATCH_PARENT, dp(49));
            params.setMargins(0, dp(4), 0, dp(4));
            options.addView(item, params);
            item.setOnClickListener(v -> {
                chooser.dismiss();
                if (option == 4) {
                    NabdhSwipeReminder.cancel(context, currentAccount, dialogId);
                    nabdhShowReminderConfirmation(0L);
                } else if (option == 3) {
                    showNabdhCustomReminderPicker(dialogId);
                } else {
                    long when;
                    if (option == 0) {
                        when = System.currentTimeMillis() + 30 * 60_000L;
                    } else if (option == 1) {
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
                    NabdhSwipeReminder.schedule(context, currentAccount, dialogId, when);
                    nabdhShowReminderConfirmation(when);
                }
            });
        }
        showDialog(chooser);
    }

    private static int nabdhSwipeBlend(int surface, int accent, float ratio) {
        final float inv = 1f - ratio;
        return android.graphics.Color.rgb(
                Math.round(android.graphics.Color.red(surface) * inv
                        + android.graphics.Color.red(accent) * ratio),
                Math.round(android.graphics.Color.green(surface) * inv
                        + android.graphics.Color.green(accent) * ratio),
                Math.round(android.graphics.Color.blue(surface) * inv
                        + android.graphics.Color.blue(accent) * ratio));
    }

    private void nabdhShowReminderConfirmation(long when) {
        if (getParentActivity() == null) return;
        final boolean rtl = LocaleController.isRTL;
        final String message = when == 0L
                ? (rtl ? "تم إلغاء التذكير." : "Reminder cancelled.")
                : (rtl ? "تم ضبط التذكير على: " : "Reminder set for: ")
                + java.text.DateFormat.getDateTimeInstance(
                        java.text.DateFormat.MEDIUM, java.text.DateFormat.SHORT)
                        .format(new java.util.Date(when));
        AndroidUtilities.runOnUIThread(() -> {
            if (getParentActivity() != null) {
                showDialog(new AlertDialog.Builder(getParentActivity())
                        .setTitle(rtl ? "تذكير المحادثة" : "Chat reminder")
                        .setMessage(message)
                        .setPositiveButton(rtl ? "تم" : "OK", null).create());
            }
        }, 150);
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
                    nabdhShowReminderConfirmation(chosen.getTimeInMillis());
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
dialogs = once(dialogs,
    "    private class SwipeController extends ItemTouchHelper.Callback {",
    palette + "    private class SwipeController extends ItemTouchHelper.Callback {",
    "gesture and reminder integration")

# Real tappable Android views belong to the DialogCell, not a canvas label.
cell = once(cell, "    private boolean drawPinBackground;",
    """    public interface NabdhSmartAction { void onAction(int index); }
    private NabdhSmartAction nabdhSmartAction;
    private android.widget.LinearLayout nabdhSmartBar;
    private boolean nabdhSwipeHapticTriggered;

    private void nabdhCreateSmartBar(android.content.Context context) {
        nabdhSmartBar = new android.widget.LinearLayout(context);
        nabdhSmartBar.setOrientation(android.widget.LinearLayout.HORIZONTAL);
        nabdhSmartBar.setLayoutDirection(LocaleController.isRTL
                ? android.view.View.LAYOUT_DIRECTION_RTL
                : android.view.View.LAYOUT_DIRECTION_LTR);
        android.graphics.drawable.GradientDrawable surface =
                new android.graphics.drawable.GradientDrawable();
        // The row itself has a Glass fill. Avoid a second nearly opaque
        // windowBackgroundWhite panel underneath it as the card slides.
        final int glassAccent = Theme.getColor(Theme.key_chats_archiveBackground);
        surface.setColor(nabdhBlendThemeColor(
                Theme.getColor(Theme.key_windowBackgroundGray), glassAccent, 0.20f));
        surface.setCornerRadius(dp(17));
        nabdhSmartBar.setBackground(surface);
        final String[] labels = LocaleController.isRTL ?
                new String[]{"ذكّرني", "كتم", "تثبيت", "أرشفة"} :
                new String[]{"Remind", "Mute", "Pin", "Archive"};
        for (int i = 0; i < labels.length; i++) {
            final int which = i;
            android.widget.TextView button = new android.widget.TextView(context);
            button.setText(labels[i]);
            button.setTextColor(android.graphics.Color.WHITE);
            button.setTextSize(9);
            button.setMaxLines(2);
            button.setGravity(android.view.Gravity.CENTER);
            button.setContentDescription(labels[i]);
            button.setClickable(true);
            button.setFocusable(true);
            // Four independent pill buttons, theme-aware and touch friendly.
            android.graphics.drawable.GradientDrawable pill =
                    new android.graphics.drawable.GradientDrawable();
            pill.setColor(Theme.getColor(Theme.key_chats_archiveBackground));
            pill.setCornerRadius(dp(11));
            pill.setStroke(dp(1), android.graphics.Color.argb(95,255,255,255));
            button.setBackground(new android.graphics.drawable.RippleDrawable(
                    android.content.res.ColorStateList.valueOf(
                            android.graphics.Color.argb(75,255,255,255)),
                    pill, null));
            button.setPadding(dp(1), dp(3), dp(1), dp(3));
            button.setOnClickListener(v -> {
                if (nabdhSmartAction != null) nabdhSmartAction.onAction(which);
            });
            android.widget.LinearLayout.LayoutParams lp =
                    new android.widget.LinearLayout.LayoutParams(dp(49),
                            android.view.ViewGroup.LayoutParams.MATCH_PARENT);
            lp.setMargins(dp(2), dp(3), dp(2), dp(3));
            nabdhSmartBar.addView(button, lp);
        }
        nabdhSmartBar.setVisibility(android.view.View.GONE);
        addView(nabdhSmartBar);
    }

    public void nabdhSetSmartSwipeActions(NabdhSmartAction callback,
            boolean muted, boolean pinned, boolean archived) {
        nabdhSmartAction = callback;
        final boolean rtl = LocaleController.isRTL;
        final String[] labels = new String[] {
                rtl ? "ذكّرني" : "Remind",
                muted ? (rtl ? "إلغاء الكتم" : "Unmute") : (rtl ? "كتم" : "Mute"),
                pinned ? (rtl ? "إلغاء التثبيت" : "Unpin") : (rtl ? "تثبيت" : "Pin"),
                archived ? (rtl ? "إلغاء الأرشفة" : "Unarchive") : (rtl ? "أرشفة" : "Archive")
        };
        for (int i = 0; i < labels.length; i++) {
            android.widget.TextView button =
                    (android.widget.TextView) nabdhSmartBar.getChildAt(i);
            button.setText(labels[i]);
            button.setContentDescription(labels[i]);
        }
        nabdhSmartBar.bringToFront();
        nabdhSmartBar.setVisibility(android.view.View.VISIBLE);
        nabdhSmartBar.setAlpha(1f);
        nabdhUpdateSmartTrayClip(translationX);
    }

    public int nabdhSmartActionAt(float x, float y) {
        if (nabdhSmartBar == null || nabdhSmartAction == null
                || nabdhSmartBar.getVisibility() != android.view.View.VISIBLE) return -1;
        float localX = x - nabdhSmartBar.getLeft();
        float localY = y - nabdhSmartBar.getTop();
        if (localX < 0 || localX >= Math.min(nabdhSmartBar.getWidth(), translationX)
                || localY < 0 || localY >= nabdhSmartBar.getHeight()) return -1;
        for (int i = 0; i < nabdhSmartBar.getChildCount(); i++) {
            android.view.View button = nabdhSmartBar.getChildAt(i);
            if (org.telegram.ui.Components.NabdhCardGeometry.hit(localX, localY,
                    button.getLeft(), button.getTop(), button.getRight(), button.getBottom())) return i;
        }
        return -1;
    }

    public void nabdhSetSmartPressed(int index) {
        if (nabdhSmartBar == null) return;
        for (int i = 0; i < nabdhSmartBar.getChildCount(); i++) {
            nabdhSmartBar.getChildAt(i).setPressed(i == index);
        }
    }

    public void nabdhPerformSmartAction(int index) {
        if (nabdhSmartAction != null && index >= 0 && index < 4) {
            android.view.View button = nabdhSmartBar.getChildAt(index);
            if (button != null) button.performClick();
        }
    }

    public void nabdhClearSmartSwipeActions() {
        nabdhSmartAction = null;
        nabdhSetSmartPressed(-1);
        nabdhSmartBar.setVisibility(android.view.View.GONE);
    }

    private final android.graphics.Rect nabdhSmartTrayClip = new android.graphics.Rect();
    private void nabdhUpdateSmartTrayClip(float translation) {
        if (nabdhSmartBar == null) return;
        int width = org.telegram.ui.Components.NabdhCardGeometry.trayWidth(translation, dp(212));
        nabdhSmartTrayClip.set(0, 0, width, Math.max(0, getMeasuredHeight() - dp(6)));
        nabdhSmartBar.setClipBounds(nabdhSmartTrayClip);
    }

    private boolean drawPinBackground;""",
    "four interactive card buttons")

cell = once(cell, """        super(context);
        storyParams.allowLongress = true;""",
    """        super(context);
        nabdhCreateSmartBar(context);
        storyParams.allowLongress = true;""", "initialize child action bar")

cell = once(cell,
    """        int size = getMeasuredHeight() + getMeasuredWidth() << 16;""",
    """        if (nabdhSmartBar != null) {
            nabdhSmartBar.measure(
                    android.view.View.MeasureSpec.makeMeasureSpec(dp(212),
                            android.view.View.MeasureSpec.EXACTLY),
                    android.view.View.MeasureSpec.makeMeasureSpec(
                            Math.max(dp(32), getMeasuredHeight() - dp(6)),
                            android.view.View.MeasureSpec.EXACTLY));
            nabdhSmartBar.layout(dp(7), dp(3), dp(219),
                    getMeasuredHeight() - dp(3));
            nabdhUpdateSmartTrayClip(translationX);
        }
        int size = getMeasuredHeight() + getMeasuredWidth() << 16;""",
    "layout interactive tray")

# Preserve the same card surface draw ordering as the verified #1036.
cell = once(cell, "        translationX = value;\n",
    """        translationX = value;
        if (nabdhSmartBar != null) {
            if (value > 0) {
                nabdhSmartBar.setVisibility(android.view.View.VISIBLE);
                nabdhSmartBar.setAlpha(1f);
                nabdhUpdateSmartTrayClip(value);
            } else {
                nabdhSmartBar.setVisibility(android.view.View.GONE);
            }
        }
""", "visibility follows swipe translation")

cell = once(cell,
    """        if (translationX != 0 || cornerProgress != 0.0f) {
            canvas.save();
            canvas.translate(0, -translateY);""",
    """        if (translationX > 0 && nabdhOwnsCard()) {
            // Stationary reveal surface: paint before the content translation,
            // so spring-back never exposes the unstyled list canvas.
            canvas.save();
            canvas.translate(0, -translateY);
            nabdhClipCard(canvas);
            // Only the exposed strip is painted; the moving card owns the rest.
            canvas.clipRect(nabdhCardBounds.left, nabdhCardBounds.top,
                    org.telegram.ui.Components.NabdhCardGeometry.revealRight(nabdhCardBounds.left, nabdhCardBounds.right, translationX),
                    nabdhCardBounds.bottom);
            nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);
            nabdhCardPaint.setColor(nabdhBlendThemeColor(
                    Theme.getColor(Theme.key_windowBackgroundGray, resourcesProvider),
                    Theme.getColor(Theme.key_chats_archiveBackground, resourcesProvider), 0.20f));
            canvas.drawRoundRect(nabdhCardBounds, dp(17), dp(17), nabdhCardPaint);
            canvas.restore();
        }
        if (translationX < 0) {
            canvas.save();
            canvas.translate(0, -translateY);
            // Native Telegram's rectangular READ reveal previously bled
            // beyond the rounded Glass surface. Clip its canvas to the same
            // bounds without allocating a Path on each frame.
            if (nabdhOwnsCard()) {
                nabdhClipCard(canvas);
                canvas.clipRect(org.telegram.ui.Components.NabdhCardGeometry.revealLeft(nabdhCardBounds.left, nabdhCardBounds.right, translationX),
                        nabdhCardBounds.top, nabdhCardBounds.right, nabdhCardBounds.bottom);
            }""",
    "clip original LEFT reveal to rounded Glass card")

cell = once(cell,
    """            if (prevValue != drawRevealBackground && archiveHidden == SharedConfig.archiveHidden) {
                try {
                    performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP, HapticFeedbackConstants.FLAG_IGNORE_GLOBAL_SETTING);""",
    """            if (!prevValue && drawRevealBackground && !nabdhSwipeHapticTriggered
                    && archiveHidden == SharedConfig.archiveHidden) {
                nabdhSwipeHapticTriggered = true;
                try {
                    performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);""",
    "single system-respecting haptic")
cell = once(cell,
    """            currentRevealProgress = 0f;
            drawRevealBackground = false;
        }
        if (isSliding && !swipeCanceled) {""",
    """            currentRevealProgress = 0f;
            drawRevealBackground = false;
            nabdhSwipeHapticTriggered = false;
        }
        if (isSliding && !swipeCanceled) {""",
    "reset haptic when closed")

# The interactive bar overlaps the avatar's original story-touch area.
# When expanded, those taps must be delivered to the actual child buttons.
cell = once(cell,
    """    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {""",
    """    private boolean nabdhHitSmartAction(android.view.MotionEvent event) {
        return translationX >= dp(140)
                && nabdhSmartActionAt(event.getX(), event.getY()) >= 0;
    }

    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {
        if (nabdhHitSmartAction(ev)) {
            return super.onInterceptTouchEvent(ev);
        }""", "no story-avatar interception of Smart Swipe buttons")
cell = once(cell,
    """    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        if (!isTopic""",
    """    @Override
    public boolean dispatchTouchEvent(MotionEvent ev) {
        if (nabdhHitSmartAction(ev)) {
            return super.dispatchTouchEvent(ev);
        }
        if (!isTopic""", "deliver buttons through child dispatch")
cell = once(cell,
    """    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (rightFragmentOpenedProgress""",
    """    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (nabdhHitSmartAction(event)) {
            return super.onTouchEvent(event);
        }
        if (rightFragmentOpenedProgress""", "button touches bypass story handler")

cell = once(cell,
    """            if (translationX != 0 || cornerProgress != 0.0f) {
                canvas.save();

                Theme.dialogs_pinnedPaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider));""",
    """            // Telegram draws a flat 64dp white backing during a swipe.
            // Keep it for native LEFT gestures only; Smart Swipe RIGHT owns
            // its separate rounded tray and must not drag a white rectangle.
            // Native rectangular backing is unnecessary for owned cards:
            // the opaque translated card fill is their sole content surface.
            if (!nabdhOwnsCard() && (translationX != 0 || cornerProgress != 0.0f)) {
                canvas.save();

                Theme.dialogs_pinnedPaint.setColor(nabdhBlendThemeColor(
                        Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider),
                        Theme.getColor(Theme.key_windowBackgroundGray, resourcesProvider), 0.55f));""", "remove right-swipe white backing without affecting native LEFT")

# Native Telegram reveal-circle work belongs exclusively to the LEFT action.
# The RIGHT tray paints its own layer and haptics, avoiding offscreen animations.
cell = once(cell,
    "drawRevealBackground = Math.abs(translationX) >= getMeasuredWidth() * 0.45f;",
    "drawRevealBackground = translationX < 0 && Math.abs(translationX) >= getMeasuredWidth() * 0.45f;",
    "disable native reveal animation for opposite direction")
cell = once(cell,
    "if (!prevValue && drawRevealBackground && !nabdhSwipeHapticTriggered",
    "if (!prevValue && (drawRevealBackground || (translationX > 0 && translationX >= dp(70))) && !nabdhSwipeHapticTriggered",
    "one haptic threshold per RIGHT gesture")

# Keep Android-specific storage and boot handling from the existing implementation.
manifest = once(manifest, "</application>",
    """    <receiver android:name="org.telegram.ui.NabdhSwipeReminder"
              android:enabled="true"
              android:exported="false">
        <intent-filter>
            <action android:name="android.intent.action.BOOT_COMPLETED" />
        </intent-filter>
    </receiver>
</application>""", "nonexported reminder receiver")

dialogs_path.write_text(dialogs, encoding="utf-8")
cell_path.write_text(cell, encoding="utf-8")
manifest_path.write_text(manifest, encoding="utf-8")
reminder_asset = Path(__file__).resolve().parents[1] / "TMessagesProj/src/main/java/org/telegram/ui/NabdhSwipeReminder.java"
if not reminder_asset.is_file():
    raise SystemExit("Missing approved local reminder receiver")
(ui / "NabdhSwipeReminder.java").write_bytes(reminder_asset.read_bytes())
print("Smart Swipe V1.1 installed with independent right gesture and real inline buttons.")
