package org.telegram.ui.Components;

import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import androidx.dynamicanimation.animation.FloatPropertyCompat;
import androidx.dynamicanimation.animation.SpringAnimation;
import androidx.dynamicanimation.animation.SpringForce;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.ui.Cells.DialogCell;

import static org.telegram.messenger.AndroidUtilities.dp;

/** Owns Smart Swipe pointer capture, row lifecycle and snap animations. */
public final class NabdhSmartSwipeController implements RecyclerView.OnItemTouchListener {
    public interface Host {
        boolean canBegin();
        boolean isEligible(long dialogId);
        boolean configure(DialogCell row, DialogCell.NabdhSmartAction callback);
        void suppressClick();
        void runAction(long dialogId, int action);
    }

    private final Host host;

    public NabdhSmartSwipeController(Host host) {
        this.host = host;
    }

    private DialogCell candidate;
    private DialogCell expanded;
    private DialogCell settlingRow;
    private long gestureDialogId;
    private SpringAnimation spring;
    private float downX, downY, startingX;
    private enum Gesture { IDLE, TOUCH_PENDING, DRAGGING, TRAY_TOUCH }
    private Gesture gesture = Gesture.IDLE;
    private float actionDownX, actionDownY, actionStartOffset;
    private final NabdhSwipeActionPress actionPress =
            new NabdhSwipeActionPress();
    private final View.OnAttachStateChangeListener rowAttachment =
            new View.OnAttachStateChangeListener() {
        @Override public void onViewAttachedToWindow(View view) {}
        @Override public void onViewDetachedFromWindow(View view) {
            view.removeOnAttachStateChangeListener(this);
            if (view == candidate || view == expanded || view == settlingRow) {
                cancel();
            }
        }
    };

    public void cancel() {
        if (spring != null) spring.cancel();
        resetRow(settlingRow);
        if (expanded != settlingRow) resetRow(expanded);
        if (candidate != settlingRow && candidate != expanded && gesture == Gesture.DRAGGING) resetRow(candidate);
        settlingRow = null;
        expanded = null;
        candidate = null;
        gesture = Gesture.IDLE;
        actionPress.cancel();
    }

