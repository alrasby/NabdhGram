#!/usr/bin/env python3
"""V1 visibility policy: hide nonfunctional rows without deleting code/resources.

Never alters Telegram's original feature implementations, message paths or
persisted account state. Re-enable after acceptance tests in a later version.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-feature-visibility.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
source = Path(__file__).resolve().parents[1] / "overlay/java/NabdhFeatureGates.java"
target = ui / "Components/NabdhFeatureGates.java"
if target.exists():
    raise SystemExit("Feature gates collision")
target.write_bytes(source.read_bytes())
page = ui / "NabdhGramFeatureCategoryActivity.java"
s = page.read_text(encoding="utf-8")

def change(before, after, name):
    global s
    n = s.count(before)
    if n != 1:
        raise SystemExit(f"Feature visibility: {name} anchor changed ({n})")
    s = s.replace(before, after, 1)

for feature in (203, 401):
    before = f"            nabdhFeatureRow(context, content, {feature});"
    after = (f"            if (org.telegram.ui.Components.NabdhFeatureGates.visible({feature})) "
             f"nabdhFeatureRow(context, content, {feature});")
    change(before, after, f"placeholder feature {feature}")

chat = """            nabdhV1Button(context, content, R.string.NabdhAiChatLaunch,
                () -> context.startActivity(new android.content.Intent(
                        context, NabdhAiChatActivity.class)));"""
withgate = """            if (org.telegram.ui.Components.NabdhFeatureGates.verifiedAiChat(context)) {
                nabdhV1Button(context, content, R.string.NabdhAiChatLaunch,
                    () -> context.startActivity(new android.content.Intent(
                            context, NabdhAiChatActivity.class)));
            }"""
change(chat, withgate, "AI Chat release gate")
page.write_text(s, encoding="utf-8")
print("PASS: hidden inactive V1 options; retained their source and future activation routes")
