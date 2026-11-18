#!/usr/bin/env python3
"""Regression: only Telegram-marked MTProxy sponsorship may be dismissed."""
from pathlib import Path
import xml.etree.ElementTree as ET
import sys

def verify(root):
    ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
    dialogs = (ui / "DialogsActivity.java").read_text(encoding="utf-8")
    feature = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
    for symbol in (
        "MessagesController.PROMO_TYPE_PROXY", "controller.isPromoDialog(candidate.id, false)",
        "controller.hidePromoDialog();", "nabdhLastProxyPromoAttemptAt",
        'getBoolean("hide_proxy_sponsors", true)', "nabdhHideProxySponsorIfPresent();",
    ):
        if symbol not in dialogs: raise ValueError("Native MTProxy-only hide contract missing: " + symbol)
    for symbol in (
        "if (featureId == 503)", "addNabdhProxySponsorControl(context, content);",
        "addNabdhProxySponsorControl(Context context, LinearLayout content)",
        'network.getBoolean("hide_proxy_sponsors", true)',
        'network.edit().putBoolean("hide_proxy_sponsors", checked).apply()',
    ):
        if symbol not in feature: raise ValueError("Visible proxy preference missing: " + symbol)
    if feature.count("addNabdhProxySponsorControl(context, content);") != 1:
        raise ValueError("Duplicate proxy sponsor toggle")
    # Restrict this check to the injected helper: native DialogsActivity
    # legitimately contains ordinary delete-chat actions elsewhere.
    helper_start = dialogs.find("private void nabdhHideProxySponsorIfPresent()")
    helper_end = dialogs.find("    @Override\n    public void onResume()", helper_start)
    if helper_start < 0 or helper_end <= helper_start:
        raise ValueError("Cannot isolate native proxy sponsor helper")
    helper = dialogs[helper_start:helper_end]
    if "deleteDialog" in helper or "deleteMessages" in helper:
        raise ValueError("Promo helper must not delete user chats or messages")
    for locale in ("values", "values-ar"):
        xml = root / "TMessagesProj/src/main/res" / locale / "nabdh_proxy_promo.xml"
        keys = {x.attrib.get("name") for x in ET.parse(xml).getroot()}
        if keys != {"NabdhProxySponsorToggle", "NabdhProxySponsorExplanation"}:
            raise ValueError("Missing exact localized MTProxy options")
    print("PASS: default-on native MTProxy-only dismissal and visible Network toggle")

if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("Usage: check-nabdh-proxy-promo-controls.py TELEGRAM_SOURCE")
    verify(Path(sys.argv[1]))
