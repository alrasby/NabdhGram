#!/usr/bin/env python3
"""Fail closed if Telegram notification RTL/family regressions return."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-notification-typography.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
native = root / "TMessagesProj/src/main/java/org/telegram/ui/Cells/NotificationsCheckCell.java"
text = native.read_text(encoding="utf-8")
launch = (root / "TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java").read_text(encoding="utf-8")
assert "valueTextView.setEllipsizeByGradient(false);" in text, "RTL first word can be faded"
assert "valueTextView.setEllipsizeByGradient(true);" not in text, "native RTL gradient still on"
for contract in (
    'textView.setTypeface(AndroidUtilities.getTypeface("fonts/rmedium.ttf"));',
    'valueTextView.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));',
    'multilineValueTextView.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));',
    "textView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG);",
    "checkBox.setChecked(checked, iconType, animationsEnabled);",
    "setMultiline(multiline);",
):
    assert contract in text, "missing native notification behavior: " + contract
assert "nabdhContainsArabic(animated.getText())" in launch, "animated Arabic font fallback missing"
assert "animated.setText(animated.getText(), false);" in launch, "animated layout not rebuilt on font edit"
assert "nabdhRefreshAllFonts()" in launch, "immediate font refresh entrypoint missing"
print("PASS: native NotificationsCheckCell RTL and Arabic typeface regression")
