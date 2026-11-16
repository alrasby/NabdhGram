# NabdhGram — Private Camera Gallery, Manual Editor and Real AI Portrait Effect
**Date:** 2026-11-16. **Target:** release/v1-feature-integration-and-signing (PR #79).

## Implemented

**Storage isolation:** new Nabdh Camera photos are written to `getFilesDir()/nabdh_camera/` (private Android application storage), and are NOT inserted in Android MediaStore or indexed by the public gallery. The in-app album enumerates only filenames created by Nabdh Camera. It needs **no extra access to the device photo library**. Intentional sharing grants read access to only a temporary sanitized `content://` copy via the existing FileProvider. Private photos are normally removed on uninstall; a future user-controlled export/backup can be added. Note: photos taken with previous builds were saved to public MediaStore and are **not retroactively deleted or migrated** by this change; users can remove those public copies from Gallery.

**Real 3 / 10 second shutter:** off → 3s → 10s selection, visible countdown on shutter, canceled by lens switching and activity pause, only captures if camera generation is still valid. Ordinary shutter remains instant when timer off.

**Non-destructive image editor:** opened from private gallery, drag/resize crop area, square/4:3/16:9/free aspect presets, rotate left/right by 90°, JPEG pixel lossless rotation when no cropping (EXIF-only). Cropping uses bounded Android `BitmapRegionDecoder` (up to ~12 MP output to limit RAM), JPEG 96 output, and preserves image orientation. `Keep original` checked by default; optional overwrite asks for explicit confirmation and uses `AtomicFile` for rollback.

**Privacy-safe photo sharing:** before handing a photo to Telegram, the app writes a separate JPEG copy in `getCacheDir()/nabdh_private_share/`. A streaming JPEG parser removes EXIF, XMP, Photoshop and comment segments (and non-ICC app metadata) without decoding or recompressing image pixels; it preserves the ICC color profile and restores ONLY orientation in fresh Exif. Original media is untouched. If sanitization fails the original is **never** shared by the Nabdh Camera flow. Cached copies are cleaned after 24 hours. This avoids exposing EXIF GPS but does not remove any location text visibly printed **in the image itself**.

**Actual on-device image AI:** optional `NabdhAiPhotoEditorActivity` launches Google's bundled `com.google.mlkit:segmentation-selfie:16.0.0-beta6` (~4.5 MB library addition, Android API 23+). The trained, on-device selfie-segmentation model calculates per-pixel foreground probabilities, and an offline editor uses the mask to retain the person and blur their background. Users must explicitly tap Apply AI; results save as a new image within the private album. No automatic Telegram message/call read, no cloud model, and no requirement for AICore, Gemma or Gemini Nano. To bound RAM, output is limited to approximately 4 MP and the **full-resolution original remains intact**. This is a real ML-based background effect, but **NOT** AI super-resolution, generative retouching, or an image synthesis engine.

**Capture fidelity:** JPEG maximum Camera2 resolution and optional vendor ISP HDR/noise/edge processing from previous revision remain. More megapixels are not proof of a better camera. Samsung camera's proprietary multi-frame fusion/ISP processing may outperform Camera2 JPEG; to approach OEM quality, we must query CameraX/Camera2 Extensions (HDR, Night, Auto) per-camera and run matched-scene blind comparisons of detail, noise, focus, dynamic range and shutter lag before marketing any superiority. Camera2 extensions may restrict available capture resolutions.

## Regression/acceptance

1. On Galaxy SM-S938B (Android 17), capture at max Camera2 JPEG dimensions with timer off/3/10s; cancel countdown by lens switch/app background. Confirm original JPEG stored privately and never appears in Gallery/Photos device albums.
2. Private gallery enumerates ONLY captured photos; open recent list, navigate, leave/reopen, handle 50+ photos, record RAM and PSS. Other installed apps must not discover private files. Check 23–28 and 29+ on emulator or physical devices.
3. Crop/rotate and save new copy; confirm original hash unchanged; choose replace original and test confirmation/AtomicFile rollback on storage error. Test EXIF rotations and very large JPEG with memory bounds.
4. Share and inspect emitted JPEG using `exiftool -gps:all` and `exiftool -XMP:all` plus `exiftool -Orientation`. GPS, XMP and model-specific metadata should be absent; display orientation and colors should remain usable. Sanitation must fail closed for invalid JPEG.
5. AI editor: with person in frame, compare background before/after with the foreground preserved; verify downloaded/included ML Kit model actually runs offline; confirm 2–3 repeated edits without leaked segmenters, ANR, OOM, or unexpected network access. The model quality is not yet independently measured.
6. Recheck Camera2 photo sharing, private camera video, Telegram native media picker and notification permissions. No additional `READ_MEDIA_IMAGES` app grant should be requested by this gallery.
7. CI Foundation/Preflight/Debug must pass **on final SHA**. Keep PR #79 draft and signed production Release unapproved until real device tests.

## What is not implemented or not proven

- No true generative AI image editor or super-resolution/deblurring model; these require separate vetted, licensed, device-benchmarked model weights.
- No claim that private Camera2 JPEG photos outperform Samsung's proprietary camera processing without controlled camera tests.
- NabdhAI/AI Chat **text generation** still cannot be accepted until Gemini Nano via AICore or verified Gemma returns an actual answer on the user's phone. The bundled **portrait-segmentation** model is a separate, narrower AI function and does not unblock language model inference.
- No native photo editor automatic cloud backup or external album migration.

**Implementation notes:** `NabdhCameraFiles.java`, `NabdhCameraActivity.java`, `NabdhCameraGalleryActivity.java`, `NabdhPhotoEditorActivity.java`, `NabdhAiPhotoEditorActivity.java`, `apply-nabdh-personalization.py` (including FileProvider and Gradle dependency), `check-nabdh-camera-browser.py`, `check-nabdh-personalization.py` and this document. Verify actual CI after commit.
