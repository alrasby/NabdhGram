#!/usr/bin/env python3
"""Regression gate for truly grouped, native-locale NabdhGram settings."""
from pathlib import Path
import xml.etree.ElementTree as ET
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-compact-settings.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main"
ui = root / "java/org/telegram/ui"
hub = (ui / "NabdhGramSettingsActivity.java").read_text(encoding="utf-8")
page = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
renderer = (ui / "Components/NabdhCompactSettings.java").read_text(encoding="utf-8")
def check(ok, reason):
    if not ok: raise SystemExit("FAIL: compact UI " + reason)

check(hub.count("section(context, content, R.string.") == 7,
      "native seven category source routes were lost")
check("NabdhCompactSettings.row(context, parent" in hub and
      "NabdhDynamicAccent.accent(" in hub and
      "NabdhStrings.get(context, titleRes)" in hub,
      "main settings lost native grouped cards / Monet / app language")
route_checks = {
    "grouped_renderer": "NabdhCompactSettings.row(" in page,
    "browser": "NabdhExpandedBrowser" in page,
    "channel_feed": "NabdhExpandedChannelFeed" in page,
    "chat_lock": "NabdhChatLockTitle" in page,
    "locale": "NabdhStrings.get(context, label)" in page,
}
check(all(route_checks.values()),
      "grouped tool route missing: " + repr(route_checks))
check("if (titleRes == R.string.NabdhAppearanceTitle) return;" in hub and
      "R.string.NabdhCompactStyleLanguageTitle" in hub and
      "nabdhFeatureRow(context, content, 601);" in page and
      "nabdhFeatureRow(context, content, 602);" in page and
      "nabdhFeatureRow(context, content, 603);" in page,
      "Appearance and Language must share one visible category without losing fonts, themes or backup")
check("nabdhExpandedButton(context, content, R.string.NabdhExpandedSwipes" not in page,
      "duplicate Swipe Actions option must not be shown in NabdhGram settings")
check(page.count("NabdhToolUi.styleToggle(context, ") >= 6 and
      "NabdhToolUi.styleInput(context, " in page,
      "custom native switches and input fields must share Telegram theme")
check("choices.setVisibility(View.GONE);" in page and
      "choices.setOnCheckedChangeListener(" in page and
      "fontTitle.setOnClickListener(" in page and
      'prefs.edit().putString("font_family", family).commit();' in page,
      "font selector must collapse without losing the existing persisted option action")
check("LocaleController.getString(R.string.NabdhExpandedTitle)" not in page and
      "LocaleController.getString(label)" not in page,
      "custom Android resources must not go through Telegram's string registry")
check("content.addView(explanation);" in page and
      "explanation.setBackground(null);" in page and
      "explanation.setTextSize(12);" in page,
      "category intro is still a large saturated card")
check('GROUP_TAG = "nabdh:compact-setting-group:v1"' in renderer and
      "group.setClipToOutline(true)" in renderer and
      "new RippleDrawable(" in renderer and
      "ColorStateList.valueOf(" in renderer and
      "setMinimumHeight(dp(context" in renderer and
      "TextUtils.isEmpty(subtitle)" in renderer and
      "LocaleController.isRTL" in renderer,
      "surface must group, clip touch feedback, adapt, and keep legible touch targets")
check("getTypeface(\"fonts/rmedium.ttf\")" in renderer,
      "selected Telegram typography bridge lost")
check("getCurrentLocale()" in (ui / "NabdhStrings.java").read_text(),
      "must respect Telegram language independent of Android device locale")
for lang in ("values", "values-ar"):
    res = root / "res" / lang / "nabdh_compact_settings.xml"
    check(res.is_file(), "missing " + lang + " summaries")
    nodes = list(ET.parse(res).getroot())
    keys = [n.get("name") for n in nodes]
    check(len(keys) == 9 and len(set(keys)) == 9 and
          all((n.text or "").strip() for n in nodes),
          "incomplete " + lang + " summaries")
check("markDialogAsRead(" not in renderer and
      "MessagesController" not in renderer and
      "NabdhAiCoreService" not in renderer,
      "renderer must not touch Telegram or AI logic")
print("PASS: six visible grouped settings categories with merged Appearance/Language, original tool routes, no duplicate Swipe Actions")
