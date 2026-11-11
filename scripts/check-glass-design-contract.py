#!/usr/bin/env python3
"""Verify cross-screen Glass design contracts before an expensive Android build."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")
bubble = (ROOT / "scripts/apply-glass-bubble-outline.py").read_text(encoding="utf-8")
profile = (ROOT / "scripts/apply-glass-native-settings-profile.py").read_text(encoding="utf-8")
settings = (ROOT / "scripts/apply-glass-settings.py").read_text(encoding="utf-8")

ordered = [
    "apply-glass-global-font.py",
    "apply-glass-chat-typefaces.py",
    "apply-glass-global-textviews.py",
    "apply-glass-settings.py",
    "apply-glass-bubble-radius.py",
    "apply-glass-bubble-outline.py",
    "apply-glass-final-screens.py",
    "apply-glass-v1-finishing.py",
    "check-glass-overlay.py",
]
positions = [workflow.find("python3 nabdhgram/scripts/" + name) for name in ordered]
assert all(pos >= 0 for pos in positions), "Missing Glass integration step"
assert positions == sorted(positions), "Glass overlays applied out of order"
assert bubble.count("(currentType == TYPE_TEXT || currentType == TYPE_MEDIA)") == 2, "Text/media design is inconsistent"
assert "!themePreview && !isSelected" in bubble, "Selection or preview protection was removed"
assert "0x330098A3" not in profile, "Hard-coded profile press color returned"
assert "Theme.key_windowBackgroundWhiteBlueText" in profile, "Theme-aware profile tint missing"
for family in ("Readex Pro", "Vazirmatn", "Noto Sans Arabic", "Tajawal", "Rubik", "Sans-serif", "Serif"):
    assert family in settings, f"Missing English font label: {family}"
assert '"values-ar": ("خط التطبيق", "Readex Pro", "Sans-serif", "Serif"' in settings, "Arabic locale changes font names"
assert "+ 'Device default font'" in settings, "Default font label changes with locale"
print("PASS: Glass pipeline order, shared text/media styling, theme colors, and stable font names")
