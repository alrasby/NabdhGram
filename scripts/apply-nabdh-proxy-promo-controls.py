#!/usr/bin/env python3
"""Expose existing native MTProxy sponsor dismissal as an explicit setting.

No Telegram server deletion, transport modifications or filtering ordinary
channels. The native promoType predicate remains the sole dismissal trigger.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-proxy-promo-controls.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
page = root / "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramFeatureCategoryActivity.java"
source = page.read_text(encoding="utf-8")
def once(before, after, label):
    global source
    count = source.count(before)
    if count != 1: raise SystemExit(f"Proxy promotion {label}: expected one anchor, got {count}")
    source = source.replace(before, after, 1)
once("        fragmentView = scroll;",
     """        if (featureId == 503) {
            addNabdhProxySponsorControl(context, content);
        }
        fragmentView = scroll;""", "show only in Network > Proxy")
once("    private void addPrivacyControls(Context context, LinearLayout content) {",
     """    private void addNabdhProxySponsorControl(Context context, LinearLayout content) {
        android.content.SharedPreferences network = context.getSharedPreferences(
                "nabdhgram_network", Context.MODE_PRIVATE);
        android.widget.Switch toggle = new android.widget.Switch(context);
        toggle.setText(nabdhText(context, R.string.NabdhProxySponsorToggle));
        toggle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        toggle.setPadding(nabdhDp(context, 16), nabdhDp(context, 14),
                          nabdhDp(context, 16), nabdhDp(context, 14));
        toggle.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        toggle.setChecked(network.getBoolean("hide_proxy_sponsors", true));
        toggle.setOnCheckedChangeListener((button, checked) -> {
            network.edit().putBoolean("hide_proxy_sponsors", checked).apply();
        });
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = nabdhDp(context, 12);
        content.addView(toggle, params);
        TextView note = new TextView(context);
        note.setText(nabdhText(context, R.string.NabdhProxySponsorExplanation));
        note.setTag("nabdh:secondary-text");
        note.setTextSize(13);
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        content.addView(note);
    }

    private void addPrivacyControls(Context context, LinearLayout content) {""", "native preference control")
page.write_text(source, encoding="utf-8")
translations = {
    "values": {
        "NabdhProxySponsorToggle": "Hide sponsored MTProxy channel",
        "NabdhProxySponsorExplanation": "On by default. Dismisses only Telegram-classified MTProxy sponsor channels in your chat list via Telegram's native hide action after reloading or returning to chats. This does not remove channels from Telegram servers, and a promotion may reappear."
    },
    "values-ar": {
        "NabdhProxySponsorToggle": "إخفاء قناة رعاية بروكسي MTProxy",
        "NabdhProxySponsorExplanation": "مفعّل افتراضيًا. يُخفي فقط قنوات الرعاية التي يصنفها Telegram لبروكسي MTProxy عند تحديث قائمة المحادثات أو العودة إليها عبر الإجراء الأصلي، ولا يحذف القنوات من خوادم Telegram وقد تظهر مجددًا."
    }
}
for locale, labels in translations.items():
    path = root / "TMessagesProj/src/main/res" / locale / "nabdh_proxy_promo.xml"
    if path.exists(): raise SystemExit("Duplicate proxy promo resources")
    rows = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for name, value in labels.items():
        rows.append('    <string name="' + name + '">' + escape(value).replace("'", "\\'") + '</string>')
    rows.append("</resources>")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
print("PASS: native MTProxy sponsor dismiss preference in Network > Proxy only")
