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
geometry = Path(__file__).resolve().parents[1] / "overlay/java/NabdhCardGeometry.java"
target = p.parent.parent / "Components/NabdhCardGeometry.java"
if target.exists():
    raise SystemExit("Card geometry class collision")
target.write_bytes(geometry.read_bytes())
renderer = geometry.with_name("NabdhCardRenderer.java")
target.with_name(renderer.name).write_bytes(renderer.read_bytes())
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
    private final org.telegram.ui.Components.NabdhCardRenderer nabdhRenderer =
            new org.telegram.ui.Components.NabdhCardRenderer();
    private boolean nabdhOwnsCard() {
        return !isTopic && !(getParent() instanceof ProfileChannelCell)
                && getMeasuredWidth() > dp(20) && getMeasuredHeight() > dp(12);
    }
    private void nabdhSetCardBounds() {
        final int horizontal = dp(org.telegram.ui.Components.NabdhCardGeometry.HORIZONTAL_INSET_DP);
        final int vertical = dp(org.telegram.ui.Components.NabdhCardGeometry.VERTICAL_INSET_DP);
        nabdhCardBounds.set(horizontal, vertical,
                getMeasuredWidth() - horizontal, getMeasuredHeight() - vertical);
    }

    private int nabdhCardRadius() {
        return dp(org.telegram.ui.Components.NabdhCardGeometry.CORNER_RADIUS_DP);
    }
    // One outer viewport for background, native canvas and child views.
    @Override
    public void draw(android.graphics.Canvas canvas) {
        if (!nabdhOwnsCard() || isFolderCell() || rightFragmentOpenedProgress != 0f) {
            super.draw(canvas);
            return;
        }
        final int saved = canvas.save();
        try {
            nabdhClipCard(canvas);
            super.draw(canvas);
        } finally {
            canvas.restoreToCount(saved);
        }
    }

    private void nabdhClipCard(android.graphics.Canvas canvas) {
        nabdhSetCardBounds();
        nabdhRenderer.clip(canvas, nabdhCardBounds, nabdhCardRadius());
    }
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
# Telegram paints the swipe action BEHIND the translated conversation content.
# Paint the card inside that same translated canvas, after native backdrop
# preparation and before text. This keeps its surface visible during drag,
# reveal and spring-back rather than toggling between two backgrounds.
# Paint after native swipe-edge white backing; the previous early drawing
# was covered by Telegram when the corner animation became active.
anchor = """            if (drawNameLock) {
                setDrawableBounds(Theme.dialogs_lockDrawable, nameLockLeft, nameLockTop);
                Theme.dialogs_lockDrawable.draw(canvas);
            }"""
if s.count(anchor) != 1:
    raise SystemExit("Pinned Telegram content-stage drawing anchor changed")
s = s.replace(anchor, """        // This canvas already carries Telegram's translationX and any
        // right-fragment transform. Never hide the card when swiping: native
        // action colors stay behind it, and the same card follows its content.
        // The actual archive folder row is supported; topic/profile rows keep
        // their original native drawing.
        if (nabdhOwnsCard()) {
            final int surface = Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider);
            final int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, resourcesProvider);
            final int alternate = Theme.getColor(Theme.key_windowBackgroundGray, resourcesProvider);
            final boolean archived = isFolderCell();
            final boolean pinned = getIsPinned();
            final boolean selected = isSelected;
            final int fill = selected
                    ? nabdhBlendThemeColor(surface, accent, 0.23f)
                    : archived ? nabdhBlendThemeColor(surface, alternate, 0.67f)
                    : pinned ? nabdhBlendThemeColor(surface, accent, 0.19f)
                    : nabdhBlendThemeColor(surface, alternate, 0.55f);
            // Keep Telegram's selection feedback, but confine our Glass
            // surface to the same rounded bounds for every dialog row.
            final int uiStyle = org.telegram.ui.Components.NabdhAppearancePrefs.uiStyle();
            nabdhSetCardBounds();
            nabdhRenderer.content(canvas, nabdhCardBounds, nabdhCardRadius(), dp(1),
                    uiStyle == 0 && !selected && !pinned && !archived
                    ? surface : uiStyle == 1 && !selected && !pinned && !archived
                    ? nabdhBlendThemeColor(surface, alternate, 0.30f) : fill,
                    nabdhBlendThemeColor(archived ? alternate : surface, accent, pinned ? 0.34f : 0.22f),
                    uiStyle == 0 ? 0 : uiStyle == 1 ? 70 : uiStyle == 2 ? 220 : 176);
        }

""" + anchor, 1)

