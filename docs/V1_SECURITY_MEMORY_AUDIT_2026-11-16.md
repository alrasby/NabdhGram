# NabdhGram — Security, Playback and Runtime Audit
**Date:** 2026-11-16. **Branch:** release/v1-feature-integration-and-signing.  
**Telegram pinned source:** 21f7d109da6ab3506c9e9577f98c6a38771ab335 (13.2.2 / 7303).

## Scope and evidence

Reviewed the actual upstream LaunchActivity, MusicPlayerService, MusicPlayerReceiver, MediaController, TelegramMediaSession, MusicBrowserService, BackupAgent, AndroidManifest and the NabdhGram overlays/services. This is a **targeted static review**, source regression gate and real APK build check. It is **not** a professional full penetration test, SBOM verification, independent malware verdict, comprehensive security guarantee, or measured CPU/RAM/energy benchmark on user hardware. No phone is connected to this execution environment. Model download and on-device inference still require hardware evidence.

## Findings and fixes

| Severity | Finding | Code action | Remaining verification |
|---|---|---|---|
| Moderate (potential memory/CPU retention) | `MusicPlayerService` creates a self-rescheduling metadata Runnable every 500ms if `C.TIME_UNSET`, without a cancellation handle in `onDestroy`. It captures the Service instance. | Store one callback reference, cancel on replacement/destroy, guard against destroyed state and stop after 12 retries (6 seconds). | Replay/stop/rotate 30+ times; heap-dump retained MusicPlayerService objects, PSS trends, seek/lock-screen controls. |
| Moderate (unnecessary IPC exposure) | Several Telegram internal services, including `MusicPlayerService`, were exported without any external intent-filter. | Set exported=false for 7 internal services. Keep public platform integrations unchanged (sync, contacts auth, Android Auto MediaBrowser, Telecom, push). | Run Firebase notifications, calls, background transfers, media and explicit service intents in Debug AND signed Release. |
| Moderate (PendingIntent tampering) | Legacy audio notification actions used implicit, mutable `PendingIntent` objects. | Explicitly target the private `MusicPlayerReceiver` and mark notification controls immutable; retain the Android media-key PendingIntent mutable because key events fill in required extras. | Play/pause/next/previous/close from notification, lock screen, Bluetooth headset and Android Auto. |
| Low–moderate (missing paired lifecycle cleanup) | AudioManager media-button receiver registration not explicitly unregistered and media player image/session references not cleared. | Unregister safely, release MediaSession, clear bitmap/receiver references after service destruction. | OEM Bluetooth interruption, repeated service recreation. |
| Moderate (OTP spoof prevention) | Telegram's `.SmsReceiver` was exported for Google SMS Retriever without a sender permission. | Require the official `com.google.android.gms.auth.api.phone.permission.SEND` on the receiver **only**, as Google documents; no READ_SMS / RECEIVE_SMS app permission. | Exercise SMS Retriever login on Google Play Services, plus manual OTP and QR login. |
| Low / privacy surface | Legacy READ_CLIPBOARD and READ_PROFILE manifest requests are not referenced in Telegram Java code. Legacy storage permissions were not upper bounded. | Remove the two unused manifest permissions. Bound READ_EXTERNAL_STORAGE to SDK <=32 and WRITE_EXTERNAL_STORAGE to SDK <=29. | Check merged APK permission list; Android 23, 29, 32, 33+ storage/send behavior. |
| Diagnostic (no hardware verdict) | AICore status failures were collapsed into a generic message. | Return safe diagnostic categories only: TIMEOUT, PERMISSION, API_INCOMPATIBLE, CLIENT_EXECUTION, CANCELLED, INTERRUPTED or SERVICE_UNAVAILABLE; no prompt or exception message is logged. | Repeat on user's Galaxy S25 Ultra with ML Kit beta5, inspect category; if still failing, obtain sanitized on-device diagnostics and check AICore availability. |
| Open (architectural risk) | Upstream manifest requests `android:allowBackup=true` with custom `BackupAgent` for saved tokens. | No silent removal: changing backup semantics can invalidate session restoration. Flagged for production privacy decision and sensitive backup/restore audit. | Review token backup requirements, encryption, dataExtractionRules / backup rules and Google Play policy. |
| Open (architectural risk) | Upstream allows HTTP cleartext for browser URL compatibility. | No blanket disabling: existing HTTP browsing would break. Needs separate browser/network policy and transport-specific audit. | Test HTTP browser, safe-link warnings, proxies and transport interception. |

