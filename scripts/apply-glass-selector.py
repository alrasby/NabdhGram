#!/usr/bin/env python3
"""Clip Telegram's RecyclerListView selector to NabdhGram dialog cards only."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-selector.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Components/RecyclerListView.java"
s = p.read_text(encoding="utf-8")
anchor = "    private void drawSelector(Canvas canvas) {\n"
if s.count(anchor) != 1:
    raise SystemExit("RecyclerListView selector anchor changed")
field_anchor = "    private void drawSelector(Canvas canvas) {"
replacement = """    // Reuse clipping geometry while the user presses a dialog card.
    private final android.graphics.Path nabdhDialogSelectorPath = new android.graphics.Path();
    private final android.graphics.RectF nabdhDialogSelectorBounds = new android.graphics.RectF();

    private void drawSelector(Canvas canvas) {
        // Telegram draws the pressed overlay at the RecyclerListView level,
        // *above* DialogCell.onDraw. Clip that overlay rather than trying to
        // cover it from the child; leave non-dialog selectors unchanged.
        final boolean nabdhDialog = selectorView instanceof org.telegram.ui.Cells.DialogCell
                && ((org.telegram.ui.Cells.DialogCell) selectorView).nabdhOwnsCard();
        final boolean nabdhCard = nabdhDialog
                || org.telegram.ui.Components.NabdhGlassRowDecoration.isGlassCard(selectorView);
        if (nabdhCard) {
            final float density = getResources().getDisplayMetrics().density;
            // Dialog cards keep the established swipe geometry; settings
            // selectors follow the same live geometry as their surfaces.
            final boolean classic = NabdhAppearancePrefs.uiStyle() == NabdhAppearancePrefs.UI_CLASSIC;
            final float inset = nabdhDialog
                    ? (classic ? 0 : AndroidUtilities.dp(NabdhCardGeometry.HORIZONTAL_INSET_DP))
                    : (classic ? 0f : 10f) * density;
            final float vertical = nabdhDialog
                    ? (classic ? 0 : AndroidUtilities.dp(NabdhCardGeometry.VERTICAL_INSET_DP))
                    : (classic ? 0f : 2f) * density;
            final float radius = nabdhDialog
                    ? (classic ? 0 : AndroidUtilities.dp(NabdhCardGeometry.CORNER_RADIUS_DP))
                    : NabdhAppearancePrefs.surfaceRadius() * density;
            nabdhDialogSelectorBounds.set(
                    selectorRect.left + inset,
                    selectorRect.top + vertical,
                    selectorRect.right - inset,
                    selectorRect.bottom - vertical);
            nabdhDialogSelectorPath.reset();
            nabdhDialogSelectorPath.addRoundRect(nabdhDialogSelectorBounds,
                    radius, radius, android.graphics.Path.Direction.CW);
            canvas.save();
            canvas.clipPath(nabdhDialogSelectorPath);
        }
"""
s=s.replace(field_anchor,replacement,1)
anchor2 = """        } else {
            selectorDrawable.draw(canvas);
        }
    }

    private boolean ignoreClipChild;"""
if s.count(anchor2)!=1:raise SystemExit("selector end anchor changed")
s=s.replace(anchor2,"""        } else {
            selectorDrawable.draw(canvas);
        }
        if (nabdhCard) {
            canvas.restore();
        }
    }

    private boolean ignoreClipChild;""",1)
p.write_text(s,encoding="utf-8")
print("Rounded selection clip applied only to dialog rows.")
