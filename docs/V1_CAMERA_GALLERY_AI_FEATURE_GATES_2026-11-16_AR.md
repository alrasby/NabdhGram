# NabdhGram V1 — Camera gallery, actual JPEG resolution, local AI blockers, and hidden V2 backlog
**Updated:** 2026-11-16. **Branch:** release/v1-feature-integration-and-signing.

## Camera changes included in this development revision

- **Captured-photo gallery:** `NabdhCameraGalleryActivity` is an internal, non-exported Activity reachable from Nabdh Camera. It queries only `Pictures/NabdhGram/` filenames `NabdhCamera_*.jpg` on scoped-storage devices, with a private FileProvider fallback for Android 23–28. No READ_MEDIA_IMAGES/READ_EXTERNAL_STORAGE grant is requested for the gallery. Grid thumbnails are decoded off the UI thread with bounded queue (70 tasks), an 8 MiB memory cache and maximum 400 recent images per load. Full-size image preview is sampled to display size; share passes the ORIGINAL content URI into Telegram. No delete, edit, cloud upload or background surveillance.
- **JPEG resolution:** enable `camera_quality` by default on new installations, but respect existing user preferences. Choose largest actually advertised JPEG output including `getHighResolutionOutputSizes(JPEG)` when available. Never silently cap to 10/12/24 MP. If the camera HAL refuses the preview + high-res JPEG stream combination, retry once with a compatible standard 12 MP-ish size and explain the fallback. This does **not** guarantee vendor-proprietary 50/200 MP sensor modes not exposed through ordinary Camera2. Avoid allocating >96 MiB for a faulty JPEG buffer.
- **Mirrored selfie:** maintain full JPEG image dimensions and pixels by writing mirrored orientation in EXIF without bitmap downscaling/recompressing. For very large JPEGs or unsupported EXIF updates, retain the original photo rather than discard or degrade it.
- **Adaptive photo processing (optional):** when enabled and supported by the selected Camera2 HAL, use native HDR scene, high-quality noise reduction and edge processing in the final still request. It is the manufacturer's camera ISP/algorithm, **not** a custom AI model; label reflects this. Expose no AI-branded feature that does not run a trained model. Future CameraX/Camera2 Extensions (HDR/Night/Bokeh) will be separately assessed for hardware and capture-session compatibility.

## Feature visibility policy

To honor “hide unready features but keep code for next release”, the following UI tiles remain in the repository but are hidden from the default release UI using `NabdhFeatureGates`:

| Feature ID | What is hidden | What is preserved |
| --- | --- | --- |
| 203 | Redundant standalone Smart Chat Preview detail card with no own working button | Native Telegram preview and its other active entry points |
| 401 | Standalone “Translation” details card with no user action | Telegram native translation engine and future translation settings integration |
| AI Chat settings tile | Hidden until a real local provider sends a non-status, non-error inference response to NabdhAI Core | NabdhAI Core model setup/diagnostics and the separate AI Chat implementation; unlocked automatically after successful model inference |

Retain `NabdhShield` manual inspection, Message Workspace, supported Voice Clarity gain, scheduling, styles, fonts, Camera2, network/storage/proxy, native translation and all core Telegram features that have actual functionality. No engine/source deleted; V2 can enable a hidden row after its real acceptance test. **Do not use a debug switch to falsely claim completed AI inference.**

Additional V2 ideas still pending development, not shown as working features in V1: advanced noise reduction, true channel aggregation beyond cached posts, on-device camera semantic processing, CameraX OEM extension HDR/night, media editing, video message PiP, higher-level AI features requiring a validated model, full automatic malicious-link blocking.

## Why NabdhAI currently has no real answer

1. On the user's Samsung Galaxy S25 Ultra SM-S938B Android 17, Google AICore `checkStatus()` returned an error category, not `AVAILABLE` or `DOWNLOADABLE`. Earlier beta4 had a known non-Pixel issue; SDK updated to beta5. Need an actual new app log/status result to isolate service binding, initialization, API incompatibility, policy or quota.
2. Gemini Nano is a **system-managed** Google model; placing arbitrary model weights in the Telegram APK cannot make AICore ready. Device/OS eligibility alone does not assert runtime availability.
3. The Gemma fallback needs a compatible licensed `.task` model (approximately 555 MiB for referenced 1B int4 artifact), integrity verification, MediaPipe runtime compatibility, ARM64 acceleration/memory benchmarking and actual inference proof. Model weight redistribution is not permitted without checking applicable terms and provenance.
4. `NabdhAI Chat` has a real isolated service IPC but cannot respond without a local model. Its shortcut remains hidden until the first successful real inference response; Core model setup stays accessible.
5. Quality requires Arabic correctness/latency/offline/privacy tests on the exact release candidate device and process; no fabricated ‘AI-ready’ statuses.

## Release-test checklist for this change

1. Camera gallery: after taking 3 photos, open gallery; confirm 3 image previews, original-photo share, chronological ordering, rotation, RTL, repeated app leave/reopen. Confirm no other device albums are listed. Test Android 29+ and Android 23–28 provider path.
2. Highest-resolution option: inspect JPEG width/height and file size against actual `CameraCharacteristics`; verify quality on back/front cameras and zoom, and no crash at max size. If the camera rejects high-res + preview, confirm clean fallback notification.
3. EXIF mirror: check front selfie dimensions unchanged; preview rotates/mirrors as expected; original front selfie without mirror remains unmodified. Check image-apps that respect EXIF.
4. Adaptive ISP: test on/off, including a camera that advertises no HDR/NR modes. Do not claim model AI inference from this feature.
5. Hidden features: release settings contain no nonfunctional preview/translation detail cards, no AI Chat launch until real inference, but all existing functional Telegram controls still work. Later V2 should be able to re-enable these cards by changing a single centralized gate.
6. CI: Foundation, pinned-source, and Java/Gradle APK build must all succeed on the **same new SHA**. Physical Android QA follows. **Do not merge PR #79 or sign production before that.**

## Recommended high-value remaining V1 features (not secretly added)

- Photo timer (3/10 seconds) and original-resolution share—small, camera-specific change after gallery is verified.
- One-tap “clear completed private downloads/cache” using Telegram's already implemented cache-management UI, **without deleting chat history**.
- A privacy-first “copy diagnostic code” for NabdhAI errors, excluding logcat/messenger data.

No unapproved feature surface is introduced by this recommendation list.
