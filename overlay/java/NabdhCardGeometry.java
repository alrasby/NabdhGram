package org.telegram.ui.Components;

/** Pure geometry and tap policy, shared by rendering and gesture handling. */
public final class NabdhCardGeometry {
    public static final int HORIZONTAL_INSET_DP = 7;
    public static final int VERTICAL_INSET_DP = 3;
    public static final int CORNER_RADIUS_DP = 17;

    private NabdhCardGeometry() {}
    // Mirrors the pinned MessagesController folder eligibility rule.
    public static boolean canMoveToFolder(long dialogId, long selfId, int targetFolder) {
        return targetFolder == 0 || (targetFolder == 1 && dialogId != selfId && dialogId != 777000L);
    }
    public static int trayWidth(float translation, int max) {
        return Math.max(0, Math.min(Math.max(0, max), Math.round(translation)));
    }
    public static float revealRight(float left, float right, float translation) {
        return Math.max(left, Math.min(right, left + Math.max(0f, translation)));
    }
    public static float revealLeft(float left, float right, float translation) {
        return Math.min(right, Math.max(left, right + Math.min(0f, translation)));
    }
    public static boolean hit(float x, float y, float left, float top, float right, float bottom) {
        return x >= left && x < right && y >= top && y < bottom;
    }
    public static boolean acceptTap(boolean released, float dx, float dy, int slop, int down, int up) {
        return released && down >= 0 && down < 4 && down == up
                && Math.abs(dx) < slop && Math.abs(dy) < slop;
    }
}
