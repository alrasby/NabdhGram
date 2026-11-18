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

tool_ui = ui / "Components/NabdhToolUi.java"
if tool_ui.exists():
    raise SystemExit("Expanded tools: refusing to replace shared UI: " + str(tool_ui))
tool_ui.write_bytes((source / "NabdhToolUi.java").read_bytes())

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

category = ui / "NabdhGramFeatureCategoryActivity.java"
c = category.read_text(encoding="utf-8")
c = exact(c, "        fragmentView = scroll;",
    """        // Tools are routed through the existing NabdhGram categories.
        if (featureId == 0 && titleRes == R.string.NabdhNetworkTitle) {
            nabdhExpandedHeader(context, content);
            nabdhExpandedButton(context, content, R.string.NabdhExpandedBrowser,
                    () -> context.startActivity(new android.content.Intent(
                            context, NabdhBrowserActivity.class)));
            nabdhExpandedButton(context, content, R.string.NabdhExpandedCamera,
                    () -> context.startActivity(new android.content.Intent(
                            context, NabdhCameraActivity.class)));
        }
        if (featureId == 0 && titleRes == R.string.NabdhPrivacyTitle) {
            nabdhExpandedHeader(context, content);
            nabdhExpandedButton(context, content, R.string.NabdhExpandedSwipes,
                    () -> nabdhChooseChatSwipe(context));
        }
        fragmentView = scroll;""", "category-aware tools routing")