# Telegram paints a full-width rectangular selected background before the
# card. For dialog rows, restrict it to the SAME 7dp/3dp and 17dp shape as the
# card; otherwise the native selection bleeds outside the curved Glass edge.
# Preserve the native branch for topic/profile rows and its original paint.
selection_old = """        if (isSelected) {
            rect.set(0, 0, getMeasuredWidth(), AndroidUtilities.lerp(getMeasuredHeight(), getCollapsedHeight(), rightFragmentOpenedProgress));
            rect.offset(0, -translateY + collapseOffset);
            canvas.drawRoundRect(rect, cornersRadius, cornersRadius, Theme.dialogs_tabletSeletedPaint);
        }"""
selection_new = """        if (isSelected) {
            if (!isTopic && !(getParent() instanceof ProfileChannelCell)) {
                // Selected color is owned by the content renderer, not a second surface.
            } else {
                rect.set(0, 0, getMeasuredWidth(), AndroidUtilities.lerp(getMeasuredHeight(),
                        getCollapsedHeight(), rightFragmentOpenedProgress));
                rect.offset(0, -translateY + collapseOffset);
                canvas.drawRoundRect(rect, cornersRadius, cornersRadius,
                        Theme.dialogs_tabletSeletedPaint);
            }
        }"""
if s.count(selection_old) != 1:
    raise SystemExit("Pinned Telegram selected background changed")
s = s.replace(selection_old, selection_new, 1)

# Exact pinned native DialogCell reorder drawing (source verified in preflight).
original_reorder = "                Theme.dialogs_reorderDrawable.setAlpha((int) (reorderIconProgress * 255));\n                setDrawableBounds(Theme.dialogs_reorderDrawable, pinLeft, pinTop);\n                Theme.dialogs_reorderDrawable.draw(canvas);"
branded_reorder = "                // Glass-friendly drag grip on pinned chat cards only.\n                // Native reordering hit targets and sorting remain unchanged.\n                final int dragAccent = Theme.getColor(\n                        Theme.key_windowBackgroundWhiteBlueText, resourcesProvider);\n                nabdhCardPaint.setStyle(android.graphics.Paint.Style.STROKE);\n                nabdhCardPaint.setStrokeCap(android.graphics.Paint.Cap.ROUND);\n                nabdhCardPaint.setStrokeWidth(dp(2));\n                nabdhCardPaint.setColor(dragAccent);\n                nabdhCardPaint.setAlpha((int) (reorderIconProgress * 235));\n                final float dragX = pinLeft + dp(4);\n                for (int dragLine = 0; dragLine < 3; dragLine++) {\n                    final float dragY = pinTop + dp(5 + dragLine * 5);\n                    canvas.drawLine(dragX, dragY, dragX + dp(13), dragY, nabdhCardPaint);\n                }\n                nabdhCardPaint.setAlpha(255);\n                nabdhCardPaint.setStrokeCap(android.graphics.Paint.Cap.BUTT);\n                nabdhCardPaint.setStyle(android.graphics.Paint.Style.FILL);"
if s.count(original_reorder) != 1:
    raise SystemExit("Pinned DialogCell reorder drawing changed")
s = s.replace(original_reorder, branded_reorder, 1)

# Native Telegram paints a light full-width rectangular gradient behind the
# reorder handle. It escapes the rounded Glass card and appears as a white box.
# Delete only that legacy overlay, keeping drawReorder, reorderIconProgress,
# native drag events, and the new branded lines untouched.
reorder_gradient = "                if (!LocaleController.isRTL) {\n                    final Paint reorderGradientPaint = getPaintReorderGradient();\n                    reorderGradientPaint.setAlpha((int) (reorderIconProgress * 255));\n                    canvas.save();\n                    canvas.translate(pinLeft - dp(24), pinTop);\n                    canvas.drawRect(0, 0, getMeasuredWidth() - (pinLeft - dp(24)), dp(24), reorderGradientPaint);\n                    canvas.restore();\n                }"
if s.count(reorder_gradient) != 1:
    raise SystemExit("Pinned reorder gradient anchor changed")
s = s.replace(reorder_gradient, "", 1)

p.write_text(s, encoding="utf-8")
print("NabdhGram Glass dialog card drawing overlay installed.")
