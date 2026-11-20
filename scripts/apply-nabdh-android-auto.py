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