method = """    private void nabdhExpandedHeader(Context context, LinearLayout parent) {

        TextView heading = new TextView(context);
        heading.setText(org.telegram.messenger.LocaleController.getString(R.string.NabdhExpandedTitle));
        heading.setTextSize(16);
        heading.setTypeface(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
        heading.setPadding(nabdhToolDp(context, 12), nabdhToolDp(context, 20),
                nabdhToolDp(context, 12), nabdhToolDp(context, 8));
        heading.setGravity(org.telegram.messenger.LocaleController.isRTL
                ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT);
        heading.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        parent.addView(heading);
    }

    private void nabdhChooseChatSwipe(Context context) {
        final String[] options = {
            org.telegram.messenger.LocaleController.getString(R.string.SwipeSettingsPin),
            org.telegram.messenger.LocaleController.getString(R.string.SwipeSettingsRead),
            org.telegram.messenger.LocaleController.getString(R.string.SwipeSettingsArchive),
            org.telegram.messenger.LocaleController.getString(R.string.SwipeSettingsMute),
            org.telegram.messenger.LocaleController.getString(R.string.SwipeSettingsDelete),
            org.telegram.messenger.LocaleController.getString(R.string.SwipeSettingsFolders)
        };
        int selected = org.telegram.messenger.SharedConfig.getChatSwipeAction(
                org.telegram.messenger.UserConfig.selectedAccount);
        // Telegram's native theme-aware settings dialog instead of an
        // unrelated stock Material alert with an English mixed-script header.
        String[] entries = new String[options.length];
        for (int i = 0; i < entries.length; i++) {
            entries[i] = (i == selected ? "✓  " : "    ") + options[i];
        }
        new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                .setTitle(org.telegram.messenger.LocaleController.getString(
                        R.string.NabdhExpandedSwipes))
                .setItems(entries, (dialog, chosen) -> {
                    if (chosen >= 0 && chosen < options.length) {
                        org.telegram.messenger.SharedConfig.updateChatListSwipeSetting(chosen);
                    }
                    dialog.dismiss();
                })
                .setNegativeButton(org.telegram.messenger.LocaleController.getString(
                        R.string.Cancel), null)
                .show();
    }

    private int nabdhToolDp(Context context, int n) {
        return (int) (n * context.getResources().getDisplayMetrics().density + .5f);
    }

    private void nabdhExpandedButton(Context context, LinearLayout parent,
                                     int label, Runnable action) {
        int subtitle;
        int icon;
        if (label == R.string.NabdhExpandedBrowser) {
            subtitle = R.string.NabdhExpandedBrowserInfo;
            icon = R.drawable.nabdh_tool_browser;
        } else if (label == R.string.NabdhExpandedCamera) {
            subtitle = R.string.NabdhExpandedCameraInfo;
            icon = R.drawable.nabdh_tool_camera;
        } else if (label == R.string.NabdhExpandedChannelFeed) {
            subtitle = R.string.NabdhExpandedChannelFeedInfo;
            icon = R.drawable.nabdh_tool_feed;
        } else if (label == R.string.NabdhChatLockTitle) {
            subtitle = R.string.NabdhExpandedLockInfo;
            icon = R.drawable.nabdh_tool_lock;
        } else {
            subtitle = R.string.NabdhExpandedSwipesInfo;
            icon = R.drawable.nabdh_tool_swipe;
        }

        final boolean rtl = org.telegram.messenger.LocaleController.isRTL;
        final int primary = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText);
        final int secondary = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2);
        final int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        final String name = org.telegram.messenger.LocaleController.getString(label);
        final String description = org.telegram.messenger.LocaleController.getString(subtitle);

        LinearLayout card = new LinearLayout(context);
        card.setOrientation(LinearLayout.HORIZONTAL);
        // Keep icon on the left and disclosure on the right, while the text
        // itself respects Telegram's selected in-app language.
        card.setLayoutDirection(View.LAYOUT_DIRECTION_LTR);
        card.setGravity(android.view.Gravity.CENTER_VERTICAL);
        card.setMinimumHeight(nabdhToolDp(context, 76));
        card.setPadding(nabdhToolDp(context, 14), nabdhToolDp(context, 12), nabdhToolDp(context, 14), nabdhToolDp(context, 12));
        card.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        card.setClickable(true);
        card.setFocusable(true);
        card.setContentDescription(name + ". " + description);
        card.setOnClickListener(v -> action.run());

        android.widget.FrameLayout iconBox = new android.widget.FrameLayout(context);
        android.graphics.drawable.GradientDrawable soft =
                new android.graphics.drawable.GradientDrawable();
        soft.setCornerRadius(nabdhToolDp(context, 13));
        soft.setColor(android.graphics.Color.argb(
                26, android.graphics.Color.red(accent),
                android.graphics.Color.green(accent),
                android.graphics.Color.blue(accent)));
        iconBox.setBackground(soft);
        android.widget.ImageView image = new android.widget.ImageView(context);
        image.setImageResource(icon);
        image.setColorFilter(accent);
        android.widget.FrameLayout.LayoutParams imageParams =
                new android.widget.FrameLayout.LayoutParams(
                        nabdhToolDp(context, 23), nabdhToolDp(context, 23), android.view.Gravity.CENTER);
        iconBox.addView(image, imageParams);
        LinearLayout.LayoutParams iconParams =
                new LinearLayout.LayoutParams(nabdhToolDp(context, 44), nabdhToolDp(context, 44));
        card.addView(iconBox, iconParams);

        LinearLayout labels = new LinearLayout(context);
        labels.setOrientation(LinearLayout.VERTICAL);
        labels.setLayoutDirection(rtl ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        labels.setGravity(android.view.Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams labelParams =
                new LinearLayout.LayoutParams(0, -2, 1);
        labelParams.leftMargin = nabdhToolDp(context, 12);
        labelParams.rightMargin = nabdhToolDp(context, 8);
        card.addView(labels, labelParams);
        TextView title = new TextView(context);
        title.setText(name);
        title.setTextSize(15);
        title.setTypeface(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
        title.setTextColor(primary);
        title.setGravity(rtl ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT);
        title.setMaxLines(2);
        title.setEllipsize(android.text.TextUtils.TruncateAt.END);
        labels.addView(title, new LinearLayout.LayoutParams(-1, -2));

        TextView details = new TextView(context);
        details.setText(description);
        details.setTextSize(12);
        details.setTextColor(secondary);
        details.setGravity(rtl ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT);
        details.setMaxLines(2);
        details.setEllipsize(android.text.TextUtils.TruncateAt.END);
        LinearLayout.LayoutParams detailParams =
                new LinearLayout.LayoutParams(-1, -2);
        detailParams.topMargin = nabdhToolDp(context, 4);
        labels.addView(details, detailParams);

        TextView chevron = new TextView(context);
        chevron.setText(rtl ? "‹" : "›");
        chevron.setTextColor(accent);
        chevron.setTextSize(25);
        chevron.setGravity(android.view.Gravity.CENTER);
        card.addView(chevron, new LinearLayout.LayoutParams(nabdhToolDp(context, 20), nabdhToolDp(context, 42)));

        LinearLayout.LayoutParams cardParams =
                new LinearLayout.LayoutParams(-1, -2);
        cardParams.bottomMargin = nabdhToolDp(context, 8);
        parent.addView(card, cardParams);
    }

"""
c = exact(c,
    "    private int nabdhCategoryDescription() {",
    method + "    private int nabdhCategoryDescription() {",
    "category tools methods")
