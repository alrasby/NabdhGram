package org.telegram.ui.Components;

/** Determines when the Smart Swipe listener owns a pointer stream. */
public final class NabdhSwipeMotion {
    public enum Decision { PENDING, CLAIM, YIELD }

    private NabdhSwipeMotion() {}

    public static Decision classify(float start, float dx, float dy, int slop, int verticalLimit) {
        float horizontal = Math.abs(dx);
        float vertical = Math.abs(dy);
        boolean inDirection = start > 0 ? dx < -slop : dx > slop;
        if (inDirection && horizontal > vertical * 1.5f && vertical < verticalLimit) {
            return Decision.CLAIM;
        }
        if (vertical > slop * 1.5f || (start == 0 && dx < -slop)) {
            return Decision.YIELD;
        }
        return Decision.PENDING;
    }

    public static float offset(float start, float dx, int maximum) {
        return Math.max(0f, Math.min(maximum, start + dx));
    }
}