**Permission policy:** Keep READ_CONTACTS/WRITE_CONTACTS, RECORD_AUDIO, CAMERA, READ_MEDIA_*, POST_NOTIFICATIONS, FOREGROUND_SERVICE_*, Bluetooth, phone/call and synchronization permissions that support existing Telegram features until functional proofs permit narrowing. `REQUEST_INSTALL_PACKAGES`, `SYSTEM_ALERT_WINDOW` and account-sync privileges merit separate per-feature review; do not silently remove and break upgrade/calling behavior. The final actual APK permission list is attached as `apk-permissions.txt` to GitHub build diagnostics.

**Activity:** This Telegram build uses `LaunchActivity`, not `MainActivity`. The pinned `LaunchActivity.onDestroy()` already calls `MediaController.getInstance().setBaseActivity(this, false)`, clears feedback view, detaches a global layout listener and cleans up delegates/fragments. The concrete potential leakage path addressed is in `MusicPlayerService`, not a proven LaunchActivity leak.

**DDoS/backdoors:** Neither DDoS immunity nor absence of backdoors can be certified by a single source scan. The AI service enforces one request at a time, optional emoji renderer uses a bounded queue, and external URLs need explicit safe-link review. No automatic chat/call extraction is wired by NabdhAI. A full supply-chain SBOM, CVE scan, network observation, IPC fuzzing, WebView inspection, TLS/proxy tests, OWASP MASVS/MSTG dynamic tests, and signed-APK assessment remain required.

## Video resource hardening

The Camera2/MediaRecorder video tool now has an explicit maximum duration of 10 minutes and a 512 MiB file-size cap. A single video-persist worker has at most 2 queued files; backlog rejection deletes the transient recording and informs the user instead of queuing arbitrary file copies in RAM/temporary storage. Hardware tests must check MediaRecorder callbacks when reaching those limits, no duplicate stop calls, storage-full behavior, and clean PiP termination. These are code-level safeguards, not proven energy or RAM results.

## Runtime profiling instructions

With one authorized ARM64 phone and Android Platform Tools:

```bash
bash scripts/profile-nabdh-runtime.sh ./nabdh-runtime-local 12
```

The script takes repeated app PSS snapshots (~15-second spacing), `gfxinfo`, `batterystats --charged` and a battery baseline. It neither restarts the phone, resets battery counters, requests root, reads messages, nor uploads any diagnostic files. PSS growth does not itself prove a leak; acquire a Java heap dump/Android Studio Memory Profiler and confirm retained references after repeated playback. Battery stats are since last charge and cannot prove an app energy budget without controlled idle/active tests and equivalent network/brightness/signal.

**Suggested real-device acceptance:** 30 playback stop/start cycles, 20 chat navigation, 10 AI status calls with and without a model, 10 camera/photo/video sessions, Wi-Fi+mobile data handover, screen-off idle 30 minutes and a separate 30-minute foreground workload. Record PSS, native allocations, frames/jank, CPU, radio/WAKE_LOCK, network, crashes, ANRs and battery delta. Do not compare battery values across inconsistent environmental conditions.

## Go / no-go

- CI Foundation, Telegram pinned-source preflight, and Android Debug compilation need to pass **on the same new commit**, including the final packaged manifest permission report.
- Once CI passes, test storage/contacts/calls/notifications/playback/video regression on ARM64; compare RAM and battery baselines.
- NabdhAI/AI Chat remains **NO-GO** until a verified model actually returns a locally generated result.
- Signed Release APK, Firebase, clean install/upgrade and license/privacy review remain unverified.
- PR #79 stays draft. Never merge/publish based only on source gates.
