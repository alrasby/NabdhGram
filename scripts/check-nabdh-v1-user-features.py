#!/usr/bin/env python3
"""Verify native-generated privacy and SAF controls; fail on phantom AI claims."""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-v1-user-features.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]) / "TMessagesProj/src/main"
ui = root / "java/org/telegram/ui"
page = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
hub = (ui / "NabdhGramSettingsActivity.java").read_text(encoding="utf-8")
for cls in ("NabdhAiPreferenceStore", "NabdhDynamicAccent", "NabdhSettingsBackup"):
    assert (ui / "Components" / (cls + ".java")).is_file(), "missing component " + cls
for snippet in (
    "case 603: return R.string.NabdhHSettingsBackup;",
    "nabdhFeatureRow(context, content, 603);",
    "if (featureId == 603)",
    "requestCode == 6603 || requestCode == 6604",
    "NabdhSettingsBackup.preview(",
    "NabdhSettingsBackup.restore(",
    "NabdhDynamicAccent.enabled(context)",
    "if (featureId == 602)",
    "addNabdhMonetControl(context, content);",
    "NabdhAiPreferenceStore.setRememberEnabled(context, value)",
    "NabdhAiPreferenceStore.clear(context)",
    "NabdhAiPreferenceStore.outputArabic(",
):
    assert snippet in page, "missing generated privacy/user UX: " + snippet
assert hub.count("NabdhDynamicAccent.accent(context,") == 1, "missing native shared accent fallback"
compact = (ui / "Components/NabdhCompactSettings.java").read_text(encoding="utf-8")
assert "icon, accent," in hub and "image.setColorFilter(accent);" in compact and "heading.setTextColor(primary);" in compact, "native Monet accent lost on icons or theme contrast lost on headings"
assert page.count("addNabdhMonetControl(context, content);") == 1, "Monet must have one UI owner"
assert "NabdhAiPrivacyDisclosure" in page, "no explicit local-AI limitation disclosure"
assert "row.setMinimumHeight(dp(context, TextUtils.isEmpty(subtitle) ? 54 : 66))" in compact and "compactGrid" not in hub, "NabdhGram final UI must preserve full-width accessible native rows"
storage = (ui / "Components/NabdhSettingsBackup.java").read_text(encoding="utf-8")
for banned in ("auth_key", "session_id", "password", "token", "userconfing",
               "TelegramUser", "getMessagesController", "getMessagesStorage",
               "getFileLoader", "FileInputStream"):
    assert banned not in storage, "backup code unexpectedly mentions sensitive entry: " + banned
assert "MAX_BYTES = 16384" in storage and "checked(raw)" in storage, "import not bounded and validated"
assert "ACTION_OPEN_DOCUMENT" in storage and "ACTION_CREATE_DOCUMENT" in storage
assert "NabdhAiPreferenceStore.setOutputLanguage" in storage
privacy = (ui / "Components/NabdhAiPreferenceStore.java").read_text(encoding="utf-8")
assert "remember_explicit_feedback" in privacy and 'false)' in privacy
assert "getSharedPreferences" in privacy and "clear().commit()" in privacy
for locale in ("values", "values-ar"):
    f = root / "res" / locale / "nabdh_v1_user_features.xml"
    assert f.is_file(), "missing locale " + locale
    keys = [el.get("name") for el in ET.parse(f).getroot()]
    assert len(keys) == len(set(keys)) and len(keys) >= 15
print("PASS: optional user-only AI preferences, Monet fallback and allowlisted SAF backup")
