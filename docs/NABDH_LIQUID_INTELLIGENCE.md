# Nabdh Liquid Glass + Nabdh Intelligence — V1 integration contract

## Visual engine (implemented in this PR)

- Reuse native Telegram MessageDrawable text path, chat wallpaper sampling,
  theme colors, native transitions, message grouping and tail geometry.
- **Implementation technique:** Material 3-inspired shape/contrast and
  restrained liquid-glass-style highlights, authored in our own Java painter;
  no Apple assets or proprietary blur implementation. A 128dp theme-aware
  light-gradient shader is cached per style/accent and translated over native
  bubble bounds, instead of being recreated during list scrolling.
- Three persistent style presets: **Soft Glass** (low contrast rim and no
  highlight), **Liquid Glass** (balanced rim and specular), **Crystal Glass**
  (higher contrast rim and highlight). Default is Liquid Glass. Full-screen
  rendering, dynamic blur per message and Compose replacements are forbidden.
- Reuse existing cached/frosted wallpaper calculation; no new bitmap or
  offscreen allocation per draw. Media, theme preview, selection and
  crossfade keep upstream behavior. Existing imported Telegram themes and
  user bubble radius remain respected.
- Appearance settings are on the existing NabdhGram Settings > Appearance
  page. User choices are stored locally and can be reversed without account
  modification. Glass preview requires real-device QA across Android versions.

## Intelligence layer (implemented in this PR)

- Preserve the **official Telegram AI Editor** (short tap on editor icon).
  On **long press** in an ordinary chat, offer opt-in **local Context Lens**.
  The local workflow NEVER sends messages, scans background conversations,
  or transmits text; it receives only the current composer text explicitly
  submitted by the user.
- Local actions: short extractive preview (not an LLM summary), explicit task
  phrase extraction, URL heuristic flags (not malware detection), reversible
  spacing/punctuation cleanup, and honest directions to native Telegram
  translation and transcription when available. Results appear in a dialog.
  Only the user can copy a result or replace their draft; no auto-send.
- In NabdhGram Settings > Nabdh Intelligence the user can enable/disable
  short-text Lens access and test local tools with text entered in the
  category screen. Never store that sample in logs or analytics.
- No new network APIs, paid services, downloadable models, login bypass,
  permissions, automatic scanning, background service or cloud secrets.

## Not falsely represented as complete

- Generative summaries, original voice STT model, cross-chat semantic vector
  search and real malware/virus scanning are **not** bundled. Telegram's
  own AI Editor, translation and transcription remain native features subject
  to their actual availability and privacy terms. Claiming our heuristic
  utilities are an LLM or antivirus would be inaccurate.
- Optional future models require explicit model selection, verified
  licensing/distribution, hardware and memory budgets, user consent for any
  data egress, secure handling of secret chats and an Android-device benchmark.
- The Visual QA Agent is tracked in issue #68; this PR does not create a
  misleading AI pass from static code checks.

## Release and regression gates

1. Foundation unit/AST/contract checks pass, including the Lens privacy
   guard and three visual style preferences.
2. Pinned Telegram upstream overlay preflight runs the exact native Java
   generation and checks before Gradle; no method/type/API loss.
3. Full Android debug build completes on the consolidated upgrade branch;
   APK package/name/icon are verified.
4. Owner tests SOFT / LIQUID / CRYSTAL with incoming/outgoing, groups,
   replies, media, saved/archived, selection, gradients, imported themes,
   light/dark and Arabic/English. Confirm no visible jank under scrolling
   and that transitions, readability and battery consumption remain sound.
5. Confirm the Context Lens works on long-press, its output cannot send
   without explicit user action, secret chat AI controls remain protected,
   and the native AI Editor still works normally.
6. PR #63 remains a draft and is not merged into `main` until previous P0
   Settings white-background/Arabic-clipping issues are also device verified.

**Verified tests belong in GitHub Actions.** This document alone is not a
statement that the Android APK is stable or that all AI features are complete.

## Real on-device ML capability — language identification

Telegram's pinned Android source already declares `com.google.mlkit:language-id:17.0.6`.
Context Lens now offers **Detect language (on-device ML)**, uses that
existing pre-bundled trained Google ML Kit model on up to 512 characters
of explicitly supplied text, asynchronously returns a BCP-47 language
tag, and closes the classifier after completion. The model does not send
text to NabdhGram servers. Unlike our heuristic summaries/tasks, this
specific action **does use an actual pretrained machine-learning model**.
ML Kit may report SDK metrics to Google; review privacy disclosures and
Google terms before any public Play Store release.

On-device **translation models** are not installed yet: ML Kit's
`translate:17.0.3` needs an explicit model download (typically tens
of MB) plus Google Translate attribution and model lifecycle handling.
The existing native Telegram translation/transcription features remain
available under their own availability and privacy terms. Google ML Kit
GenAI embedding/speech agents released in October 2026 require Kotlin
2.3+, which is not a safe blind upgrade of this Telegram-native
Java/Gradle codebase. Do not label those capabilities as integrated.

Test the language action with Arabic, English, mixed-script and unknown
short texts, then exit the dialog during an in-flight async call.
