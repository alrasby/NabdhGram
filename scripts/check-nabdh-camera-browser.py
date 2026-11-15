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
check('intent.setAction(Intent.ACTION_SEND);' in camera and
      'intent.setType("image/jpeg");' in camera and
      "Intent.EXTRA_STREAM" in camera and
      "Intent.FLAG_GRANT_READ_URI_PERMISSION" in camera,
      "captured images handed to native Telegram send without bypassing recipient UI")
check('new Intent(this, LaunchActivity.class)' in camera,
      "share target must be Telegram LaunchActivity, not exported camera")
check('FileProvider.getUriForFile(this,' in camera and
      'getPackageName() + ".provider"' in camera and
      "MediaStore.Images.Media.EXTERNAL_CONTENT_URI" in camera,
      "camera files use content URIs on both old and new Android")
check('android:name="androidx.core.content.FileProvider"' in manifest and
      'android:resource="@xml/provider_paths"' in manifest and
      'name="external_files" path="/storage/"' in provider,
      "existing Telegram FileProvider covers older camera file storage")
check("Nabdh Camera2" in camera and "كاميرا نبض جرام" in camera and
      "NabdhToolUi.install(this, page" in camera,
      "camera Arabic locale provided")
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
