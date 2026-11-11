#!/usr/bin/env python3
"""Verify cross-screen Glass design contracts before an expensive Android build."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")
bubble = (ROOT / "scripts/apply-glass-bubble-outline.py").read_text(encoding="utf-8")
profile = (ROOT / "scripts/apply-glass-native-settings-profile.py").read_text(encoding="utf-8")
finishing = (ROOT / "scripts/apply-glass-v1-finishing.py").read_text(encoding="utf-8")
settings = (ROOT / "scripts/apply-glass-settings.py").read_text(encoding="utf-8")
login_overlay = (ROOT / "scripts/apply-glass-login-finish.py").read_text(encoding="utf-8")
finishing_ui = finishing

ordered = [
    "apply-glass-global-font.py",
    "apply-glass-chat-typefaces.py",
    "apply-glass-global-textviews.py",
    "apply-glass-settings.py",
    "apply-glass-bubble-radius.py",
    "apply-glass-bubble-outline.py",
    "apply-glass-final-screens.py",
    "apply-glass-v1-finishing.py",
    "apply-glass-settings-surfaces.py",
    "check-glass-overlay.py",
]
positions = [workflow.find("python3 nabdhgram/scripts/" + name) for name in ordered]
assert all(pos >= 0 for pos in positions), "Missing Glass integration step"
assert positions == sorted(positions), "Glass overlays applied out of order"
assert bubble.count("(currentType == TYPE_TEXT || currentType == TYPE_MEDIA)") == 2, "Text/media design is inconsistent"
assert "!themePreview && !isSelected" in bubble, "Selection or preview protection was removed"
assert finishing.count("if ((currentType == TYPE_TEXT || currentType == TYPE_MEDIA) && !themePreview && !isSelected)") == 2, "Final overlay no longer matches text/media anchor"
assert "0x330098A3" not in profile, "Hard-coded profile press color returned"
assert "Theme.key_windowBackgroundWhiteBlueText" in profile, "Theme-aware profile tint missing"
for family in ("Readex Pro", "Vazirmatn", "Noto Sans Arabic", "Tajawal", "Rubik", "Sans-serif", "Serif"):
    assert family in settings, f"Missing English font label: {family}"
assert '"values-ar": ("خط التطبيق", "Readex Pro", "Sans-serif", "Serif"' in settings, "Arabic locale changes font names"
assert "+ 'Device default font'" in settings, "Default font label changes with locale"
assert (chr(92) * 2 + "n            settings.allow_firebase") not in login_overlay, "Double-escaped Java newline in auth overlay"
assert "if (nabdhGlassSettings) {" in finishing_ui and "updateColors(holder);" in finishing_ui, "Settings rows must refresh Glass after native bind"
assert "float renderedStart = offsetX + lineLeft;" in finishing_ui, "RTL badge not anchored to rendered glyphs"
assert "R.drawable.nabdh_keypad_delete" in login_overlay and "nabdh_keypad_delete.xml" in login_overlay, "Native delete vector not bundled"
assert "SIDE_PADDING = 10, BUTTON_PADDING = 6" in login_overlay, "Original keypad geometry not restored"
assert "Theme.key_windowBackgroundWhite" in login_overlay, "Keypad surface must follow theme"
native_surfaces = (ROOT / "scripts/apply-glass-settings-surfaces.py").read_text(encoding="utf-8")
assert all(name in native_surfaces for name in ("NotificationsSettingsActivity.java",
    "PrivacySettingsActivity.java", "DataSettingsActivity.java", "ThemeActivity.java")), "Missing native settings target"
assert "getColor(Theme.key_windowBackgroundWhiteBlueText)" in native_surfaces, "Theme-independent settings border"
assert "onDrawOver" in native_surfaces and "isSettingRow" in native_surfaces, "Settings decoration must exclude non-row views"
global_fonts = (ROOT / "scripts/apply-glass-global-textviews.py").read_text(encoding="utf-8")
assert "final boolean telegramTextFace" in global_fonts, "Telegram-native typefaces excluded from UI scale"
assert "telegramTextFace ? android.graphics.Typeface.DEFAULT" in global_fonts, "Reset may restore saved custom font"
bundled_themes = (ROOT / "scripts/apply-nabdh-bundled-themes.py").read_text(encoding="utf-8")
assert "else if (pathToFile != null)" in bundled_themes, "Theme file null guard missing"
assert "isDark = previewBackgroundColor != 0" in bundled_themes, "Native theme fallback missing"
print("PASS: Glass pipeline order, shared text/media styling, theme colors, and stable font names")
