#!/usr/bin/env python3
"""Enable Android Auto's notification-powered messaging using Telegram's native reply/read receivers.

No custom in-car screen, exported service, background message scraping, or
change to secret chats, media, calls or notification privacy.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-android-auto.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
source = manifest.read_text(encoding="utf-8")
metadata = '''        <!-- Android Auto notification-powered messaging only, no template UI. -->
        <meta-data android:name="com.google.android.gms.car.application"
                   android:resource="@xml/automotive_app_desc" />
'''
if "com.google.android.gms.car.application" in source:
    # Telegram already declares Android Auto: preserve the existing declaration
    # and upgrade only the messaging notification actions below.
    if source.count("com.google.android.gms.car.application") != 1 or (
            '@xml/automotive_app_desc' not in source):
        raise SystemExit("Inspect unsupported existing automotive manifest metadata")
else:
    if source.count("</application>") != 1:
        raise SystemExit("Pinned manifest application anchor changed")
    manifest.write_text(source.replace("</application>", metadata+"    </application>",1),encoding="utf-8")
xml = root / "TMessagesProj/src/main/res/xml/automotive_app_desc.xml"
xml.parent.mkdir(parents=True,exist_ok=True)
if xml.exists():
    existing = xml.read_text(encoding="utf-8")
    if "<automotiveApp" not in existing or "</automotiveApp>" not in existing:
        raise SystemExit("Existing automotive descriptor is malformed")
    if '<uses name="notification"' not in existing:
        existing = existing.replace("</automotiveApp>",
                                    '    <uses name="notification" />' + chr(10) + '</automotiveApp>', 1)
        xml.write_text(existing, encoding="utf-8")
else:
    xml.write_text('''<?xml version="1.0" encoding="utf-8"?>
<automotiveApp>
    <uses name="notification" />
</automotiveApp>
''',encoding="utf-8")
# Telegram is a two-module build. A declaration that exists only in the
# TMessagesProj library manifest can be omitted by the AFAT app variant's
# manifest merge. Place the Auto metadata and descriptor in the FINAL
# TMessagesProj_App module as well; this is what Android Auto inspects.
app_manifest = root / "TMessagesProj_App/src/main/AndroidManifest.xml"
app_xml = app_manifest.read_text(encoding="utf-8")
if "com.google.android.gms.car.application" not in app_xml:
    if app_xml.count("</application>") != 1:
        raise SystemExit("AFAT app manifest application anchor changed")
    app_xml = app_xml.replace("</application>", metadata + "    </application>", 1)
    app_manifest.write_text(app_xml, encoding="utf-8")
else:
    if app_xml.count("com.google.android.gms.car.application") != 1 or (
            "@xml/automotive_app_desc" not in app_xml):
        raise SystemExit("AFAT app existing automotive metadata needs review")
app_desc = root / "TMessagesProj_App/src/main/res/xml/automotive_app_desc.xml"
app_desc.parent.mkdir(parents=True, exist_ok=True)
auto_content = xml.read_text(encoding="utf-8")
if '<uses name="notification"' not in auto_content:
    raise SystemExit("Android Auto descriptor lacks messaging notification capability")
if app_desc.exists() and app_desc.read_text(encoding="utf-8") != auto_content:
    raise SystemExit("AFAT app automotive descriptor differs from Telegram definition")
app_desc.write_text(auto_content, encoding="utf-8")
notification = root / "TMessagesProj/src/main/java/org/telegram/messenger/NotificationsController.java"
text = notification.read_text(encoding="utf-8")
# These two native Telegram actions already have proper PendingIntent-backed,
# account/dialog-scoped receivers and RemoteInput with semantic tags. They were
# included only in the wearable extender: Android Auto needs NORMAL actions.
# Keep previews off if Telegram privacy suppresses them, and never add for
# secret chats or story notifications.
anchor = '''                    .setCategory(NotificationCompat.CATEGORY_MESSAGE);

            try {'''
replacement = '''                    .setCategory(NotificationCompat.CATEGORY_MESSAGE);

            // Android Auto reads notification-level reply/read actions.
            // Reuse Telegram's original guarded WearReplyReceiver and
            // AutoMessageHeardReceiver, without bypassing security settings.
            if (!dialogKey.story && !DialogObject.isEncryptedDialog(dialogId)
                    && !waitingForPasscode && !SharedConfig.isWaitingForPasscodeEnter) {
                builder.addAction(readAction);
                if (wearReplyAction != null) {
                    builder.addAction(wearReplyAction);
                }
            }

            try {'''
if text.count(anchor) != 1:
    raise SystemExit("Pinned per-conversation MessagingStyle action anchor changed")
for required in (
    "NotificationCompat.MessagingStyle messagingStyle;",
    ".setSemanticAction(NotificationCompat.Action.SEMANTIC_ACTION_REPLY)",
    ".setSemanticAction(NotificationCompat.Action.SEMANTIC_ACTION_MARK_AS_READ)",
    "WearReplyReceiver.class",
    "AutoMessageHeardReceiver.class",
    ".setStyle(messagingStyle)",
):
    if required not in text:
        raise SystemExit("Native Telegram messaging action capability missing: "+required)
notification.write_text(text.replace(anchor,replacement,1),encoding="utf-8")
print("PASS: Android Auto declared for notifications, existing secure Telegram reply/read actions published")
