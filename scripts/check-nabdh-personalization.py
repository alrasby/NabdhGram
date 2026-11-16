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
               "applyTitle(bar, getContext())"):
    check(anchor in appearance, "native home layout not actually connected: " + anchor)
check("bubbleRadius = radius" in preferences and
      'putInt("bubbleRadius", radius)' in preferences and
      "didSetNewTheme" in screen,
      "bubble shape needs real Telegram radius and repaint")
for key in ("camera_remember", "camera_mirror", "camera_stabilize",
            "camera_quality", "camera_zoom_bar"):
    check(key in screen and key in camera, "Camera2 option is not functional: " + key)
video = (base / "overlay/java/NabdhVideoActivity.java").read_text(encoding="utf-8")
for token in ("MediaRecorder", "CameraDevice.TEMPLATE_RECORD",
              "CONTROL_VIDEO_STABILIZATION_MODE_ON", "CONTROL_AE_TARGET_FPS_RANGE",
              "enterPictureInPictureMode(", "MediaStore.Video.Media", "Intent.ACTION_SEND"):
    check(token in video, "video option not backed by real recorder: " + token)
check("video_fps" in preferences and "setVideoFps" in preferences and
      "video_pip" in screen and "video_stabilize" in screen and
      "NabdhVideoActivity.class" in camera,
      "video controls must be connected to native recorder")
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
check("NabdhPersonalizeActivity.HOME" in settings and
      "NabdhPersonalizeActivity.BUBBLES" in settings and
      "NabdhPersonalizeActivity.CAMERA" in settings,
      "appearance settings missing actual actions")
check("NabdhPersonalizeActivity" in manifest and "NabdhAiChatActivity" in manifest
      and "NabdhVideoActivity" in manifest and 'android:supportsPictureInPicture="true"' in manifest,
      "new activities must remain private")
check("final boolean nabdhVisibleStories" in dialogs
      and "nabdhVisibleStories" in dialogs.split(
          "public void updateStoriesVisibility(boolean animated) {")[1],
      "native stories animation must use immutable derived visibility")
check("MediaRecorder" in get("NabdhVideoActivity.java")
      and "NabdhVideoActivity" in manifest,
      "video recorder must be installed as a private Android activity")
check("mirroredSelfie(bytes)" in nativeCamera,
      "actual Camera2 mirror flow absent")
check("NabdhAiChatActivity.class" in settings,
      "AI Chat must appear under intelligence settings")
print("PASS: native layout, bubble, camera and isolated AI Chat routes")
