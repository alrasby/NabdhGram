#!/usr/bin/env python3
"""Wire manual NabdhAI Core into pinned Telegram without modifying chat paths.

Two mutually exclusive providers:
* Gemini Nano through AICore/ML Kit when its model is AVAILABLE.
* Privately imported, SHA-256-verified MediaPipe Gemma model otherwise.
Inference lives in a private, non-exported Android process.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-ai-core.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
repo = Path(__file__).resolve().parents[1]
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"


def once(source: str, marker: str, updated: str, label: str) -> str:
    count = source.count(marker)
    if count != 1:
        raise SystemExit(f"NabdhAI {label}: expected 1 anchored source, found {count}")
    return source.replace(marker, updated, 1)


for name in ("NabdhAiNanoProvider.java", "NabdhAiGemmaProvider.java"):
    dest = ui / "Components" / name
    if dest.exists():
        raise SystemExit("NabdhAI component collision: " + name)
    dest.write_bytes((repo / "overlay/java" / name).read_bytes())

for name in ("NabdhAiCoreService.java", "NabdhAiActivity.java", "NabdhAiChatActivity.java"):
    dest = ui / name
    if dest.exists():
        raise SystemExit("NabdhAI activity/service collision: " + name)
    dest.write_bytes((repo / "overlay/java" / name).read_bytes())

manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
xml = manifest.read_text(encoding="utf-8")
# The base Telegram APK deliberately supports Android 23+. ML Kit GenAI
# plus transitive GenAI Common require Android 26+; a narrowly scoped
# override lets the *app* retain Android 23 while optional AI code is guarded
# below Android 26. Hardware QA on API 23–25 remains a release requirement.
# Never override an unrecognized library, and never start AICore on older OSes.
legacy = '<uses-sdk tools:overrideLibrary="com.google.mlkit.vision.segmentation.subject"/>'
approved = '<uses-sdk tools:overrideLibrary="com.google.mlkit.vision.segmentation.subject,com.google.mlkit.genai.prompt,com.google.mlkit.genai.common"/>'
xml = once(xml, legacy, approved, "Android 23 compatibility / ML Kit 26 guard")

marker = '        <!-- NabdhGram user-launched tools; never exported or reachable by implicit intents -->'
xml = once(xml, marker,
    marker + '''
        <!-- No chat, login or call hooks. Dedicated, killable AI process. -->
        <activity android:name="org.telegram.ui.NabdhAiActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
        <activity android:name="org.telegram.ui.NabdhAiChatActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
        <service android:name="org.telegram.ui.NabdhAiCoreService"
                 android:exported="false"
                 android:process=":nabdh_ai" />''', "process manifest")
manifest.write_text(xml, encoding="utf-8")

category = ui / "NabdhGramFeatureCategoryActivity.java"
s = category.read_text(encoding="utf-8")
marker = '''        if (featureId == 0 && titleRes == R.string.NabdhIntelligenceTitle) {
            addNabdhPrivacyControls(context, content);
        }'''
s = once(s, marker,
'''        if (featureId == 0 && titleRes == R.string.NabdhIntelligenceTitle) {
            addNabdhPrivacyControls(context, content);
            nabdhV1Button(context, content, R.string.NabdhAiCoreLaunch,
                () -> context.startActivity(new android.content.Intent(
                        context, NabdhAiActivity.class)));
            nabdhV1Button(context, content, R.string.NabdhAiChatLaunch,
                () -> context.startActivity(new android.content.Intent(
                        context, NabdhAiChatActivity.class)));
        }''', "manual intelligence hub launch")
category.write_text(s, encoding="utf-8")

# Pinned current Telegram still needs minSdk 23. Both AI engines are isolated
# behind runtime API+availability checks in a separate opt-in process.
gradle = root / "TMessagesProj/build.gradle"
g = gradle.read_text(encoding="utf-8")
anchor = "    implementation 'com.google.mlkit:language-id:17.0.6'"
g = once(g, anchor, anchor + '''
    // Only invoked in the private :nabdh_ai process after explicit user action.
    implementation 'com.google.mlkit:genai-prompt:1.0.0-beta4'
    implementation 'com.google.mediapipe:tasks-genai:0.10.27'
    // ML Kit beta4 download() requires coroutines 1.11+ (Google known issue).
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0'
'''.rstrip(), "pinned ML Kit/MediaPipe library dependencies")
gradle.write_text(g, encoding="utf-8")

labels = {
    "values": ("NabdhAI Core — on-device inference",
        "Optional local inference with Gemini Nano if ready; verified Gemma fallback on compatible devices. Neither model reads chats without a user request."),
    "values-ar": ("محرك NabdhAI المحلي",
        "استنتاج محلي اختياري باستخدام Gemini Nano عند توفره، أو Gemma بعد استيراد نموذج موثّق على جهاز متوافق؛ لا قراءة صامتة للمحادثات."),
}
for locale, (title, note) in labels.items():
    dest = root / "TMessagesProj/src/main/res" / locale / "nabdh_ai_core.xml"
    if dest.exists():
        raise SystemExit("NabdhAI translated resource collision: " + locale)
    dest.write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <string name="NabdhAiCoreLaunch">' + escape(title).replace("'", "\\'") + '</string>\n'
        '    <string name="NabdhAiCoreStatus">' + escape(note).replace("'", "\\'") + '</string>\n'
        '</resources>\n', encoding="utf-8")
    # A real opt-in chat screen using the same isolated service and local model.
    chatLabel = "AI Chat — private on-device assistant" if locale == "values" else "AI Chat — محادثة ذكاء محلي خاصة"
    xml = dest.read_text(encoding="utf-8")
    xml = once(xml, "</resources>",
        '    <string name="NabdhAiChatLaunch">' + escape(chatLabel) + '</string>\\n</resources>',
        "AI Chat localized launch label")
    dest.write_text(xml, encoding="utf-8")
    # Existing AI preferences had accurately said "not connected" before this overlay.
    # They must not continue showing that statement when providers are now wired.
    prefs = root / "TMessagesProj/src/main/res" / locale / "nabdh_v1_user_features.xml"
    before = ("Local AI models are not yet connected. No chat monitoring, passive learning, secret recording or automatic message reading. Only the explicit settings you choose below are saved."
              if locale == "values" else
              "لم يُوصَّل نموذج لغوي محلي بعد. لا مراقبة للمحادثات ولا تعلم خفي ولا تسجيل ولا قراءة تلقائية للرسائل. تُحفظ التفضيلات التي تختارها أنت فقط.")
    # Don't modify unknown translations silently; status remains guarded in the UI.
    if prefs.exists():
        content = prefs.read_text(encoding="utf-8")
        if before in content:
            prefs.write_text(content.replace(before, note, 1), encoding="utf-8")

print("PASS: private process and opt-in real provider bindings, en/ar routes and pinned deps")