    private void resetRow(DialogCell row) {
        if (row == null) return;
        row.removeOnAttachStateChangeListener(rowAttachment);
        row.nabdhClearSmartSwipeActions();
        row.setTranslationX(0f);
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
        spring = new SpringAnimation(row,
                new FloatPropertyCompat<DialogCell>(
                        "nabdhSmartSwipeX") {
                    @Override public float getValue(DialogCell value) {
                        return value.getTranslationX();
                    }
                    @Override public void setValue(DialogCell value, float x) {
                        if (value.getDialogId() == boundId) value.setTranslationX(x);
                    }
                });
        SpringForce force =
                new SpringForce(target);
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
            MotionEvent event) {
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            gesture = Gesture.IDLE;
            actionPress.cancel();
            candidate = null;
            downX = event.getX();
            downY = event.getY();
            if (!host.canBegin()) {
                close();
                return false;
            }
            if (expanded != null) {
                // The list owns click/long-press handlers even when buttons
                // are children of DialogCell. Fully consume tray touches.
                host.suppressClick();
                gesture = Gesture.TRAY_TOUCH;
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
            View child = recycler.findChildViewUnder(downX, downY);
            if (!(child instanceof DialogCell)) return false;
            DialogCell row = (DialogCell) child;
            long id = row.getDialogId();
            if (!row.nabdhCanSwipe() || !host.isEligible(id)) return false;
            candidate = row;
            gesture = Gesture.TOUCH_PENDING;
            gestureDialogId = id;
            startingX = row.getTranslationX();
            return false;
        }
        if (action == MotionEvent.ACTION_POINTER_DOWN) {
            candidate = null;
            gesture = Gesture.IDLE;
        }
        if (action == MotionEvent.ACTION_MOVE && candidate != null) {
            if (candidate.getDialogId() != gestureDialogId) {
                candidate = null;
                return false;
            }
            float dx = event.getX() - downX;
            float dy = event.getY() - downY;
            int slop = ViewConfiguration.get(
                    recycler.getContext()).getScaledTouchSlop();
            final NabdhSwipeMotion.Decision decision =
                    NabdhSwipeMotion.classify(
                            startingX, dx, dy, slop, dp(36));
            if (decision == NabdhSwipeMotion.Decision.CLAIM) {
                final DialogCell row = candidate;
                final long dialogId = row.getDialogId();
                if (!host.configure(row, index -> {
                    if (expanded == row && row.getDialogId() == dialogId) {
                        close();
                        host.runAction(dialogId, index);
                    }
                })) {
                    candidate = null;
                    return false;
                }
                row.addOnAttachStateChangeListener(rowAttachment);
                gesture = Gesture.DRAGGING;
                host.suppressClick();
                if (spring != null) spring.cancel();
                if (settlingRow != null && settlingRow != row) {
                    settlingRow.removeOnAttachStateChangeListener(rowAttachment);
                    settlingRow.nabdhClearSmartSwipeActions();
                    settlingRow.setTranslationX(0f);
                    settlingRow = null;
                }
                recycler.getParent().requestDisallowInterceptTouchEvent(true);
                row.setTranslationX(NabdhSwipeMotion.offset(
                        startingX, dx, dp(212)));
                return true;
            }
            if (decision == NabdhSwipeMotion.Decision.YIELD) {
                candidate = null;
            }
        }
        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            candidate = null;
        }
        if (candidate == null) gesture = Gesture.IDLE;
        return false;
    }

    @Override public void onTouchEvent(RecyclerView recycler,
            MotionEvent event) {
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_POINTER_DOWN) {
            cancel();
            return;
        }
        if (expanded != null && expanded.getDialogId() != gestureDialogId
                || candidate != null && candidate.getDialogId() != gestureDialogId) {
            cancel();
            return;
        }
        if (gesture == Gesture.TRAY_TOUCH) {
            final int slop = ViewConfiguration.get(
                    recycler.getContext()).getScaledTouchSlop();
            float dx = event.getX() - actionDownX;
            int hit = expanded == null ? -1 : expanded.nabdhSmartActionAt(
                    event.getX() - expanded.getLeft(), event.getY() - expanded.getTop());
            if (expanded != null && action == MotionEvent.ACTION_MOVE) {
                float dy = event.getY() - actionDownY;
                if (Math.abs(dy) > slop && Math.abs(dy) > Math.abs(dx)) {
                    actionPress.cancel();
                    close();
                } else if (dx < -slop && Math.abs(dx) > Math.abs(dy) * 1.5f) {
                    if (spring != null) spring.cancel();
                    expanded.setTranslationX(NabdhSwipeMotion.offset(
                            actionStartOffset, dx, dp(212)));
                }
            }
            if (expanded != null && action == MotionEvent.ACTION_MOVE
                    && !actionPress.update(event.getPointerId(0), event.getX(),
                            event.getY(), slop, hit)) {
                expanded.nabdhSetSmartPressed(-1);
            }
            if (action == MotionEvent.ACTION_UP
                    || action == MotionEvent.ACTION_CANCEL) {
                DialogCell row = expanded;
                int actionIndex = -1;
                if (action == MotionEvent.ACTION_UP) {
                    actionIndex = actionPress.release(event.getPointerId(0), event.getX(),
                            event.getY(), slop, hit);
                } else {
                    actionPress.cancel();
                }
                if (row != null) row.nabdhSetSmartPressed(-1);
                gesture = Gesture.IDLE;
                if (row != null && row.getParent() == recycler
                        && actionIndex >= 0) {
                    // Delegate to a real TextView.performClick(), not to
                    // RecyclerListView's underlying item click handler.
                    row.nabdhPerformSmartAction(actionIndex);
                } else if (row != null && (action == MotionEvent.ACTION_CANCEL
                        || row.getTranslationX() < dp(135))) {
                    close();
                } else if (row != null) {
                    settle(row, dp(212));
                }
            }
            return;
        }
        if (candidate == null || gesture != Gesture.DRAGGING) return;
        if (action == MotionEvent.ACTION_MOVE) {
            float dx = event.getX() - downX;
            candidate.setTranslationX(NabdhSwipeMotion.offset(
                    startingX, dx, dp(212)));
        } else if (action == MotionEvent.ACTION_UP
                || action == MotionEvent.ACTION_CANCEL) {
            DialogCell row = candidate;
            boolean open = action == MotionEvent.ACTION_UP
                    && row.getTranslationX() > (startingX > 0 ? dp(135) : dp(68))
                    && row.getParent() == recycler;
            candidate = null;
            gesture = Gesture.IDLE;
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
}
