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

dialogs = once(dialogs,
    "        private SwipeController swipeController;",
    "        private SwipeController swipeController;\n        private Runnable nabdhCancelSwipe;",
    "store the gesture lifecycle with its list page")
dialogs = once(dialogs,
    "    public void onPause() {\n        super.onPause();",
    """    public void onPause() {
        if (viewPages != null) {
            for (ViewPage page : viewPages) {
                if (page != null && page.nabdhCancelSwipe != null) page.nabdhCancelSwipe.run();
            }
        }
        super.onPause();""",
    "cancel active gestures when leaving the dialogs screen")

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
            final int previousFolder = dialog.folder_id;
            final int targetFolder = previousFolder == 0 ? 1 : 0;
            final long selfId = getUserConfig().getClientUserId();
            final boolean rtl = LocaleController.isRTL;
            if (!org.telegram.ui.Components.NabdhCardGeometry.canMoveToFolder(
                    dialogId, selfId, targetFolder)) {
                android.widget.Toast.makeText(getParentActivity(),
                        rtl ? "لا يسمح تيليجرام بأرشفة هذه المحادثة" :
                                "Telegram does not allow archiving this chat",
                        android.widget.Toast.LENGTH_SHORT).show();
                return;
            }
            final int previousPin = dialog.pinnedNum;
            final int result = getMessagesController().addDialogToFolder(
                    dialogId, targetFolder, -1, 0);
            final TLRPC.Dialog updated = getMessagesController().dialogs_dict.get(dialogId);
            if (result == 0 || updated == null || updated.folder_id != targetFolder) {
                android.widget.Toast.makeText(getParentActivity(),
                        rtl ? "لم تنتقل المحادثة" : "Chat was not moved",
                        android.widget.Toast.LENGTH_SHORT).show();
                return;
            }
            if (targetFolder == 1) {
                if (result == 2 && SharedConfig.archiveHidden) SharedConfig.toggleArchiveHidden();
                final UndoView undoView = getUndoView();
                if (undoView != null) {
                    undoView.showWithAction(0, UndoView.ACTION_ARCHIVE, null,
                            () -> getMessagesController().addDialogToFolder(
                                    dialogId, previousFolder, previousPin, 0));
                }
            }
        }
    }

    private void installNabdhSmartSwipe(ViewPage page) {
        page.listView.addOnItemTouchListener(new RecyclerView.OnItemTouchListener() {
            private DialogCell candidate;
            private DialogCell expanded;
            private DialogCell settlingRow;
            private long gestureDialogId;
            private androidx.dynamicanimation.animation.SpringAnimation spring;
            private float downX, downY, startingX;
            private boolean dragging;
            private boolean consumedDown;
            private float actionDownX, actionDownY, actionStartOffset;
            private final org.telegram.ui.Components.NabdhSwipeActionPress actionPress =
                    new org.telegram.ui.Components.NabdhSwipeActionPress();
            private final android.view.View.OnAttachStateChangeListener rowAttachment =
                    new android.view.View.OnAttachStateChangeListener() {
                @Override public void onViewAttachedToWindow(android.view.View view) {}
                @Override public void onViewDetachedFromWindow(android.view.View view) {
                    view.removeOnAttachStateChangeListener(this);
                    if (view == candidate || view == expanded || view == settlingRow) {
                        page.nabdhCancelSwipe.run();
                    }
                }
            };

            {
                page.nabdhCancelSwipe = () -> {
                    if (spring != null) spring.cancel();
                    if (settlingRow != null) {
                        settlingRow.removeOnAttachStateChangeListener(rowAttachment);
                        settlingRow.nabdhClearSmartSwipeActions();
                        settlingRow.setTranslationX(0f);
                        settlingRow = null;
                    }
                    if (expanded != null) {
                        expanded.removeOnAttachStateChangeListener(rowAttachment);
                        expanded.nabdhClearSmartSwipeActions();
                        expanded.setTranslationX(0f);
                        expanded = null;
                    }
                    if (candidate != null) {
                        candidate.removeOnAttachStateChangeListener(rowAttachment);
                        candidate.nabdhClearSmartSwipeActions();
                        candidate.setTranslationX(0f);
                        candidate = null;
                    }
                    dragging = false;
                    consumedDown = false;
                    actionPress.cancel();
                };
            }

            private void settle(DialogCell row, float target) {
                if (row == null) return;
                if (spring != null) spring.cancel();
                if (settlingRow != null && settlingRow != row) {
                    settlingRow.removeOnAttachStateChangeListener(rowAttachment);
                    settlingRow.nabdhClearSmartSwipeActions();
                    settlingRow.setTranslationX(0f);
                }
                settlingRow = row;
                final long boundId = row.getDialogId();
                spring = new androidx.dynamicanimation.animation.SpringAnimation(row,
                        new androidx.dynamicanimation.animation.FloatPropertyCompat<DialogCell>(
                                "nabdhSmartSwipeX") {
                            @Override public float getValue(DialogCell value) {
                                return value.getTranslationX();
                            }
                            @Override public void setValue(DialogCell value, float x) {
                                if (value.getDialogId() == boundId) value.setTranslationX(x);
                            }
                        });
                androidx.dynamicanimation.animation.SpringForce force =
                        new androidx.dynamicanimation.animation.SpringForce(target);
                force.setStiffness(550f);
                force.setDampingRatio(0.88f);
                spring.setSpring(force);
                spring.setMinValue(0f);
                spring.setMaxValue(dp(212));
                spring.setMinimumVisibleChange(0.7f);
                spring.addEndListener((animation, cancelled, value, velocity) -> {
                    if (!cancelled) {
                        settlingRow = null;
                        if (target == 0f) {
                            row.removeOnAttachStateChangeListener(rowAttachment);
                            if (row.getDialogId() == boundId) row.nabdhClearSmartSwipeActions();
                        }
                    }
                });
                if (android.os.Build.VERSION.SDK_INT >= 26
                        && !android.animation.ValueAnimator.areAnimatorsEnabled()) {
                    row.setTranslationX(target);
                    if (target == 0f) {
                        row.removeOnAttachStateChangeListener(rowAttachment);
                        row.nabdhClearSmartSwipeActions();
                    }
                    settlingRow = null;
                    return;
                }
                spring.start();
            }

            private void close() {
                if (expanded != null) {
                    DialogCell old = expanded;
                    expanded = null;
                    old.nabdhSetSmartPressed(-1);
                    settle(old, 0f);
                }
            }

            @Override public boolean onInterceptTouchEvent(RecyclerView recycler,
                    android.view.MotionEvent event) {
                int action = event.getActionMasked();
                if (action == android.view.MotionEvent.ACTION_DOWN) {
                    consumedDown = false;
                    actionPress.cancel();
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
                        actionStartOffset = expanded.getTranslationX();
                        gestureDialogId = expanded.getDialogId();
                        float cx = event.getX() - expanded.getLeft();
                        float cy = event.getY() - expanded.getTop();
                        if (expanded.getParent() != recycler
                                || cx < dp(7) || cx >= dp(219) || cy < dp(3)
                                || cy > expanded.getHeight() - dp(3)
                                || expanded.getTranslationX() < dp(140)) {
                            close();
                            return true; // Outside tap dismisses without chat opening.
                        }
                        int pressedAction = expanded.nabdhSmartActionAt(cx, cy);
                        if (pressedAction >= 0) {
                            actionPress.begin(event.getPointerId(0), pressedAction,
                                    event.getX(), event.getY());
                            expanded.nabdhSetSmartPressed(pressedAction);
                        }
                        return true;
                    }
                    if (downX <= dp(24)
                            || downX >= recycler.getWidth() - dp(24)) return false;
                    android.view.View child = recycler.findChildViewUnder(downX, downY);
                    if (!(child instanceof DialogCell)) return false;
                    DialogCell row = (DialogCell) child;
                    long id = row.getDialogId();
                    if (!row.nabdhOwnsCard() || DialogObject.isFolderDialogId(id)
                            || getMessagesController().isPromoDialog(id, false)
                            || getMessagesController().dialogs_dict.get(id) == null
                            || page.dialogsType != DIALOGS_TYPE_DEFAULT
                            && page.dialogsType != DIALOGS_TYPE_FOLDER1
                            && page.dialogsType != DIALOGS_TYPE_FOLDER2) return false;
                    candidate = row;
                    gestureDialogId = id;
                    startingX = row.getTranslationX();
                    return false;
                }
                if (action == android.view.MotionEvent.ACTION_POINTER_DOWN) candidate = null;
                if (action == android.view.MotionEvent.ACTION_MOVE && candidate != null) {
                    if (candidate.getDialogId() != gestureDialogId) {
                        candidate = null;
                        return false;
                    }
                    float dx = event.getX() - downX;
                    float dy = event.getY() - downY;
                    int slop = android.view.ViewConfiguration.get(
                            recycler.getContext()).getScaledTouchSlop();
                    final org.telegram.ui.Components.NabdhSwipeMotion.Decision decision =
                            org.telegram.ui.Components.NabdhSwipeMotion.classify(
                                    startingX, dx, dy, slop, dp(36));
                    if (decision == org.telegram.ui.Components.NabdhSwipeMotion.Decision.CLAIM) {
                        final DialogCell row = candidate;
                        final long dialogId = row.getDialogId();
                        final TLRPC.Dialog current = getMessagesController().dialogs_dict.get(dialogId);
                        if (current == null) {
                            candidate = null;
                            return false;
                        }
                        row.removeOnAttachStateChangeListener(rowAttachment);
                        row.addOnAttachStateChangeListener(rowAttachment);
                        row.nabdhSetSmartSwipeActions(index -> {
                            if (expanded == row && row.getDialogId() == dialogId) {
                                close();
                                nabdhRunSmartAction(dialogId, index);
                            }
                        }, getMessagesController().isDialogMuted(dialogId, 0),
                                isDialogPinned(current), current.folder_id != 0);
                        dragging = true;
                        nabdhIgnoreItemClicksUntil =
                                android.os.SystemClock.uptimeMillis() + 450L;
                        page.listView.cancelClickRunnables(true);
                        if (spring != null) spring.cancel();
                        if (settlingRow != null && settlingRow != row) {
                            settlingRow.removeOnAttachStateChangeListener(rowAttachment);
                            settlingRow.nabdhClearSmartSwipeActions();
                            settlingRow.setTranslationX(0f);
                            settlingRow = null;
                        }
                        recycler.getParent().requestDisallowInterceptTouchEvent(true);
                        row.setTranslationX(org.telegram.ui.Components.NabdhSwipeMotion.offset(
                                startingX, dx, dp(212)));
                        return true;
                    }
                    if (decision == org.telegram.ui.Components.NabdhSwipeMotion.Decision.YIELD) {
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
                if (action == android.view.MotionEvent.ACTION_POINTER_DOWN) {
                    page.nabdhCancelSwipe.run();
                    return;
                }
                if (expanded != null && expanded.getDialogId() != gestureDialogId
                        || candidate != null && candidate.getDialogId() != gestureDialogId) {
                    page.nabdhCancelSwipe.run();
                    return;
                }
                if (consumedDown) {
                    final int slop = android.view.ViewConfiguration.get(
                            recycler.getContext()).getScaledTouchSlop();
                    float dx = event.getX() - actionDownX;
                    int hit = expanded == null ? -1 : expanded.nabdhSmartActionAt(
                            event.getX() - expanded.getLeft(), event.getY() - expanded.getTop());
                    if (expanded != null && action == android.view.MotionEvent.ACTION_MOVE) {
                        float dy = event.getY() - actionDownY;
                        if (Math.abs(dy) > slop && Math.abs(dy) > Math.abs(dx)) {
                            actionPress.cancel();
                            close();
                        } else if (dx < -slop && Math.abs(dx) > Math.abs(dy) * 1.5f) {
                            if (spring != null) spring.cancel();
                            expanded.setTranslationX(org.telegram.ui.Components.NabdhSwipeMotion.offset(
                                    actionStartOffset, dx, dp(212)));
                        }
                    }
                    if (expanded != null && action == android.view.MotionEvent.ACTION_MOVE
                            && !actionPress.update(event.getPointerId(0), event.getX(),
                                    event.getY(), slop, hit)) {
                        expanded.nabdhSetSmartPressed(-1);
                    }
                    if (action == android.view.MotionEvent.ACTION_UP
                            || action == android.view.MotionEvent.ACTION_CANCEL) {
                        DialogCell row = expanded;
                        int actionIndex = -1;
                        if (action == android.view.MotionEvent.ACTION_UP) {
                            actionIndex = actionPress.release(event.getPointerId(0), event.getX(),
                                    event.getY(), slop, hit);
                        } else {
                            actionPress.cancel();
                        }
                        if (row != null) row.nabdhSetSmartPressed(-1);
                        consumedDown = false;
                        if (row != null && row.getParent() == recycler
                                && actionIndex >= 0) {
                            // Delegate to a real TextView.performClick(), not to
                            // RecyclerListView's underlying item click handler.
                            row.nabdhPerformSmartAction(actionIndex);
                        } else if (row != null && (action == android.view.MotionEvent.ACTION_CANCEL
                                || row.getTranslationX() < dp(135))) {
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
                    candidate.setTranslationX(org.telegram.ui.Components.NabdhSwipeMotion.offset(
                            startingX, dx, dp(212)));
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
                        && page.nabdhCancelSwipe != null) {
                    page.nabdhCancelSwipe.run();
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
        // The stationary card reveal owns the surface; this child only draws buttons.
        nabdhSmartBar.setBackground(null);
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
        nabdhUpdateSmartTrayClip(translationX);
        nabdhSmartBar.setVisibility(translationX > 0
                ? android.view.View.VISIBLE : android.view.View.GONE);
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
    """        final boolean closingSmartSwipe = translationX > 0 && value == 0;
        translationX = value;
        if (closingSmartSwipe) isSliding = false;
        if (nabdhSmartBar != null) {
            if (value > 0 && nabdhSmartAction != null) {
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
            // The stationary surface also fills the space behind the moving
            // rounded corner. The outer viewport clips both layers.
            nabdhSetCardBounds();
            nabdhRenderer.reveal(canvas, nabdhCardBounds, nabdhCardRadius(),
                    nabdhBlendThemeColor(
                    Theme.getColor(Theme.key_windowBackgroundGray, resourcesProvider),
                    Theme.getColor(Theme.key_chats_archiveBackground, resourcesProvider), 0.20f));
            canvas.restore();
        }
        if (translationX < 0) {
            canvas.save();
            canvas.translate(0, -translateY);
            // Owned rows already have the enclosing rounded viewport.""",
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

                Theme.dialogs_pinnedPaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider));""", "remove right-swipe white backing without affecting native LEFT")

# Owned cards use the same renderer for BOTH reveal directions. The native
# action icon and localized text remain; native rectangular/circular fills
# only run for rows outside the Nabdh card engine.
cell = once(cell,
    "                canvas.drawRect(tx - dp(8), 0, getMeasuredWidth(), getMeasuredHeight(), Theme.dialogs_pinnedPaint);",
    """                if (!nabdhOwnsCard()) {
                    canvas.drawRect(tx - dp(8), 0, getMeasuredWidth(), getMeasuredHeight(), Theme.dialogs_pinnedPaint);
                }""", "remove native rectangular fill for owned rows")
cell = once(cell,
    "                canvas.drawCircle(drawableCx, drawableCy, rad * AndroidUtilities.accelerateInterpolator.getInterpolation(currentRevealProgress), Theme.dialogs_pinnedPaint);",
    """                if (!nabdhOwnsCard()) {
                    canvas.drawCircle(drawableCx, drawableCy, rad * AndroidUtilities.accelerateInterpolator.getInterpolation(currentRevealProgress), Theme.dialogs_pinnedPaint);
                }""", "remove native animated circle fill for owned rows")
cell = once(cell,
    "            float tx = getMeasuredWidth() + translationX;",
    """            float tx = getMeasuredWidth() + translationX;
            if (nabdhOwnsCard()) {
                nabdhSetCardBounds();
                nabdhRenderer.reveal(canvas, nabdhCardBounds, nabdhCardRadius(),
                        nabdhBlendThemeColor(backgroundColor, revealBackgroundColor,
                                Math.max(0f, Math.min(1f, currentRevealProgress))));
                // Clip native glyphs to the exposed strip; the stationary
                // surface continues behind the moving rounded corner.
                canvas.clipRect(org.telegram.ui.Components.NabdhCardGeometry.revealLeft(
                        nabdhCardBounds.left, nabdhCardBounds.right, translationX),
                        nabdhCardBounds.top, nabdhCardBounds.right, nabdhCardBounds.bottom);
            }""", "render native action surface through card renderer")

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

for name in ("NabdhSwipeActionPress.java", "NabdhSwipeMotion.java"):
    asset = Path(__file__).resolve().parents[1] / "overlay/java" / name
    (ui / "Components" / name).write_bytes(asset.read_bytes())
dialogs_path.write_text(dialogs, encoding="utf-8")
cell_path.write_text(cell, encoding="utf-8")
manifest_path.write_text(manifest, encoding="utf-8")
reminder_asset = Path(__file__).resolve().parents[1] / "TMessagesProj/src/main/java/org/telegram/ui/NabdhSwipeReminder.java"
if not reminder_asset.is_file():
    raise SystemExit("Missing approved local reminder receiver")
(ui / "NabdhSwipeReminder.java").write_bytes(reminder_asset.read_bytes())
print("Smart Swipe V1.1 installed with independent right gesture and real inline buttons.")
