#!/usr/bin/env python3
"""Fail-closed contracts for physical-position split-action switch targets."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-toggle-hitboxes.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"
helper = (root / "Components/NabdhToggleHitbox.java").read_text(encoding="utf-8")
required = ("getCheckBox()", "thumb.getX()", "thumb.getWidth() / 2f",
            "Math.abs(touchX - centerX)", "AndroidUtilities.dp(38)")
for token in required:
    if token not in helper:
        raise SystemExit("Missing actual rendered switch hitbox: " + token)
cases = {
    "DataSettingsActivity.java": 1,
    "NotificationsSettingsActivity.java": 1,
    "ThemeActivity.java": 2,
}
for name, count in cases.items():
    text = (root / name).read_text(encoding="utf-8")
    if text.count("NabdhToggleHitbox.isToggleTap(view, x)") != count:
        raise SystemExit(f"{name}: incorrect physical hitbox count")
    if name == "DataSettingsActivity.java" and text.count("if (nabdhToggleHit)") != 2:
        raise SystemExit("Data Settings must retain exactly two shared toggle branches")
    if "LocaleController.isRTL && x <= dp(76)" in text or (
        "LocaleController.isRTL && x <= AndroidUtilities.dp(76)" in text
    ):
        raise SystemExit(f"{name}: legacy RTL side-assumption survived")
text = (root / "Cells/TextCheckCell2.java").read_text(encoding="utf-8")
for token in ("checkBoxClickArea != null", "checkBox.getX() + checkBox.getWidth() / 2f",
              "checkBoxClickArea.setTranslationX(desiredLeft - checkBoxClickArea.getLeft())"):
    if token not in text:
        raise SystemExit("TextCheckCell2 split touch area not aligned: " + token)
print("PASS: physical-toggle touch targets across Data, Notifications, Theme, Web Browser and expandable check cells")