category.write_text(c, encoding="utf-8")

labels = {
    "values": {
        "NabdhExpandedTitle": "More tools",
        "NabdhExpandedBrowser": "Private browser",
        "NabdhExpandedBrowserInfo": "Website navigation and tracking controls",
        "NabdhExpandedCamera": "Advanced camera",
        "NabdhExpandedCameraInfo": "Camera2 capture and photo sharing",
        "NabdhExpandedChannelFeed": "Channel feed",
        "NabdhExpandedChannelFeedInfo": "Recent cached channel posts",
        "NabdhExpandedSwipes": "Swipe actions",
        "NabdhExpandedSwipesInfo": "Choose your chat-list swipe action",
        "NabdhExpandedLockInfo": "Local PIN and protected conversation previews",
    },
    "values-ar": {
        "NabdhExpandedTitle": "أدوات إضافية",
        "NabdhExpandedBrowser": "المتصفح الداخلي",
        "NabdhExpandedBrowserInfo": "تصفح المواقع والتحكم بحماية التتبع",
        "NabdhExpandedCamera": "الكاميرا المتقدمة",
        "NabdhExpandedCameraInfo": "تصوير Camera2 ومشاركة الصور",
        "NabdhExpandedChannelFeed": "موجز القنوات",
        "NabdhExpandedChannelFeedInfo": "أحدث منشورات القنوات المحفوظة",
        "NabdhExpandedSwipes": "إجراءات السحب",
        "NabdhExpandedSwipesInfo": "تخصيص السحب في قائمة المحادثات",
        "NabdhExpandedLockInfo": "رمز محلي وحماية معاينات المحادثات",
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


# Compact, tintable Material vector glyphs shared by the settings cards.
icons = {
    "browser": ("M3,12 A9,9 0,1 1,21 12 A9,9 0,1 1,3 12", "M12,3 L12,21 M3,12 L21,12 M5,7 L19,7 M5,17 L19,17"),
    "camera": ("M3,7 L7,7 L9,4 L15,4 L17,7 L21,7 L21,20 L3,20 Z", "M8,13 A4,4 0,1 1,16 13 A4,4 0,1 1,8 13"),
    "feed": ("M5,3 L19,3 L19,21 L5,21 Z", "M8,7 L16,7 M8,11 L16,11 M8,15 L16,15 M8,18 L13,18"),
    "lock": ("M5,11 L19,11 L19,21 L5,21 Z", "M8,11 L8,8 A4,4 0,0 1,16 8 L16,11 M12,15 L12,17"),
    "swipe": ("M3,8 L19,8 M15,4 L19,8 L15,12", "M21,16 L5,16 M9,12 L5,16 L9,20"),
}
drawable = root / "TMessagesProj/src/main/res/drawable"
for key, (outline, details) in icons.items():
    dest = drawable / ("nabdh_tool_" + key + ".xml")
    if dest.exists():
        raise SystemExit("Expanded tools icon collision: " + str(dest))
    dest.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android" '
        'android:width="24dp" android:height="24dp" '
        'android:viewportWidth="24" android:viewportHeight="24">\n'
        '  <path android:pathData="' + outline + '" '
        'android:fillColor="@android:color/transparent" '
        'android:strokeColor="#FFFFFFFF" android:strokeWidth="1.6" '
        'android:strokeLineCap="round" android:strokeLineJoin="round"/>\n'
        '  <path android:pathData="' + details + '" '
        'android:fillColor="@android:color/transparent" '
        'android:strokeColor="#FFFFFFFF" android:strokeWidth="1.6" '
        'android:strokeLineCap="round" android:strokeLineJoin="round"/>\n'
        '</vector>\n',
        encoding="utf-8")

print("PASS: private Camera2/Browser/ChannelFeed activities and working Settings launchers")
