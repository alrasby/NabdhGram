#!/usr/bin/env python3
"""Round native Telegram settings and profile touch selectors (UI only)."""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-native-settings-profile.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"
changes = [
    ("SettingsActivity.java",
     "        listView.setSections();\n",
     "        listView.setSections();\n        // NabdhGram Glass: rounded touch feedback on native settings rows.\n        listView.setSelectorRadius(17);\n"),
    ("ProfileActivity.java",
     "        listView.setSections();\n        listView.applyPaddingToSections = false;",
     "        listView.setSections();\n        // NabdhGram Glass: rounded profile action selection.\n        listView.setSelectorRadius(17);\n        listView.applyPaddingToSections = false;"),
]
for name, anchor, replacement in changes:
    p = root / name
    source = p.read_text(encoding="utf-8")
    if source.count(anchor) != 1:
        raise SystemExit(f"Unexpected native UI anchor: {name}")
    p.write_text(source.replace(anchor, replacement, 1), encoding="utf-8")
    print(f"Applied rounded native selector: {name}")

# Profile action buttons are painted by a custom View, not a RecyclerView selector.
# Draw one static, rounded press tint under the currently touched action.
actions = root / "Components/ProfileActionsView.java"
source = actions.read_text(encoding="utf-8")
old = "    private final Paint paint = new Paint();"
if source.count(old) != 1:
    raise SystemExit("ProfileActionsView paint anchor changed")
source = source.replace(old, old + """
    private final Paint nabdhPressPaint = new Paint(Paint.ANTI_ALIAS_FLAG);""", 1)
old = "        canvas.clipRect(action.rect);\n\n        updateBounds(action);"
if source.count(old) != 1:
    raise SystemExit("ProfileActionsView action drawing anchor changed")
source = source.replace(old, """        canvas.clipRect(action.rect);
        if (hit == action) {
            nabdhPressPaint.setColor(0x330098A3);
            canvas.drawRoundRect(action.rect, getRoundRadius(), getRoundRadius(), nabdhPressPaint);
        }

        updateBounds(action);""", 1)
old = "                    hit.bounce.setPressed(true);"
if source.count(old) != 1:
    raise SystemExit("ProfileActionsView touch start anchor changed")
source = source.replace(old, old + "\n                    invalidate();", 1)
# Ensure pressed background clears on action completion and drag cancellation.
old = "hit.bounce.setPressed(false);"
if source.count(old) != 2:
    raise SystemExit("ProfileActionsView touch reset anchors changed")
source = source.replace(old, old + "\n                    invalidate();")
actions.write_text(source, encoding="utf-8")
