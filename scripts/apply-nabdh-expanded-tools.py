#!/usr/bin/env python3
"""Install opt-in Camera2, Browser and Channel Feed as isolated native Activities.

Pinned 13.2.2 source overlays only. No Telegram chat transport, login, call or
message-read handlers are replaced. These activities are explicitly launched
from NabdhGram Settings and cannot be started by other Android apps.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-expanded-tools.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
source = Path(__file__).resolve().parents[1] / "overlay/java"
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"

def exact(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expanded tools {label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)

for name in ("NabdhBrowserActivity.java", "NabdhCameraActivity.java",
             "NabdhChannelFeedActivity.java"):
    target = ui / name
    if target.exists():
        raise SystemExit("Expanded tools: refusing to overwrite " + str(target))
    target.write_bytes((source / name).read_bytes())

manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
marker = "        <!-- usesCleartextTraffic for browser supporting opening http:// links -->"
activities = """        <!-- NabdhGram user-launched tools; never exported or reachable by implicit intents -->
        <activity android:name="org.telegram.ui.NabdhBrowserActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
        <activity android:name="org.telegram.ui.NabdhCameraActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
        <activity android:name="org.telegram.ui.NabdhChannelFeedActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
"""
m = exact(m, marker, marker + "\n" + activities, "private activity manifest")
manifest.write_text(m, encoding="utf-8")

hub = ui / "NabdhGramSettingsActivity.java"
h = hub.read_text(encoding="utf-8")
h = exact(h, "        fragmentView = scroll;",
    """        nabdhExpandedTools(context, content);
        fragmentView = scroll;""", "settings entry")
method = """    private void nabdhExpandedTools(Context context, LinearLayout parent) {
        TextView heading = new TextView(context);
        heading.setText(context.getString(R.string.NabdhExpandedTitle));
        heading.setTextSize(18);
        heading.setPadding(0, 18, 0, 12);
        heading.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        parent.addView(heading);
        nabdhExpandedButton(context, parent, R.string.NabdhExpandedBrowser,
                () -> context.startActivity(new android.content.Intent(
                        context, NabdhBrowserActivity.class)));
        nabdhExpandedButton(context, parent, R.string.NabdhExpandedCamera,
                () -> context.startActivity(new android.content.Intent(
                        context, NabdhCameraActivity.class)));
        nabdhExpandedButton(context, parent, R.string.NabdhExpandedChannelFeed,
                () -> context.startActivity(new android.content.Intent(
                        context, NabdhChannelFeedActivity.class)));
    }

    private void nabdhExpandedButton(Context context, LinearLayout parent,
                                     int label, Runnable action) {
        TextView card = new TextView(context);
        card.setText(context.getString(label));
        card.setTextSize(16);
        card.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        int d = (int) (16 * context.getResources().getDisplayMetrics().density);
        card.setPadding(d, d, d, d);
        card.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        card.setClickable(true);
        card.setFocusable(true);
        card.setOnClickListener(view -> action.run());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.bottomMargin = d / 2;
        parent.addView(card, params);
    }

"""
h = exact(h,
    "    private void section(Context context, LinearLayout parent, int titleRes, int descriptionRes) {",
    method + "    private void section(Context context, LinearLayout parent, int titleRes, int descriptionRes) {",
    "tools methods")
hub.write_text(h, encoding="utf-8")

labels = {
    "values": {
        "NabdhExpandedTitle": "NabdhGram tools",
        "NabdhExpandedBrowser": "Internal browser · tracking protection",
        "NabdhExpandedCamera": "Advanced Camera2 · photo controls",
        "NabdhExpandedChannelFeed": "Channel Feed · recent cached posts / swipe",
    },
    "values-ar": {
        "NabdhExpandedTitle": "أدوات نبض جرام",
        "NabdhExpandedBrowser": "المتصفح الداخلي وحماية التتبع",
        "NabdhExpandedCamera": "كاميرا Camera2 المتقدمة",
        "NabdhExpandedChannelFeed": "منشورات القنوات والسحب",
    },
}
for locale, pairs in labels.items():
    dest = root / "TMessagesProj/src/main/res" / locale / "nabdh_expanded_tools.xml"
    if dest.exists():
        raise SystemExit("Expanded tools resource collision")
    rows = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for key, value in pairs.items():
        rows.append('    <string name="' + key + '">' +
                    escape(value).replace("'", "\\'") + '</string>')
    rows.append('</resources>')
    dest.write_text("\n".join(rows) + "\n", encoding="utf-8")

print("PASS: private Camera2/Browser/ChannelFeed activities and working Settings launchers")
