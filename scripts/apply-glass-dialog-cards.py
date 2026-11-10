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
""" + """    // Blend resolved Telegram theme colors instead of fixed light/dark palette values.
    // This keeps imported .attheme palettes effective for the custom dialog cards.
    private static int nabdhBlendThemeColor(int base, int tint, float ratio) {
        float inv = 1.0f - ratio;
        return android.graphics.Color.rgb(
                Math.round(android.graphics.Color.red(base) * inv + android.graphics.Color.red(tint) * ratio),
                Math.round(android.graphics.Color.green(base) * inv + android.graphics.Color.green(tint) * ratio),
                Math.round(android.graphics.Color.blue(base) * inv + android.graphics.Color.blue(tint) * ratio));
    }

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
                && rightFragmentOpenedProgress == 0.0f
                // drawArchive defaults to true for ordinary Telegram dialogs;
                // it is NOT an archive-row test. Use folder ID instead.
                && !isTopic
                && !(getParent() instanceof ProfileChannelCell)
                && getMeasuredWidth() > dp(20) && getMeasuredHeight() > dp(12)) {
            final int surface = Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider);
            final int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, resourcesProvider);
            final int alternate = Theme.getColor(Theme.key_windowBackgroundGray, resourcesProvider);
            final boolean archived = isFolderCell();
            final boolean pinned = getIsPinned();
            final boolean selected = isPressed() || isSelected || isSelected();
            final int fill = selected
                    ? nabdhBlendThemeColor(surface, accent, 0.22f)
                    : archived ? nabdhBlendThemeColor(surface, alternate, 0.58f)
                    : pinned ? nabdhBlendThemeColor(surface, accent, 0.13f)
                    : nabdhBlendThemeColor(surface, alternate, 0.22f);
            // Keep Telegram's selection feedback, but confine our Glass
            // surface to the same rounded bounds for every dialog row.
            nabdhCardPaint.setColor(fill);
            nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);
            nabdhCardBounds.set(dp(7), dp(3), getMeasuredWidth() - dp(7),
                    getMeasuredHeight() - dp(3));
            canvas.drawRoundRect(nabdhCardBounds, dp(17), dp(17), nabdhCardPaint);
            nabdhCardPaint.setColor(nabdhBlendThemeColor(
                    archived ? alternate : surface, accent, pinned ? 0.45f : 0.22f));
            nabdhCardPaint.setStyle(android.graphics.Paint.Style.STROKE);
            nabdhCardPaint.setStrokeWidth(dp(1));
            canvas.drawRoundRect(nabdhCardBounds, dp(17), dp(17), nabdhCardPaint);
            nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);
        }

        updateHelper.updateAnimationValues();""", 1)

p.write_text(s, encoding="utf-8")
print("NabdhGram Glass dialog card drawing overlay installed.")
