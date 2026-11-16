#!/usr/bin/env python3
"""Source contract for Camera2 share handoff and browser restrictions.

A successful contract does not assert camera/device/browser runtime QA.
"""
import sys
from pathlib import Path
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-camera-browser.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
camera = (ui / "NabdhCameraActivity.java").read_text(encoding="utf-8")
browser = (ui / "NabdhBrowserActivity.java").read_text(encoding="utf-8")
manifest = (root / "TMessagesProj/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
provider = (root / "TMessagesProj/src/main/res/xml/provider_paths.xml").read_text(encoding="utf-8")
def check(condition, message):
    if not condition: raise SystemExit("FAIL: " + message)
check("private Uri savePhoto(byte[] bytes)" in camera and
      "lastPhotoUri = saved;" in camera and "sharePhoto.setEnabled(saved != null);" in camera,
      "only saved camera files can be shared")
check('send.setAction(Intent.ACTION_SEND);' in camera and
      'send.setType("image/jpeg");' in camera and
      "Intent.EXTRA_STREAM" in camera and
      "Intent.FLAG_GRANT_READ_URI_PERMISSION" in camera,
      "captured images handed to native Telegram send without bypassing recipient UI")
check('new Intent(this, LaunchActivity.class)' in camera,
      "share target must be Telegram LaunchActivity, not exported camera")
check("NabdhCameraFiles.saveCapture(this, bytes)" in camera
      and "NabdhCameraFiles.uri(this, original)" in camera
      and "NabdhCameraFiles.sanitizedShare(this, file)" in camera
      and "MediaStore.Images.Media.EXTERNAL_CONTENT_URI" not in camera,
      "camera originals must be app-private and only sanitized copies shared")
private = (ui / "NabdhCameraFiles.java").read_text(encoding="utf-8")
gallery = (ui / "NabdhCameraGalleryActivity.java").read_text(encoding="utf-8")
editor = (ui / "NabdhPhotoEditorActivity.java").read_text(encoding="utf-8")
ai = (ui / "NabdhAiPhotoEditorActivity.java").read_text(encoding="utf-8")
check("getFilesDir()" in private
      and "NabdhCamera_" in private
      and "MediaStore.Images.Media.EXTERNAL_CONTENT_URI" not in private
      and 'new File(context.getFilesDir(), ALBUM)' in private,
      "all camera photos must be stored only in app-private internal storage")
check("removeMetadata(InputStream in, OutputStream out)" in private
      and "new ExifInterface(checked)" in private
      and "APP0 JFIF" in private and "fail closed" in private.lower()
      and "privateShareDir" in private,
      "share must scrub JPEG metadata into a private temporary copy")
check("NabdhCameraFiles.recent(this)" in gallery
      and "NabdhCameraFiles.sanitizedShare(this, file)" in gallery
      and "MediaStore" not in gallery,
      "gallery may browse only internal Nabdh camera album")
check("NabdhPhotoEditorActivity.class" in gallery
      and "NabdhAiPhotoEditorActivity.class" in gallery
      and "new BitmapRegionDecoder" not in editor
      and "BitmapRegionDecoder.newInstance" in editor
      and "keepOriginal.setChecked(true)" in editor
      and "AtomicFile(original)" in editor,
      "actual editable crop/rotate must preserve original by default")
check("SelfieSegmenterOptions.SINGLE_IMAGE_MODE" in ai
      and "Segmentation.getClient(opts)" in ai
      and "portraitBlur(input, mask)" in ai
      and "NabdhCameraFiles.newPhoto(this)" in ai,
      "AI editor must use real on-device segmentation and save private copies")
check("timerSeconds == 0 ? 3 : timerSeconds == 3 ? 10 : 0" in camera
      and "timerHandler.postDelayed(this, 1000)" in camera
      and "cancelCountdown();" in camera,
      "shutter timer needs 3/10 seconds, cancellation and real delayed capture")
check('name="nabdh_private_camera" path="nabdh_camera/"' in provider
      and 'name="nabdh_private_share" path="nabdh_private_share/"' in provider,
      "provider must scope internal originals and sanitized share cache")
check('android:name="androidx.core.content.FileProvider"' in manifest and
      'android:resource="@xml/provider_paths"' in manifest and
      'name="external_files" path="/storage/"' in provider,
      "existing Telegram FileProvider covers older camera file storage")
check("Nabdh Camera2" in camera and "كاميرا نبض جرام" in camera and
      "NabdhToolUi.install(this, page" in camera,
      "camera Arabic locale provided")
check('shutter.setContentDescription(local("Capture photo", "التقاط صورة"));' in camera and
      'shutter.setOnClickListener(v -> startTimedPhoto());' in camera and
      "captureBar.addView(shutter" in camera and
      "new LinearLayout.LayoutParams(0, dp(48), 1f)" in camera,
      "camera requires accessible shutter plus bounded controls")
check("cameraGeneration++;" in camera and
      "generation != cameraGeneration" in camera and
      "openingCamera" in camera and
      "onOpened(CameraDevice opened)" in camera and
      "previewSurface.release();" in camera,
      "camera switching and pause must release old surfaces and reject late callbacks")
check("onCaptureFailed(CameraCaptureSession current," in camera and
      "onCaptureSequenceAborted(CameraCaptureSession current," in camera and
      "takingPhoto = false;" in camera,
      "asynchronous capture failure must re-enable camera shutter")
check("public boolean shouldOverrideUrlLoading(WebView view, String url)" in browser and
      "shouldOverrideUrlLoading(WebView view, WebResourceRequest request)" in browser,
      "old and new Android WebView redirects have URL allowlist")
check('!"https".equalsIgnoreCase(uri.getScheme())' in browser and
      '!"http".equalsIgnoreCase(uri.getScheme())' in browser and
      'uri.getEncodedAuthority().contains("@")' in browser,
      "only HTTP(S) with no URL userinfo allowed")
check("cfg.setJavaScriptEnabled(false);" in browser and
      "cfg.setAllowFileAccess(false);" in browser and
      "cfg.setAllowUniversalAccessFromFileURLs(false);" in browser and
      "cfg.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW)" in browser,
      "WebView sandbox default remains conservative")
check("متصفح نبض جرام" in browser and "Theme.key_windowBackgroundWhite" in browser,
      "browser Arabic and adaptive palette present")
print("PASS: camera content-URI Telegram send, browser API23 redirects, Arabic theme/source safety")
