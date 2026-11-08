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
s = s.replace(anchor, """        // Render behind Telegram text and avatars; pressed/selected cards get teal feedback.
        // Pinned rows get a distinct teal-tinted surface without reordering dialogs.
        final int nabdhSurface = Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider);
        final boolean nabdhDark = android.graphics.Color.red(nabdhSurface)
                + android.graphics.Color.green(nabdhSurface)
                + android.graphics.Color.blue(nabdhSurface) < 360;
        final boolean nabdhPinned = getIsPinned();
        final boolean nabdhActive = isPressed() || isSelected();
        final int nabdhTint = nabdhPinned
                ? (nabdhDark ? 0xFF104B52 : 0xFFE0F5F2)
                : (nabdhDark ? 0xFF172D36 : 0xFFF6FBFB);
        nabdhCardPaint.setColor(nabdhActive
                ? (nabdhDark ? 0xFF146E75 : 0xFFB6E9E6) : nabdhTint);
        nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);
        final float nabdhInset = dp(7);
        nabdhCardBounds.set(nabdhInset, dp(3), getMeasuredWidth() - nabdhInset,
                getMeasuredHeight() - dp(3));
        canvas.drawRoundRect(nabdhCardBounds, dp(17), dp(17), nabdhCardPaint);
        nabdhCardPaint.setColor(nabdhPinned
                ? (nabdhDark ? 0xFF1CA6A6 : 0xFF8ACFCC)
                : (nabdhDark ? 0xFF24545D : 0xFFD9EAEA));
        nabdhCardPaint.setStyle(android.graphics.Paint.Style.STROKE);
        nabdhCardPaint.setStrokeWidth(dp(1));
        canvas.drawRoundRect(nabdhCardBounds, dp(17), dp(17), nabdhCardPaint);
        nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);

""" + anchor, 1)
p.write_text(s, encoding="utf-8")
print("NabdhGram Glass dialog card drawing overlay installed.")
