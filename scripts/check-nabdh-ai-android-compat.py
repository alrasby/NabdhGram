#!/usr/bin/env python3
"""Validate optional Android 26+ ML Kit integration in Telegram's API 23 build.

This is a lightweight source contract. The *real* manifest merge runs as an
independent early Gradle task in CI and remains the definitive check.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-ai-android-compat.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main"
manifest = ET.parse(ui / "AndroidManifest.xml")
tools = "{http://schemas.android.com/tools}overrideLibrary"
sdk = manifest.getroot().find("uses-sdk")
if sdk is None:
    raise SystemExit("FAIL: generated manifest lacks pinned uses-sdk override")
allowed = set((sdk.attrib.get(tools) or "").split(","))
expected = {
    "com.google.mlkit.vision.segmentation.subject",
    "com.google.mlkit.genai.prompt",
    "com.google.mlkit.genai.common",
}
if allowed != expected:
    raise SystemExit(f"FAIL: unexpected optional AI manifest override list: {allowed}")
activity = (ui / "java/org/telegram/ui/NabdhAiActivity.java").read_text()
nano = (ui / "java/org/telegram/ui/Components/NabdhAiNanoProvider.java").read_text()
gemma = (ui / "java/org/telegram/ui/Components/NabdhAiGemmaProvider.java").read_text()
gradle = (root / "TMessagesProj/build.gradle").read_text()
if "android.os.Build.VERSION.SDK_INT < 26" not in activity:
    raise SystemExit("FAIL: AI Activity must refuse startup on Android 23-25")
if "Build.VERSION.SDK_INT < 26" not in nano or "Build.VERSION.SDK_INT < 28" not in gemma:
    raise SystemExit("FAIL: AI runtime API guards missing")
if "genai-prompt:1.0.0-beta5" not in gradle or "tasks-genai:0.10.27" not in gradle:
    raise SystemExit("FAIL: expected pinned AI dependency missing")
service = (ui / "java/org/telegram/ui/NabdhAiCoreService.java").read_text()
if not all(token in nano for token in (
        "int status()", "FeatureStatus.DOWNLOADABLE", "FeatureStatus.UNAVAILABLE",
        "futures.download(new DownloadCallback()", "onDownloadFailed(GenAiException",
        "new DownloadCallback()", "public static int download(")):
    raise SystemExit("FAIL: Gemini Nano status and explicit official AICore download missing")
if not all(token in service for token in (
        "DOWNLOAD_NANO = 4", "NabdhAiNanoProvider.download(",
        "NANO_DOWNLOADABLE", "NANO_DOWNLOADING", '"NANO_UNAVAILABLE"',
        '"AICORE_CHECK_FAILED"', "NANO_CAN_DOWNLOAD", "sendNano(")):
    raise SystemExit("FAIL: AI isolated service cannot report/download a supported model")
if not all(token in activity for token in (
        "NabdhAiCoreService.DOWNLOAD_NANO", "downloadNano.setEnabled(downloadable)",
        '"NANO_UNAVAILABLE"', '"NANO_DOWNLOAD_FAILED"',
        '"AICORE_CHECK_FAILED"', "screen.addView(state, 1)",
        'لا يوجد نموذج ذكاء محلي متوافق مثبت')):
    raise SystemExit("FAIL: user-approved AICore download or localized no-model state missing")
if "kotlinx-coroutines-android:1.11.0" not in gradle:
    raise SystemExit("FAIL: ML Kit prompt must include coroutine dependency for downloads")
if "Download Gemini Nano" not in activity or ".setPositiveButton(local(" not in activity:
    raise SystemExit("FAIL: model download must require explicit user confirmation")
# No placebo model download: the button is disabled until a real AICore
# DOWNLOADABLE check, and a failed check must not be called "unsupported".
if "STATUS_CHECK_FAILED = -100" not in nano or "return STATUS_CHECK_FAILED;" not in nano:
    raise SystemExit("FAIL: AICore service failures must differ from unsupported hardware")
if "data.putBoolean(NANO_CAN_DOWNLOAD, nanoStatus == FeatureStatus.DOWNLOADABLE)" not in service:
    raise SystemExit("FAIL: native model download must only be enabled for DOWNLOADABLE")
if "downloadNano.setEnabled(false);" not in activity or "downloadNano.setAlpha(0.5f);" not in activity:
    raise SystemExit("FAIL: Gemini download button should be disabled before status check")
if "Uri.parse(\"https://developers.google.com/ml-kit/genai/#device-support\")" not in activity:
    raise SystemExit("FAIL: official compatibility guidance missing")
if "Uri.parse(\"https://developers.google.com/edge/mediapipe/solutions/genai/llm_inference/android\")" not in activity:
    raise SystemExit("FAIL: verified MediaPipe Gemma import guidance missing")
if "GEMMA_3_1B_INT4_SHA256" not in activity or (
        "e3d981c01aeaaac69a84ffa0d4be13281b3176731063f1bea1c9fe6887bd9dee" not in activity):
    raise SystemExit("FAIL: recommended Gemma int4 integrity hash missing")
if not all(x in activity for x in ("Gemma3-1B-IT/blob/main/gemma3-1b-it-int4.task", "huggingface.co/litert-community/")):
    raise SystemExit("FAIL: recommended Gemma file must open canonical license-gated page")
if "NabdhAiCoreService.CHAT" not in (ui / "java/org/telegram/ui/NabdhAiChatActivity.java").read_text():
    raise SystemExit("FAIL: AI Chat must use isolated real model inference service")
if ".setTopK(" in gemma:
    raise SystemExit("FAIL: unsupported MediaPipe topK setter restored")
if "محرك نبض للذكاء الاصطناعي" not in activity or (
        "org.telegram.ui.Components.NabdhToolUi.styleButton(this, button)" not in activity
        or "org.telegram.ui.Components.NabdhToolUi.styleInput(this, textInput)" not in activity):
    raise SystemExit("FAIL: opt-in AI UI lost Arabic or theme-aware Glass")
if "الذكاء المحلي غير متاح لهذا الإصدار" not in activity:
    raise SystemExit("FAIL: old Android devices must show local AI unavailability")
print("PASS: ML Kit prompt/common manifest allowlist; Android 23-25 service guard; pinned providers")
