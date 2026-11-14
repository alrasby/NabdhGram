#!/usr/bin/env python3
"""Pin-scoped UI fixes: clip icon picker, restore chat-list samples, left-side toggles.

Run AFTER apply-glass-remaining-settings.py and the other native overlays.
Every edit checks its exact Telegram 13.2.2 anchor; never patch unknown upstream.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-chat-settings-visual-fixes.py TELEGRAM_SOURCE")
ui = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"


def replace(name, old, new, expected=1):
    path = ui / name
    src = path.read_text(encoding="utf-8")
    actual = src.count(old)
    if actual != expected:
        raise SystemExit(f"{name}: expected {expected} anchors, found {actual}: {old[:100]!r}")
    path.write_text(src.replace(old, new), encoding="utf-8")


# 1. The native icon selector scrolls horizontally inside the inset Glass row.
# Its RecyclerView children were drawn right across that row's rounded border.
# Clip ONLY that one cell to exactly the 10dp/2dp/20dp Glass outline;
# preserve the native item scrolling, selection, hit testing and alias logic.
replace(
    "ThemeActivity.java",
    "                org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(holder.itemView, true);\n"
    "            }\n",
    """                org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(holder.itemView, true);
            }
            if (holder.getItemViewType() == TYPE_APP_ICON) {
                holder.itemView.setOutlineProvider(new android.view.ViewOutlineProvider() {
                    @Override public void getOutline(android.view.View view, android.graphics.Outline outline) {
                        final int insetX = AndroidUtilities.dp(10);
                        final int insetY = AndroidUtilities.dp(2);
                        outline.setRoundRect(insetX, insetY,
                                Math.max(insetX, view.getWidth() - insetX),
                                Math.max(insetY, view.getHeight() - insetY),
                                AndroidUtilities.dp(20));
                    }
                });
                holder.itemView.setClipToOutline(true);
            }
""",
)
# The native 2/3-line samples use nearly transparent switchTrack swatches.
# Their mock avatar/rows disappear over our tinted Glass card. Use the active
# theme foreground (never a hard-coded color), and readable alpha levels.
replace("Cells/ChatListCell.java",
        "            int color = Theme.getColor(Theme.key_switchTrack);",
        "            int color = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText);")
replace("Cells/ChatListCell.java",
        "Color.argb(a == 0 ? 204 : 90, r, g, b)",
        "Color.argb(a == 0 ? 200 : 145, r, g, b)")
replace("Cells/ChatListCell.java",
        "Color.argb(i == 0 ? 204 : 90, r, g, b)",
        "Color.argb(i == 0 ? 210 : 155, r, g, b)")
# Keep both existing radio choices and SharedConfig.setUseThreeLinesLayout.

# 2. Standard native toggle cells: physical LEFT is independent of locale.
# Preserve text gravity (Arabic remains right-aligned, English left-aligned).
# Reserve the left toggle gutter in BOTH locales to prevent English overlap.
replace("Cells/TextCheckCell.java",
        "LocaleController.isRTL ? 70 : padding, 0, LocaleController.isRTL ? padding : 70, 0",
        "70, 0, padding, 0", 2)
replace("Cells/TextCheckCell.java",
        "LocaleController.isRTL ? 70 : padding, 35, LocaleController.isRTL ? padding : 70, 0",
        "70, 35, padding, 0")
replace("Cells/TextCheckCell.java",
        "LocaleController.isRTL ? 64 : padding, 36, LocaleController.isRTL ? padding : 64, 0",
        "70, 36, padding, 0")
replace("Cells/TextCheckCell.java",
        "(LocaleController.isRTL ? Gravity.LEFT : Gravity.RIGHT) | Gravity.CENTER_VERTICAL, 22, 0, 22, 0",
        "Gravity.LEFT | Gravity.CENTER_VERTICAL, 22, 0, 22, 0", 2)

replace("Cells/TextCheckCell2.java",
        "LocaleController.isRTL ? Gravity.LEFT : Gravity.RIGHT));",
        "Gravity.LEFT));")
replace("Cells/TextCheckCell2.java",
        "(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT) | Gravity.TOP, LocaleController.isRTL ? 64 : 21,",
        "(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT) | Gravity.TOP, 64,", 2)
replace("Cells/TextCheckCell2.java",
        "LocaleController.isRTL ? 21 : 64, 0",
        "21, 0", 2)
replace("Cells/TextCheckCell2.java",
        "(LocaleController.isRTL ? Gravity.LEFT : Gravity.RIGHT) | Gravity.CENTER_VERTICAL, 22, 0, 22, 0",
        "Gravity.LEFT | Gravity.CENTER_VERTICAL, 22, 0, 22, 0")
# Expanded-switch arrow was laid at the same left edge as its RTL/LTR toggle.
# With the fixed-left switch, put this optional disclosure control at the RIGHT.
replace("Cells/TextCheckCell2.java",
        "LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_VERTICAL));",
        "LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_VERTICAL | Gravity.RIGHT));")

replace("Cells/NotificationsCheckCell.java",
        "(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT) | Gravity.CENTER_VERTICAL, 8, 0, 8, 0",
        "Gravity.RIGHT | Gravity.CENTER_VERTICAL, 8, 0, 8, 0")
replace("Cells/NotificationsCheckCell.java",
        "LocaleController.isRTL ? 80 : (withImage ? 64 : padding),",
        "80,", 3)
replace("Cells/NotificationsCheckCell.java",
        "LocaleController.isRTL ? (withImage ? 64 : padding) : 80,",
        "(withImage ? 64 : padding),", 3)
replace("Cells/NotificationsCheckCell.java",
        "(LocaleController.isRTL ? Gravity.LEFT : Gravity.RIGHT) | Gravity.CENTER_VERTICAL, 21, 0, 21, 0",
        "Gravity.LEFT | Gravity.CENTER_VERTICAL, 21, 0, 21, 0")

# 3. Power Saver has its own custom SwitchCell, plus a special split
# click zone for rows with expandable sub-options. Move BOTH the switch
# and the hit-zone calculation without changing any LiteMode flags.
replace("LiteModeSettingsActivity.java",
        "(LocaleController.isRTL ? x > dp(19 + 37 + 19) : x < view.getMeasuredWidth() - dp(19 + 37 + 19))",
        "x > dp(19 + 37 + 19)")
replace("LiteModeSettingsActivity.java",
        "(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT), 20, 0, 20, 0",
        "Gravity.RIGHT, 20, 0, 20, 0")
replace("LiteModeSettingsActivity.java",
        "Gravity.CENTER_VERTICAL | (LocaleController.isRTL ? Gravity.LEFT : Gravity.RIGHT), 19, 0, 19, 0",
        "Gravity.CENTER_VERTICAL | Gravity.LEFT, 19, 0, 19, 0")
replace("LiteModeSettingsActivity.java",
        "Gravity.CENTER_VERTICAL | (LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT), 64, 0, 8, 0",
        "Gravity.CENTER_VERTICAL | (LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT), 64, 0, LocaleController.isRTL ? 8 : 64, 0")
replace("LiteModeSettingsActivity.java",
        "AndroidUtilities.dp(item.viewType == VIEW_TYPE_SWITCH ? (LocaleController.isRTL ? 64 : 75) + 4 : 8)",
        "AndroidUtilities.dp(item.viewType == VIEW_TYPE_SWITCH ? 68 : 8)")

print("PASS: app icons clipped, chat-list previews visible, and major native switches fixed left")
