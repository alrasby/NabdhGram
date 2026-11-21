#!/usr/bin/env python3
"""Fail-closed contracts for native V1 home, bubble and camera personalization."""
from pathlib import Path
import sys

base = Path(__file__).resolve().parents[1]
appearance = (base / "scripts/apply-nabdh-personalization.py").read_text(encoding="utf-8")
preferences = (base / "overlay/java/NabdhHomePrefs.java").read_text(encoding="utf-8")
screen = (base / "overlay/java/NabdhPersonalizeActivity.java").read_text(encoding="utf-8")
camera = (base / "overlay/java/NabdhCameraActivity.java").read_text(encoding="utf-8")
chat = (base / "overlay/java/NabdhAiChatActivity.java").read_text(encoding="utf-8")
ai = (base / "overlay/java/NabdhAiCoreService.java").read_text(encoding="utf-8")
workflow = (base / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")

def check(ok, message):
    if not ok:
        raise SystemExit("FAIL personalization: " + message)

check("apply-nabdh-personalization.py Telegram-upstream" in workflow and
      "check-nabdh-personalization.py Telegram-upstream" in workflow,
      "apply and QA must both run in real Android preflight")
for key in ("center_title", "hide_stories", "hide_fab", "hide_search",
            "folder_mode", "bubble_radius"):
    check(key in preferences or key in screen,
          "missing real persisted appearance setting " + key)
for anchor in ('"hide_stories"', '"hide_fab"', '"hide_search"',
               "filterTabsView.addTab(", "folderLabel(getContext()",
               "updateStoriesVisibility(false)", "updateFilterTabs(true, false)",
               "applyTitle(actionBar, getContext())"):
    check(anchor in appearance, "native home layout not actually connected: " + anchor)
# Native Telegram owns both alternating title views. The branding changes
# the image wordmark in place and does not override alpha, scale or motion.
title_overlay = (base / "scripts/apply-dialogs-title.py").read_text(encoding="utf-8")
check('telegramLogoView.setImageDrawable(new NabdhNativeWordmarkDrawable());' in title_overlay and
      'private static final class NabdhNativeWordmarkDrawable' in title_overlay and
      'final float logoAlpha = logoVisibility * progress;' in title_overlay and
      'telegramLogoView.setTranslationX(titleView.getTranslationX() + dp(1));' in title_overlay and
      'LayoutHelper.createFrame(132, 22)' in title_overlay and
      '0.8f + 0.2f * containersAlpha' in title_overlay and
      'getTitlesContainer().setAlpha' not in title_overlay and
      'nabdhRestoreChatTitle' not in title_overlay and
      'setScaleX(1f)' not in title_overlay and
      'NabdhHomePrefs.applyTitle' not in title_overlay,
      "branding must reuse Telegram wordmark slot and native story motion")
check('bar.setCenterTitleAndGlass(enabled(context, "center_title"));' in preferences and
      'title.setTranslationX(' not in preferences,
      "optional title centering must use native ActionBar, not manual translations")

check("bubbleRadius = radius" in preferences and
      'putInt("bubbleRadius", radius)' in preferences and
      "didSetNewTheme" in screen,
      "bubble shape needs real Telegram radius and repaint")
for key in ("camera_remember", "camera_mirror", "camera_stabilize",
            "camera_quality", "camera_zoom_bar", "camera_smart_processing"):
    check(key in screen and key in camera, "Camera2 option is not functional: " + key)
video = (base / "overlay/java/NabdhVideoActivity.java").read_text(encoding="utf-8")
for token in ("MediaRecorder", "CameraDevice.TEMPLATE_RECORD",
              "CONTROL_VIDEO_STABILIZATION_MODE_ON", "CONTROL_AE_TARGET_FPS_RANGE",
              "enterPictureInPictureMode(", "MediaStore.Video.Media", "Intent.ACTION_SEND"):
    check(token in video, "video option not backed by real recorder: " + token)
check(all(key in video for key in (
      "new ArrayBlockingQueue<>(2)", "setMaxDuration(10 * 60 * 1000)",
      "setMaxFileSize(512L * 1024 * 1024)", "RejectedExecutionException",
      "MEDIA_RECORDER_INFO_MAX_DURATION_REACHED")),
      "video recorder needs bounded memory/storage and safe auto-stop")
check("video_fps" in preferences and "setVideoFps" in preferences and
      "video_pip" in screen and "video_stabilize" in screen and
      "NabdhVideoActivity.class" in camera,
      "video controls must be connected to native recorder")
gallery = (base / "overlay/java/NabdhCameraGalleryActivity.java").read_text(encoding="utf-8")
private = (base / "overlay/java/NabdhCameraFiles.java").read_text(encoding="utf-8")
editor = (base / "overlay/java/NabdhPhotoEditorActivity.java").read_text(encoding="utf-8")
ai_editor = (base / "overlay/java/NabdhAiPhotoEditorActivity.java").read_text(encoding="utf-8")
check("NabdhCameraGalleryActivity.java" in appearance
      and "NabdhCameraFiles.java" in appearance
      and "NabdhPhotoEditorActivity.java" in appearance
      and "NabdhAiPhotoEditorActivity.java" in appearance
      and "NabdhCameraGalleryActivity.class" in camera
      and "NabdhCameraFiles.recent(this)" in gallery
      and "getFilesDir()" in private
      and "NabdhCameraFiles.sanitizedShare(this, file)" in gallery
      and "NabdhCameraFiles.sanitizedShare(this, file)" in camera,
      "gallery must use only private originals and sanitized shares")
check("timerSeconds == 0 ? 3 : timerSeconds == 3 ? 10 : 0" in camera
      and "timerHandler.postDelayed(this, 1000)" in camera,
      "3/10 second capture timer missing")
check("BitmapRegionDecoder.newInstance" in editor
      and "keepOriginal.setChecked(true)" in editor
      and "AtomicFile(original)" in editor
      and "Math.floorMod(" not in editor
      and "normalRotation(" in editor
      and "normalRotation(userRotation + amount)" in editor
      and "normalRotation(exif + userRotation)" in editor
      and "normalRotation(exifRotation + userRotation)" in editor
      and "normalRotation(angle)" in editor
      and "normalRotation(userRotation + amount, 360)" not in editor
      and "normalRotation(exif + userRotation, 360)" not in editor
      and "normalRotation(exifRotation + userRotation, 360)" not in editor
      and "normalRotation(angle, 360)" not in editor,
      "non-destructive crop/rotate editor missing")
check("ExifInterface exif = new ExifInterface(file);" in gallery
      and "exif.getRotationDegrees()" in gallery
      and "exif.isFlipped()" in gallery,
      "private gallery previews must honor orientation and front-camera mirror")
check("Segmentation.getClient(opts)" in ai_editor
      and "SelfieSegmenterOptions.SINGLE_IMAGE_MODE" in ai_editor
      and "portraitBlur(input, mask)" in ai_editor
      and "NabdhCameraFiles.newPhoto(this)" in ai_editor,
      "real bundled on-device ML Kit portrait model missing")
check("getHighResolutionOutputSizes(ImageFormat.JPEG)" in camera
      and "Collections.max(Arrays.asList(output)" not in camera
      and "resolutionFallback = true;" in camera
      and "getBoolean(key, \"camera_quality\".equals(key))" in preferences,
      "full Camera2 resolution and compatible fallback must be functional")
check("exif.flipHorizontally();" in camera
      and "exif.saveAttributes();" in camera
      and "Bitmap.createBitmap(bitmap" not in camera,
      "high-resolution selfies must not be downsampled for mirroring")
check("CONTROL_SCENE_MODE_HDR" in camera
      and "NOISE_REDUCTION_MODE_HIGH_QUALITY" in camera
      and "EDGE_MODE_HIGH_QUALITY" in camera
      and "Vendor Camera2 ISP processing" in camera
      and "Not a generative AI model" in screen,
      "camera processing must be hardware-gated and honestly named")
check("ExifInterface" in camera and "mirroredSelfie(bytes)" in camera and
      "LENS_OPTICAL_STABILIZATION_MODE_ON" in camera and
      "CaptureRequest.JPEG_QUALITY" in camera and
      "new SeekBar(this)" in camera,
      "Camera2 mirror/OIS/quality/zoom must be real Camera2 behavior")
check("NabdhAiCoreService.CHAT" in chat and "service.send(task)" in chat and
      "history.setLength(0)" in chat and "CHAT = 5" in ai and
      "request.what == CHAT ?" in ai and "No automatic Telegram chat" in chat,
      "AI Chat must use isolated actual inference, not pretend responses or surveillance")
check("NabdhAiChatActivity.class" in (base / "scripts/apply-nabdh-ai-core.py").read_text(),
      "AI Chat must have a real settings launcher")
if sys.argv[1:] == ["--self-test"]:
    print("PASS: personalization source contract")
    raise SystemExit(0)
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-personalization.py --self-test | TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
get = lambda name: (ui / name).read_text(encoding="utf-8")
dialogs = get("DialogsActivity.java")
tabs = get("MainTabsActivity.java")
settings = get("NabdhGramFeatureCategoryActivity.java")
nativeCamera = get("NabdhCameraActivity.java")
manifest = (root / "TMessagesProj/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
for token in ("NabdhHomePrefs.folderLabel(", "NabdhHomePrefs.enabled(", "NabdhHomePrefs.applyTitle("):
    check(token in dialogs or token in tabs, "native home hook lost " + token)
stories_cell = get("Stories/DialogStoriesCell.java")
check('telegramLogoView.setImageDrawable(new NabdhNativeWordmarkDrawable());' in stories_cell and
      'private static final class NabdhNativeWordmarkDrawable' in stories_cell and
      'telegramLogoView.setImageResource(R.drawable.telegram_logo_2);' not in stories_cell and
      'telegramLogoView.setColorFilter(getTextLogoColor(), PorterDuff.Mode.MULTIPLY);' in stories_cell and
      "final float logoAlpha = logoVisibility * progress;" in stories_cell and
      "telegramLogoView.setTranslationX(titleView.getTranslationX() + dp(1));" in stories_cell,
      "stories header must retain native Telegram title animation")
check('getTitlesContainer().setScaleX(1f)' not in title_overlay and
      'getTitlesContainer().setAlpha(1f)' not in title_overlay and
      'nabdhRestoreChatTitle' not in title_overlay,
      "native Telegram stories/action-bar animation must not be overridden by branding")

check("NabdhPersonalizeActivity.HOME" in settings and
      "NabdhPersonalizeActivity.BUBBLES" in settings and
      "NabdhPersonalizeActivity.CAMERA" in settings,
      "appearance settings missing actual actions")
check("NabdhCameraGalleryActivity" in manifest
      and "NabdhPhotoEditorActivity" in manifest
      and "NabdhAiPhotoEditorActivity" in manifest
      and "NabdhCameraFiles" not in manifest and
      "NabdhPersonalizeActivity" in manifest and "NabdhAiChatActivity" in manifest
      and "NabdhVideoActivity" in manifest and 'android:supportsPictureInPicture="true"' in manifest,
      "new activities must remain private")
check("final boolean nabdhVisibleStories" in dialogs
      and "nabdhVisibleStories" in dialogs.split(
          "public void updateStoriesVisibility(boolean animated) {")[1],
      "native stories animation must use immutable derived visibility")
check("MediaRecorder" in get("NabdhVideoActivity.java")
      and "NabdhVideoActivity" in manifest,
      "video recorder must be installed as a private Android activity")
check("mirroredSelfie(bytes)" in nativeCamera and
      "NabdhCameraGalleryActivity.class" in nativeCamera and
      "NabdhCameraFiles.saveCapture(this, bytes)" in nativeCamera,
      "actual Camera2 mirror flow absent")
check("NabdhAiChatActivity.class" in settings,
      "AI Chat must appear under intelligence settings")
check("com.google.mlkit:segmentation-selfie:16.0.0-beta6" in
      (root / "TMessagesProj/build.gradle").read_text(encoding="utf-8"),
      "bundled ML Kit portrait model dependency missing")
check('name="nabdh_private_camera" path="nabdh_camera/"' in
      (root / "TMessagesProj/src/main/res/xml/provider_paths.xml").read_text(encoding="utf-8"),
      "private camera FileProvider path missing")
print("PASS: native layout, bubble, camera and isolated AI Chat routes")
