#!/usr/bin/env python3
"""Security regression gate for NabdhGram's pinned Android overlay.

No claim of complete malware/vulnerability detection. Evaluate the final
generated manifest and Java source, not just test for UI settings.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parents[1]
installer = (HERE / "scripts/apply-nabdh-security-hardening.py").read_text(encoding="utf-8")
workflow = (HERE / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")
ai = (HERE / "overlay/java/NabdhAiCoreService.java").read_text(encoding="utf-8")
nano = (HERE / "overlay/java/NabdhAiNanoProvider.java").read_text(encoding="utf-8")
aiui = (HERE / "overlay/java/NabdhAiActivity.java").read_text(encoding="utf-8")
ANDROID = "{http://schemas.android.com/apk/res/android}"

def verify(condition, detail):
    if not condition:
        raise SystemExit("FAIL NabdhGram security: " + detail)

for token in (
    "cancelRunOnUIThread(nabdhMetadataUpdate)",
    "nabdhMetadataRetries <= 12",
    "unregisterMediaButtonEventReceiver(",
    "FLAG_IMMUTABLE | PendingIntent.FLAG_CANCEL_CURRENT",
    'android:exported="false"',
):
    verify(token in installer, "security overlay missing " + token)
verify("apply-nabdh-security-hardening.py Telegram-upstream" in workflow
       and "check-nabdh-security-hardening.py Telegram-upstream" in workflow,
       "security overlay and final audit must both run before Gradle")
verify("lastDiagnostic" in nano and "diagnosticCode()" in nano
       and "NANO_DIAGNOSTIC" in ai and "NANO_DIAGNOSTIC" in aiui,
       "NabdhAI AICore failure categories must be visible without sensitive logs")
verify("newSingleThreadExecutor()" in ai and "busy.compareAndSet(false, true)" in ai
       and "serial.shutdownNow()" in ai,
       "local inference must have bounded concurrency and shutdown")

if sys.argv[1:] == ["--self-test"]:
    print("PASS: security source integration contract")
    raise SystemExit(0)
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-security-hardening.py --self-test | TELEGRAM_SOURCE")

root = Path(sys.argv[1]).resolve()
manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
tree = ET.parse(manifest)
app = tree.getroot().find("application")
verify(app is not None, "main app declaration missing")
components = {}
for component in app:
    if component.tag in ("service", "receiver", "activity", "provider"):
        name = component.get(ANDROID + "name")
        if name:
            components[name] = component

internal = (".BringAppForegroundService", ".NotificationsService",
            ".VideoEncodingService", ".ImportingService",
            ".LocationSharingService", ".MusicPlayerService",
            "org.telegram.ui.Stories.recorder.StoryUploadingService",
            "org.telegram.ui.NabdhAiCoreService",
            "org.telegram.ui.NabdhVideoActivity")
for name in internal:
    item = components.get(name)
    verify(item is not None and item.get(ANDROID + "exported") == "false",
           "internal service/activity unexpectedly exported: " + name)

for name in (".MusicBrowserService", ".ContactsSyncAdapterService",
             ".AuthenticatorService", ".voip.TelegramConnectionService"):
    verify(components.get(name) is not None and
           components[name].get(ANDROID + "exported") == "true",
           "upstream framework integration broken: " + name)
verify(components.get(".SmsReceiver") is not None
       and components[".SmsReceiver"].get(ANDROID + "exported") == "true"
       and components[".SmsReceiver"].get(ANDROID + "permission") ==
           "com.google.android.gms.auth.api.phone.permission.SEND",
       "SMS Retriever receiver must authenticate Google Play Services sender")
verify(components.get("org.telegram.ui.NabdhAiCoreService").get(
           ANDROID + "process") == ":nabdh_ai",
       "AI inference process separation lost")
permissions = {}
for permission in tree.getroot().findall("uses-permission"):
    name = permission.get(ANDROID + "name")
    permissions[name] = permission

verify("android.permission.READ_CLIPBOARD" not in permissions,
       "obsolete clipboard permission must not ship")
verify("android.permission.READ_PROFILE" not in permissions,
       "obsolete profile permission must not ship")
verify(permissions["android.permission.READ_EXTERNAL_STORAGE"].get(
           ANDROID + "maxSdkVersion") == "32", "legacy read storage is unbounded")
verify(permissions["android.permission.WRITE_EXTERNAL_STORAGE"].get(
           ANDROID + "maxSdkVersion") == "29", "legacy write storage is unbounded")
for critical in ("INTERNET", "RECORD_AUDIO", "CAMERA", "READ_CONTACTS",
                 "USE_BIOMETRIC", "POST_NOTIFICATIONS"):
    verify("android.permission." + critical in permissions,
           "Telegram feature-critical permission removed: " + critical)
for banned in ("QUERY_ALL_PACKAGES", "BIND_ACCESSIBILITY_SERVICE",
               "BIND_DEVICE_ADMIN", "CAPTURE_AUDIO_OUTPUT", "READ_SMS",
               "RECEIVE_SMS", "WRITE_SECURE_SETTINGS"):
    verify("android.permission." + banned not in permissions,
           "unexpected privileged capability: " + banned)

player = (root / "TMessagesProj/src/main/java/org/telegram/messenger/MusicPlayerService.java").read_text(encoding="utf-8")
for value in ("nabdhDestroyed = true;", "nabdhMetadataUpdate = null;",
              "cancelRunOnUIThread(nabdhMetadataUpdate)", "nabdhMetadataRetries <= 12",
              "mediaSession.setActive(false);", "mediaSession.release();",
              "audioManager.unregisterMediaButtonEventReceiver("):
    verify(value in player, "media service retention risk: " + value)
verify(player.count("new Intent(NOTIFY_") >= 5 and
       "new Intent(NOTIFY_PREVIOUS).setClass(this, MusicPlayerReceiver.class)" in player
       and "new Intent(NOTIFY_CLOSE).setClass(this, MusicPlayerReceiver.class)" in player,
       "legacy media notification actions must be explicit")
verify("new Intent(NOTIFY_PREVIOUS), fixIntentFlags(PendingIntent.FLAG_MUTABLE" not in player,
       "unsafe mutable/implicit player action reintroduced")

launch = (root / "TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java").read_text(encoding="utf-8")
verify("MediaController.getInstance().setBaseActivity(this, false);" in launch
       and "MediaController.getInstance().setFeedbackView(feedbackView, false);" in launch,
       "LaunchActivity must detach from MediaController on destroy")

print("PASS: 9 app components, media lifecycle, protected PendingIntents, storage scopes, "
      "AI isolation and native Telegram launch lifecycle checked")
