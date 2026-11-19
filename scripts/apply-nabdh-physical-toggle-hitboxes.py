#!/usr/bin/env python3
"""Match split-action settings toggle touch zones to their actual switch views.

Telegram's split-action rows use a language-dependent 76dp hit test, but
NabdhGram's RTL/device layouts can put the visual switch on the other edge.
Never change the switch ON/OFF state, save handler or whole-row navigation.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-physical-toggle-hitboxes.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
components = ui / "Components"
helper = components / "NabdhToggleHitbox.java"
if helper.exists():
    raise SystemExit("NabdhToggleHitbox already exists")
helper.write_text("""package org.telegram.ui.Components;

import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.Cells.NotificationsCheckCell;

/**
 * Common physical-hit test for Telegram's split-action settings rows.
 * Uses the rendered switch's coordinates, independent of app/device RTL.
 */
public final class NabdhToggleHitbox {
    private NabdhToggleHitbox() {}

    public static boolean isToggleTap(View row, float touchX) {
        if (!(row instanceof NotificationsCheckCell)) return false;
        View thumb = ((NotificationsCheckCell) row).getCheckBox();
        if (thumb == null || thumb.getWidth() <= 0 || row.getWidth() <= 0) return false;
        // Keep Telegram's generous 76dp toggle target but center it over
        // the real control rather than over an assumed RTL/LTR edge.
        float centerX = thumb.getX() + thumb.getWidth() / 2f;
        float radius = AndroidUtilities.dp(38);
        return Math.abs(touchX - centerX) <= radius;
    }
}
""", encoding="utf-8")

data = ui / "DataSettingsActivity.java"
s = data.read_text(encoding="utf-8")
existing = """            boolean nabdhToggleHit = false;
            if (view instanceof NotificationsCheckCell) {
                View toggleView = ((NotificationsCheckCell) view).getCheckBox();
                float center = toggleView.getX() + toggleView.getWidth() / 2f;
                nabdhToggleHit = Math.abs(x - center) <= AndroidUtilities.dp(48);
            }"""
new = """            boolean nabdhToggleHit =
                    org.telegram.ui.Components.NabdhToggleHitbox.isToggleTap(view, x);"""
if s.count(existing) != 1 or s.count("if (nabdhToggleHit)") != 2:
    raise SystemExit("Nabdh data split-action click handling drift")
data.write_text(s.replace(existing, new, 1), encoding="utf-8")

for filename, count in (("NotificationsSettingsActivity.java", 1), ("ThemeActivity.java", 2)):
    file = ui / filename
    s = file.read_text(encoding="utf-8")
    expr = ("LocaleController.isRTL && x <= dp(76) || "
            "!LocaleController.isRTL && x >= view.getMeasuredWidth() - dp(76)")
    if s.count(expr) != count:
        raise SystemExit(f"{filename}: expected {count} native hit test(s), got {s.count(expr)}")
    s = s.replace(expr, "org.telegram.ui.Components.NabdhToggleHitbox.isToggleTap(view, x)")
    file.write_text(s, encoding="utf-8")

# TextCheckCell2's explicit 76dp clickable overlay must remain over the
# actual switch rather than the opposite language edge.
cell = ui / "Cells/TextCheckCell2.java"
s = cell.read_text(encoding="utf-8")
anchor = """        super.onLayout(changed, left, top, right, bottom);
        if (collapseViewContainer != null) {"""
replacement = """        super.onLayout(changed, left, top, right, bottom);
        if (checkBoxClickArea != null && checkBox.getWidth() > 0) {
            float desiredLeft = checkBox.getX() + checkBox.getWidth() / 2f
                    - checkBoxClickArea.getWidth() / 2f;
            checkBoxClickArea.setTranslationX(desiredLeft - checkBoxClickArea.getLeft());
        }
        if (collapseViewContainer != null) {"""
if s.count(anchor) != 1:
    raise SystemExit("TextCheckCell2 onLayout native anchor changed")
cell.write_text(s.replace(anchor, replacement, 1), encoding="utf-8")
print("PASS: split-action toggle taps follow physical switch for Data/Notifications/Theme/TextCheckCell2")
