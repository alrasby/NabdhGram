# Nabdh Liquid Glass + Nabdh Intelligence — V1 integration contract

## Visual engine (implemented in this PR)

- Reuse native Telegram MessageDrawable text path, chat wallpaper sampling,
  theme colors, native transitions, message grouping and tail geometry.
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
