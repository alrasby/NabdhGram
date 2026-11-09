#!/usr/bin/env python3
"""Draw lightweight NabdhGram Glass cards behind dialog rows.

No changes to adapter ordering, click targets, Telegram message state or storage.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-dialog-cards.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java"
s = p.read_text(encoding="utf-8")
anchor = "    protected void onDraw(Canvas canvas) {\n        if (currentDialogId == 0 && customDialog == null) {"
if s.count(anchor) != 1:
    raise SystemExit("DialogCell drawing anchor changed")
# Use a reused Paint, avoid allocations and expensive blur during scrolling.
field_anchor = "    private boolean drawPinBackground;"
if s.count(field_anchor) != 1:
    raise SystemExit("DialogCell pinned state anchor changed")
s = s.replace(field_anchor, """    // NabdhGram Glass: cached paint for rounded chat surfaces.
    private final android.graphics.Paint nabdhCardPaint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    private final android.graphics.RectF nabdhCardBounds = new android.graphics.RectF();
""" + field_anchor, 1)
# Draw after Telegram's base pinned/archive background, before message content.
# Painting at the beginning of onDraw would be hidden by the later base fill.
anchor = "        canvas.restore();\n\n        updateHelper.updateAnimationValues();"
if s.count(anchor) != 1:
    raise SystemExit(f"DialogCell card rendering anchor changed: {s.count(anchor)}")
s = s.replace(anchor, """        canvas.restore();

        // NabdhGram Glass: draw only for normal dialog rows, after Telegram
        // backgrounds and before message content. Do not interfere with archive,
        // swipe-to-reveal, tablet slide effects, or transient edit animations.
        if (translationX == 0 && currentRevealProgress == 0.0f
                && rightFragmentOpenedProgress == 0.0f && !drawArchive
                && currentDialogFolderId == 0 && !isTopic
                && getMeasuredWidth() > dp(20) && getMeasuredHeight() > dp(12)) {
            final int surface = Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider);
            final boolean dark = android.graphics.Color.red(surface)
                    + android.graphics.Color.green(surface)
                    + android.graphics.Color.blue(surface) < 360;
            final boolean pinned = getIsPinned();
            final boolean selected = isPressed() || isSelected || isSelected();
            final int fill = selected
                    ? (dark ? 0xFF146E75 : 0xFFB6E9E6)
                    : pinned ? (dark ? 0xFF104B52 : 0xFFE0F5F2)
                    : (dark ? 0xFF203A42 : 0xFFEAF6F5);
            // Keep Telegram's selection feedback, but confine our Glass
            // surface to the same rounded bounds for every dialog row.
            nabdhCardPaint.setColor(fill);
            nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);
            nabdhCardBounds.set(dp(7), dp(3), getMeasuredWidth() - dp(7),
                    getMeasuredHeight() - dp(3));
            canvas.drawRoundRect(nabdhCardBounds, dp(17), dp(17), nabdhCardPaint);
            nabdhCardPaint.setColor(pinned
                    ? (dark ? 0xFF1CA6A6 : 0xFF8ACFCC)
                    : (dark ? 0xFF39727A : 0xFFBDDAD8));
            nabdhCardPaint.setStyle(android.graphics.Paint.Style.STROKE);
            nabdhCardPaint.setStrokeWidth(dp(1));
            canvas.drawRoundRect(nabdhCardBounds, dp(17), dp(17), nabdhCardPaint);
            nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);
        }

        updateHelper.updateAnimationValues();""", 1)

p.write_text(s, encoding="utf-8")
print("NabdhGram Glass dialog card drawing overlay installed.")
