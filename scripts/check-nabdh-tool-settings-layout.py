#!/usr/bin/env python3
"""Fail-fast contract: new tools use hierarchical native Telegram-style settings.

This checks generated Telegram source and Android resources, not only overlay
templates. A passing source check does not substitute for a phone screenshot.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-tool-settings-layout.py TELEGRAM_SOURCE")

root = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main"
ui = root / "java/org/telegram/ui"
hub = (ui / "NabdhGramSettingsActivity.java").read_text(encoding="utf-8")
category = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
chrome = (ui / "Components/NabdhToolUi.java").read_text(encoding="utf-8")
lock = (ui / "NabdhChatLockActivity.java").read_text(encoding="utf-8")
browser = (ui / "NabdhBrowserActivity.java").read_text(encoding="utf-8")
camera = (ui / "NabdhCameraActivity.java").read_text(encoding="utf-8")
feed = (ui / "NabdhChannelFeedActivity.java").read_text(encoding="utf-8")
ai = (ui / "NabdhAiActivity.java").read_text(encoding="utf-8")

def require(value: bool, reason: str) -> None:
    if not value:
        raise SystemExit("FAIL: " + reason)

require("nabdhExpandedHeader(context, content)" not in hub and
        "nabdhExpandedTools(context, content)" not in hub,
        "tool rows must not clutter main NabdhGram settings")
for section, label in (
    ("NabdhNetworkTitle", "NabdhExpandedBrowser"),
    ("NabdhNetworkTitle", "NabdhExpandedCamera"),
    ("NabdhProductivityTitle", "NabdhExpandedChannelFeed"),
    ("NabdhPrivacyTitle", "NabdhExpandedSwipes"),
    ("NabdhPrivacyTitle", "NabdhChatLockTitle"),
):
    require(f"titleRes == R.string.{section}" in category and
            f"R.string.{label}" in category,
            f"native {section} must link {label}")

require("new org.telegram.ui.ActionBar.AlertDialog.Builder(context)" in category and
        "SharedConfig.updateChatListSwipeSetting(chosen)" in category,
        "swipe dialog must use Telegram theme without changing the native action")
require("NabdhGlassRowDecoration.newCardBackground()" in category and
        "heading.setText(org.telegram.messenger.LocaleController.getString(" in category and
        "title.setText(name)" in category and "details.setText(description)" in category,
        "rows must be themed, translated and have concise title plus subtitle")
require("card.setMinimumHeight(nabdhToolDp(context, 76))" in category and
        "card.setContentDescription(name" in category and
        "card.setFocusable(true)" in category,
        "tool rows need readable touch targets and accessibility text")
require("AndroidUtilities.getTypeface(\"fonts/rmedium.ttf\")" in category,
        "native tool rows must use current Telegram typography family")

for name in ("browser", "camera", "feed", "lock", "swipe"):
    file = root / "res/drawable" / ("nabdh_tool_" + name + ".xml")
    require(file.is_file(), f"missing material icon {name}")
    tree = ET.parse(file)
    require(tree.getroot().tag == "vector" and
            len(list(tree.getroot())) >= 2,
            f"invalid material icon {name}")

xml_ns = "{http://schemas.android.com/apk/res/android}"
for locale, expected in (("values", "More tools"), ("values-ar", "أدوات إضافية")):
    tree = ET.parse(root / "res" / locale / "nabdh_expanded_tools.xml")
    names = {x.attrib.get("name"): x.text for x in tree.getroot()}
    require(names.get("NabdhExpandedTitle") == expected and
            names.get("NabdhExpandedLockInfo") and
            names.get("NabdhExpandedBrowserInfo"),
            f"{locale} titles/subtitles are incomplete")

require("android.view.View.LAYOUT_DIRECTION_RTL" in lock and
        "authorized = false;" in lock, "PIN manager must retain RTL and relock")
for name, code in (("browser", browser), ("camera", camera),
                   ("feed", feed), ("PIN manager", lock), ("AI", ai)):
    require("NabdhToolUi.install(this" in code,
            f"{name} must use the same in-app toolbar and typography")
require("Theme.key_windowBackgroundWhite" in chrome and
        "LocaleController.isRTL" in chrome and
        "fonts/rmedium.ttf" in chrome and
        "activity.onBackPressed()" in chrome,
        "shared toolbar must respect native theme, font, direction and back")
require("page.addView(security);" in browser and
        "page.addView(controls, navParams);" in browser,
        "browser must separate narrow navigation and security controls")
print("PASS: nested category routing, Arabic headings, vector icons, Glass rows, five shared toolbars, readable browser controls")
