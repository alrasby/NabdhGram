package org.telegram.ui.Components;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.RectF;

/** Composes the stationary action surface and translated dialog surface in one viewport. */
public final class NabdhCardEngine {
    private final RectF bounds = new RectF();
    private final NabdhCardRenderer renderer = new NabdhCardRenderer();
    private int radius;

    public void setViewport(int width, int height, int horizontal, int vertical, int radius) {
        bounds.set(horizontal, vertical, width - horizontal, height - vertical);
        this.radius = radius;
    }

    public void clipViewport(Canvas canvas) {
        renderer.clip(canvas, bounds, radius);
    }

    public void drawContent(Canvas canvas, int surface, int accent, int alternate,
                            boolean archived, boolean pinned, boolean selected, int style, int stroke) {
        final int fill;
        if (selected) {
            fill = blend(surface, accent, 0.23f);
        } else if (archived) {
            fill = blend(surface, alternate, 0.67f);
        } else if (pinned) {
            fill = blend(surface, accent, 0.19f);
        } else if (style == 0) {
            fill = surface;
        } else {
            fill = blend(surface, alternate, style == 1 ? 0.30f : 0.55f);
        }
        int border = blend(archived ? alternate : surface, accent, pinned ? 0.34f : 0.22f);
        int opacity = style == 0 ? 0 : style == 1 ? 70 : style == 2 ? 220 : 176;
        renderer.content(canvas, bounds, radius, stroke, fill, border, opacity);
    }

    public void drawAction(Canvas canvas, int base, int accent, float progress) {
        renderer.reveal(canvas, bounds, radius, blend(base, accent, progress));
    }

    public void clipTrailingAction(Canvas canvas, float translation) {
        canvas.clipRect(NabdhCardGeometry.revealLeft(bounds.left, bounds.right, translation),
                bounds.top, bounds.right, bounds.bottom);
    }

    private static int blend(int base, int tint, float ratio) {
        float remaining = 1f - ratio;
        return Color.rgb(Math.round(Color.red(base) * remaining + Color.red(tint) * ratio),
                Math.round(Color.green(base) * remaining + Color.green(tint) * ratio),
                Math.round(Color.blue(base) * remaining + Color.blue(tint) * ratio));
    }
}
