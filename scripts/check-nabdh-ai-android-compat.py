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
if "genai-prompt:1.0.0-beta4" not in gradle or "tasks-genai:0.10.27" not in gradle:
    raise SystemExit("FAIL: expected pinned AI dependency missing")
service = (ui / "java/org/telegram/ui/NabdhAiCoreService.java").read_text()
if not all(token in nano for token in (
        "int status()", "FeatureStatus.DOWNLOADABLE", "FeatureStatus.DOWNLOADING",
        "futures.download(new DownloadCallback()", "onDownloadFailed(GenAiException",
        "new DownloadCallback()", "public static int download(")):
    raise SystemExit("FAIL: Gemini Nano status and explicit official AICore download missing")
if not all(token in service for token in (
        "DOWNLOAD_NANO = 4", "NabdhAiNanoProvider.download(",
        "NANO_DOWNLOADABLE", "NANO_DOWNLOADING", '"NO_MODEL"')):
    raise SystemExit("FAIL: AI isolated service cannot report/download a supported model")
if not all(token in activity for token in (
        "NabdhAiCoreService.DOWNLOAD_NANO", '"تنزيل Gemini Nano (للأجهزة المدعومة)"',
        '"NANO_UNAVAILABLE"', '"NANO_DOWNLOAD_FAILED"',
        '"لا يوجد نموذج ذكاء محلي متوافق مثبت"')):
    raise SystemExit("FAIL: user-approved AICore download or localized no-model state missing")
if "kotlinx-coroutines-android:1.11.0" not in gradle:
    raise SystemExit("FAIL: ML Kit beta4 download must pin compatible coroutines (Google known issue)")
if "Download Gemini Nano" not in activity or ".setPositiveButton(local(" not in activity:
    raise SystemExit("FAIL: model download must require explicit user confirmation")
if ".setTopK(" in gemma:
    raise SystemExit("FAIL: unsupported MediaPipe topK setter restored")
if "محرك نبض للذكاء الاصطناعي" not in activity or (
        "org.telegram.ui.Components.NabdhToolUi.styleButton(this, button)" not in activity
        or "org.telegram.ui.Components.NabdhToolUi.styleInput(this, textInput)" not in activity):
    raise SystemExit("FAIL: opt-in AI UI lost Arabic or theme-aware Glass")
if "الذكاء المحلي غير متاح لهذا الإصدار" not in activity:
    raise SystemExit("FAIL: old Android devices must show local AI unavailability")
print("PASS: ML Kit prompt/common manifest allowlist; Android 23-25 service guard; pinned providers")
