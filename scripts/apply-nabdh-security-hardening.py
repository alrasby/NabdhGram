#!/usr/bin/env python3
"""Minimal security hardening for pinned Telegram 13.2.2 / NabdhGram.

Does not intercept messages, contacts, WebView traffic or Telegram VoIP.
Protects internal services and media notification PendingIntents; removes
a manifest-only legacy permission and bounds music metadata callbacks.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-security-hardening.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()

def once(source, old, new, reason):
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"FAIL security {reason}: expected one pinned anchor, got {count}")
    return source.replace(old, new, 1)

manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
# READ_CLIPBOARD has no Android runtime grant path for ordinary clipboard reads.
# It is present only in upstream's manifest and is not referenced in its Java code.
m = once(m, '    <uses-permission android:name="android.permission.READ_CLIPBOARD"/>\n',
         '', "legacy READ_CLIPBOARD")
m = once(m, '    <uses-permission android:name="android.permission.READ_PROFILE"/>\n',
         '', "obsolete READ_PROFILE")
# Old Android storage support must remain functional; do not grant broad storage
# beyond OS versions where the legacy permissions are meaningful.
m = once(m, '<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>',
         '<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32"/>',
         "legacy read storage scope")
m = once(m, '<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" tools:node="replace" />',
         '<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29" tools:node="replace" />',
         "legacy write storage scope")
# The SMS Retriever broadcast is exported for Google Play Services, but
# only an authenticated sender holding Google's signature permission may
# provide an OTP. This is a RECEIVER permission, not a new app permission.
m = once(m,
         'android:name=".SmsReceiver"\n            android:exported="true">',
         'android:name=".SmsReceiver"\n            android:exported="true"\n'
         '            android:permission="com.google.android.gms.auth.api.phone.permission.SEND">',
         "Google Play Services SMS Retriever sender authentication")
# Only internal, explicitly started Telegram services with NO intent-filters.
# Account/contacts sync, telecom, browser browsing and FCM remain exported.
internal_services = (
    '.BringAppForegroundService', '.NotificationsService', '.VideoEncodingService',
    'org.telegram.ui.Stories.recorder.StoryUploadingService', '.ImportingService',
    '.LocationSharingService', '.MusicPlayerService'
)
for name in internal_services:
    tag = f'android:name="{name}"'
    start = m.find('<service', 0)
    matches = []
    while start >= 0:
        end = m.find('/>', start)
        end2 = m.find('</service>', start)
        if end2 != -1 and (end == -1 or end2 < end):
            end = end2 + len('</service>') - 2
        if end == -1: break
        block = m[start:end + 2]
        if tag in block:
            matches.append((start, end + 2, block))
        start = m.find('<service', end + 2)
    if len(matches) != 1:
        raise SystemExit(f"FAIL security {name}: cannot isolate unique service")
    start, end, block = matches[0]
    if 'android:exported="true"' not in block or '<intent-filter' in block:
        raise SystemExit(f"FAIL security {name}: service exposure changed upstream")
    m = m[:start] + block.replace('android:exported="true"',
                                  'android:exported="false"', 1) + m[end:]
manifest.write_text(m, encoding="utf-8")

player = root / "TMessagesProj/src/main/java/org/telegram/messenger/MusicPlayerService.java"
s = player.read_text(encoding="utf-8")
s = once(s, '    private String loadingFilePath;',
'''    private String loadingFilePath;

    // Prevent legacy RemoteControlClient polling callbacks from retaining a
    // destroyed Service, and cap duration polling when metadata never arrives.
    private Runnable nabdhMetadataUpdate;
    private int nabdhMetadataRetries;
    private volatile boolean nabdhDestroyed;
'''.rstrip(), "music pending callback fields")
s = once(s, '                AndroidUtilities.runOnUIThread(new Runnable() {',
'''                if (nabdhMetadataUpdate != null) {
                    AndroidUtilities.cancelRunOnUIThread(nabdhMetadataUpdate);
                }
                nabdhMetadataRetries = 0;
                nabdhMetadataUpdate = new Runnable() {''',
"music callback replace")
s = once(s,
'''                        if (remoteControlClient == null || MediaController.getInstance().getPlayingMessageObject() == null) {
                            return;
                        }
                        if (MediaController.getInstance().getPlayingMessageObject().audioPlayerDuration == C.TIME_UNSET) {
                            AndroidUtilities.runOnUIThread(this, 500);
                            return;
                        }''',
'''                        if (nabdhDestroyed || remoteControlClient == null ||
                                MediaController.getInstance().getPlayingMessageObject() == null) {
                            nabdhMetadataUpdate = null;
                            return;
                        }
                        if (MediaController.getInstance().getPlayingMessageObject().audioPlayerDuration == C.TIME_UNSET) {
                            // Do not poll forever in the background on a broken
                            // stream or an audio item that never resolves duration.
                            if (++nabdhMetadataRetries <= 12) {
                                AndroidUtilities.runOnUIThread(this, 500);
                            } else {
                                nabdhMetadataUpdate = null;
                            }
                            return;
                        }
                        nabdhMetadataUpdate = null;''',
"bounded duration retry")
s = once(s,
'''                }, 1000);
            }
            if (MediaController.getInstance().isDownloadingCurrentMessage()) {''',
'''                };
                AndroidUtilities.runOnUIThread(nabdhMetadataUpdate, 1000);
            }
            if (MediaController.getInstance().isDownloadingCurrentMessage()) {''',
"media callback schedule")
s = once(s,
'''    public void onDestroy() {
        unregisterReceiver(headsetPlugReceiver);''',
'''    public void onDestroy() {
        nabdhDestroyed = true;
        if (nabdhMetadataUpdate != null) {
            AndroidUtilities.cancelRunOnUIThread(nabdhMetadataUpdate);
            nabdhMetadataUpdate = null;
        }
        unregisterReceiver(headsetPlugReceiver);''',
"service cleanup")
s = once(s,
'''            audioManager.unregisterRemoteControlClient(remoteControlClient);
        }
        if (mediaSession != null) {
            mediaSession.release();
        }''',
'''            audioManager.unregisterRemoteControlClient(remoteControlClient);
            // Paired with the registerMediaButtonEventReceiver in onStartCommand.
            try {
                audioManager.unregisterMediaButtonEventReceiver(
                        new ComponentName(getApplicationContext(), MusicPlayerReceiver.class.getName()));
            } catch (RuntimeException ignored) {
                // Some OEM audio services unregister the receiver internally.
            }
            remoteControlClient = null;
        }
        if (mediaSession != null) {
            mediaSession.setActive(false);
            mediaSession.setCallback(null);
            mediaSession.release();
            mediaSession = null;
        }
        if (imageReceiver != null) {
            imageReceiver.setImageBitmap((BitmapDrawable) null);
            imageReceiver = null;
        }
        if (albumArtPlaceholder != null) {
            albumArtPlaceholder.recycle();
            albumArtPlaceholder = null;
        }''',
"service audio/session/image cleanup")
# Media-button PendingIntent remains MUTABLE, because Android fills key events.
# Action buttons and artwork notifications need no fill-in and must be immutable.
button_actions = ("NOTIFY_PREVIOUS", "NOTIFY_CLOSE", "NOTIFY_PAUSE",
                  "NOTIFY_NEXT", "NOTIFY_PLAY")
for action in button_actions:
    before = 'new Intent(' + action + '), fixIntentFlags(PendingIntent.FLAG_MUTABLE'
    after = ('new Intent(' + action +
             ').setClass(this, MusicPlayerReceiver.class), fixIntentFlags(PendingIntent.FLAG_IMMUTABLE')
    s = once(s, before, after, "implicit legacy notification " + action)
# The modern MediaStyle notifications are already explicit, but their action
# fields are immutable as well; no inline reply or mutable parameters needed.
s = s.replace('fixIntentFlags(PendingIntent.FLAG_MUTABLE | PendingIntent.FLAG_CANCEL_CURRENT)',
              'fixIntentFlags(PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_CANCEL_CURRENT)')
s = once(s,
'''PendingIntent contentIntent = PendingIntent.getActivity(ApplicationLoader.applicationContext, 0, intent, fixIntentFlags(PendingIntent.FLAG_MUTABLE));''',
'''PendingIntent contentIntent = PendingIntent.getActivity(ApplicationLoader.applicationContext, 0, intent, fixIntentFlags(PendingIntent.FLAG_IMMUTABLE));''',
"player notification content intent")
player.write_text(s, encoding="utf-8")

# Telegram 13.2.2 retains the most recently created LaunchActivity through
# two static strong references. The OS can destroy/recreate that Activity
# during a rotation or a resource configuration change. Clearing references
# to the destroyed instance prevents retaining its entire old view hierarchy.
# The identity checks are essential: NEVER clear a newer live Activity.
launch = root / "TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java"
launch_source = launch.read_text(encoding="utf-8")
launch_source = once(launch_source,
'''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N && frameMetricsOverlayView != null) {
            frameMetricsOverlayView.detach();
        }
    }

    private static void onDestroyStaticResources()''',
'''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N && frameMetricsOverlayView != null) {
            frameMetricsOverlayView.detach();
        }
        if (instance == this) {
            instance = null;
        }
        if (staticInstanceForAlerts == this) {
            staticInstanceForAlerts = null;
        }
    }

    private static void onDestroyStaticResources()''',
"LaunchActivity static stale references")
launch.write_text(launch_source, encoding="utf-8")
print("PASS: internal services, MediaPlayer lifecycle, LaunchActivity refs, PendingIntents and legacy storage scope")
