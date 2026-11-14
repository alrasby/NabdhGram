#!/usr/bin/env python3
"""Telegram 13.2.2: switch ON thumb stays at physical LEFT in every locale.

This adjusts only the thumb's X coordinate. The native progress animation,
check state, tap handling, colors, ripple, icon and accessibility are untouched.
Run after all other NabdhGram overlays and before the Java source/API guard.
"""
from pathlib import Path
import sys

ORIGINAL = "        int tx = x + AndroidUtilities.dp(7) + (int) (AndroidUtilities.dp(17) * progress);"
REPLACEMENT = (
    "        // NabdhGram: ON thumb is physically left in Arabic and English.\n"
    "        // Preserve the logical progress (0 = off, 1 = on) for animation,\n"
    "        // checked colors, callbacks, icons and accessibility.\n"
    "        int tx = x + AndroidUtilities.dp(7) + (int) (AndroidUtilities.dp(17) * (1.0f - progress));"
)
MARKER = "NabdhGram: ON thumb is physically left in Arabic and English."
EXPECTED_STATE = "setProgress(checked ? 1.0f : 0.0f);"
EXPECTED_ANIM = 'ObjectAnimator.ofFloat(this, "progress", newCheckedState ? 1 : 0)'
EXPECTED_RIPPLE = "rippleDrawable.setBounds(tx - AndroidUtilities.dp(18), ty - AndroidUtilities.dp(18), tx + AndroidUtilities.dp(18), ty + AndroidUtilities.dp(18));"


def assert_contract(text, modified):
    needle = REPLACEMENT if modified else ORIGINAL
    if text.count(needle) != 1:
        raise AssertionError("switch thumb X anchor is missing or duplicated")
    for anchor in (EXPECTED_STATE, EXPECTED_ANIM, EXPECTED_RIPPLE):
        if text.count(anchor) != 1:
            raise AssertionError("native switch state/animation/ripple contract changed: " + anchor)
    if modified and ORIGINAL in text:
        raise AssertionError("the original right-on thumb formula is still present")
    if modified and text.count(MARKER) != 1:
        raise AssertionError("NabdhGram thumb inversion marker is missing")


def thumb_x(x, dp7, dp17, progress):
    return x + dp7 + int(dp17 * (1.0 - progress))


def self_test():
    # Physical-LTR coordinates must remain identical in AR and EN, including
    # intermediate animation frames, and without reversing logical state.
    for lang in ("ar", "en"):
        left = thumb_x(3, 7, 17, 1.0)
        middle = thumb_x(3, 7, 17, .5)
        right = thumb_x(3, 7, 17, 0.0)
        assert left == 10 and middle == 18 and right == 27, lang
        assert left < middle < right, lang
    original = "\n".join((ORIGINAL, EXPECTED_STATE, EXPECTED_ANIM, EXPECTED_RIPPLE))
    assert_contract(original, False)
    changed = original.replace(ORIGINAL, REPLACEMENT)
    assert_contract(changed, True)
    print("PASS: thumb ON-left / OFF-right and original logical state preserved")


def main(argv):
    if argv == ["--self-test"]:
        self_test()
        return
    if len(argv) != 2 or argv[0] not in ("--apply", "--verify"):
        raise SystemExit("Usage: apply-fixed-left-toggle-thumb.py --self-test | --apply TELEGRAM_SOURCE | --verify TELEGRAM_SOURCE")
    path = Path(argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/Components/Switch.java"
    text = path.read_text(encoding="utf-8")
    if argv[0] == "--apply":
        assert_contract(text, False)
        path.write_text(text.replace(ORIGINAL, REPLACEMENT, 1), encoding="utf-8")
        assert_contract(path.read_text(encoding="utf-8"), True)
    else:
        assert_contract(text, True)
    print("PASS: physical-left ON thumb in native Telegram Switch; state/animations unchanged")


if __name__ == "__main__":
    main(sys.argv[1:])
