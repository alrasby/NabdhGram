package org.telegram.ui.Components;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;

/** Owns card surfaces, outline and clipping; native dialog content remains separate. */
public final class NabdhCardRenderer {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path outline = new Path();
    public void clip(Canvas canvas, RectF bounds, float radius) {
        outline.reset();
        outline.addRoundRect(bounds, radius, radius, Path.Direction.CW);
        canvas.clipPath(outline);
    }
    public void reveal(Canvas canvas, RectF bounds, float radius, int color) {
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(color);
        canvas.drawRoundRect(bounds, radius, radius, paint);
    }
    public void content(Canvas canvas, RectF bounds, float radius, float stroke,
                        int fill, int border, int alpha) {
        reveal(canvas, bounds, radius, fill);
        if (alpha > 0) {
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(stroke);
            paint.setColor(border);
            paint.setAlpha(alpha);
            canvas.drawRoundRect(bounds, radius, radius, paint);
        }
        paint.setStyle(Paint.Style.FILL);
        paint.setAlpha(255);
    }
}
