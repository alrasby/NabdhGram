#!/usr/bin/env python3
"""Apply NabdhGram Glass styling to native Telegram login input surfaces only.

Preserves the upstream authentication state machine, network calls, text listeners,
editability, keyboard handling, CAPTCHA and verification code transitions.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-login.py TELEGRAM_SOURCE")

path = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java"
source = path.read_text(encoding="utf-8")

anchor = "    @Override\n    public View createView(Context context) {"
if source.count(anchor) != 1:
    raise SystemExit("LoginActivity createView anchor changed")
helper = """    // NabdhGram Glass: native Telegram theme keys respect installed .attheme
    // palettes. Backgrounds are decorative only; no focus or click interceptors.
    private static android.graphics.drawable.GradientDrawable nabdhLoginSurface(
            float radiusDp, float tintStrength) {
        int base = Theme.getColor(Theme.key_windowBackgroundWhite);
        int tint = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        int red = Math.round(Color.red(base) * (1f - tintStrength) + Color.red(tint) * tintStrength);
        int green = Math.round(Color.green(base) * (1f - tintStrength) + Color.green(tint) * tintStrength);
        int blue = Math.round(Color.blue(base) * (1f - tintStrength) + Color.blue(tint) * tintStrength);
        android.graphics.drawable.GradientDrawable shape =
                new android.graphics.drawable.GradientDrawable();
        shape.setColor(Color.rgb(red, green, blue));
        shape.setCornerRadius(dp(radiusDp));
        shape.setStroke(dp(1), Color.argb(72, Color.red(tint), Color.green(tint), Color.blue(tint)));
        return shape;
    }

"""
source = source.replace(anchor, helper + anchor, 1)
# A Java annotation must immediately precede the method it annotates.
if "    @Override\n    // NabdhGram Glass:" in source:
    raise SystemExit("Glass helper accidentally inserted after @Override")
if source.count(anchor) != 1:
    raise SystemExit("LoginActivity createView @Override was displaced")

# OutlineTextContainerView retains its native focus outline and labels.
# Do not change edit-text padding, listeners, layout size or auth transitions.
for name in ("countryOutlineView", "phoneOutlineView", "outlineCodeField"):
    needle = f"{name} = new OutlineTextContainerView(context);"
    if source.count(needle) != 1:
        raise SystemExit(f"Unexpected native login field anchor: {name}")
    source = source.replace(needle, needle + f"\n            {name}.setBackground(nabdhLoginSurface(18f, 0.055f));", 1)

# Covers SMS/Telegram app verification, missed call and email code inputs,
# including variants with different native code lengths and custom keyboards.
code_needle = "codeFieldContainer = new CodeFieldContainer(context) {"
if source.count(code_needle) != 4:
    raise SystemExit("Telegram verification field count changed")
# Add a background only when each field is placed into a parent. Applying it
# in the constructor would require fragile brace matching; these four branches
# have stable parent-add anchors.
anchors = (
    "addView(codeFieldContainer, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, 42, Gravity.CENTER_HORIZONTAL, 0, 32, 0, 0));",
    "addView(codeFieldContainer, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, 42, Gravity.CENTER_HORIZONTAL, 0, setup ? 48 : 32, 0, 0));",
)
# Upstream uses the same 42dp layout in both SMS/Telegram code and
# a second login verification flow; the email layout occurs once.
expected_counts = (2, 1)
for needle, expected in zip(anchors, expected_counts):
    count = source.count(needle)
    if count != expected:
        raise SystemExit(f"Login code input layout anchor changed: expected {expected}, found {count}")
    source = source.replace(
        needle,
        "codeFieldContainer.setBackground(nabdhLoginSurface(16f, 0.045f));\n                " + needle,
        expected
    )

path.write_text(source, encoding="utf-8")
print("NabdhGram Glass login phone, password and verification surfaces installed.")
