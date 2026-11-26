package org.telegram.ui.Components;

/** Tracks one action press, including pointer identity and irreversible cancellation. */
public final class NabdhSwipeActionPress {
    private int pointer = -1;
    private int action = -1;
    private float downX;
    private float downY;

    public void begin(int pointer, int action, float x, float y) {
        this.pointer = pointer;
        this.action = action;
        downX = x;
        downY = y;
    }

    public boolean update(int pointer, float x, float y, int slop, int hit) {
        if (this.pointer == pointer
                && NabdhCardGeometry.acceptTap(true, x - downX, y - downY, slop, action, hit)) {
            return true;
        }
        cancel();
        return false;
    }

    public int release(int pointer, float x, float y, int slop, int hit) {
        int result = update(pointer, x, y, slop, hit) ? action : -1;
        cancel();
        return result;
    }

    public void cancel() {
        pointer = -1;
        action = -1;
    }
}
