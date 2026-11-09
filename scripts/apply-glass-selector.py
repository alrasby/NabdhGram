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
        final boolean nabdhDialog = selectorView instanceof org.telegram.ui.Cells.DialogCell;
        if (nabdhDialog) {
            final float density = getResources().getDisplayMetrics().density;
            nabdhDialogSelectorBounds.set(
                    selectorRect.left + 7f * density,
                    selectorRect.top + 3f * density,
                    selectorRect.right - 7f * density,
                    selectorRect.bottom - 3f * density);
            nabdhDialogSelectorPath.reset();
            nabdhDialogSelectorPath.addRoundRect(nabdhDialogSelectorBounds,
                    17f * density, 17f * density, android.graphics.Path.Direction.CW);
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
        if (nabdhDialog) {
            canvas.restore();
        }
    }

    private boolean ignoreClipChild;""",1)
p.write_text(s,encoding="utf-8")
print("Rounded selection clip applied only to dialog rows.")
