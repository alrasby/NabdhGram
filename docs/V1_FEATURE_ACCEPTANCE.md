# NabdhGram V1 — implementation and acceptance checkpoint

**Date:** 2026-11-14. **Branch:** `release/v1-feature-integration-and-signing`.
The **verified upstream stable source** is `main` at Telegram 13.2.2 (7303);
this feature batch must not be publicly released before its own build and QA.

## Existing baseline and user-tested foundation

The prior 13.2.2 upgrade passed GitHub Foundation/source checks/Android #578,
and the owner confirmed a fresh install and phone tests of that build.
The approved brand/logo, themes/Glass, Arabic UI and font controls, optional
Privacy Screen, native proxy, Telegram-supported sign-in, local composer
Context Lens, native Telegram AI/translation/transcription remain preserved.
This says nothing about new V1 tools until their APK is compiled and tested.

## Integrated in this feature branch (requires native/phone QA)

| Feature | Current implementation | Release state |
| --- | --- | --- |
| Focus Lens | Opt-in explicit-text local task/question/date/decision signals, no background chats | New source / awaiting APK + device |
| Catch Me Up | **Manual pasted-excerpt** extraction; no unread group history access or LLM | Partial, not full approved behavior |
| NabdhShield Safe Link | Opt-in local URL risk hints: HTTP, userinfo, punycode, IP host, executable disguise | Partial: no pre-open file interception or real malware/known-bad database |
| Message Workspace | User-chosen local draft notes with AndroidKeyStore AES-256-GCM, copy/delete | Partial: no links back to source Telegram messages |
| Lens | Existing manual composer/context dialog extended with above local actions | Needs device checks |
| Release | Full `assembleAfatRelease` pipeline, Firebase + owner certificate pinned; main-only manual | Prepared; no valid private signing inputs verified and no Release APK produced |

## Not yet integrated as complete V1

- **Smart Chat Preview:** the official Telegram-native modal preview is ALREADY visible in the owner's installed screenshot; pinned DialogsActivity.showChatPreview opens ChatActivity through presentFragmentAsPreviewWithMenu and provides a separate explicit markAsRead(dialogId) action. Preserve the existing preview; do not duplicate it or claim custom implementation. Verify unread count AND server read acknowledgements stay unchanged from preview until the user marks read or opens chat normally.
- **Voice Clarity:** tested DSP / playback-quality and level processing, not just
  relabeling native speed controls.
- **Network Intelligence:** actual intelligent and persistent Wi-Fi/mobile
  caching/transfer behavior and functional tests; current network diagnostics
  are diagnostics only.
- **NabdhShield file guardian:** inspect downloaded bytes for MIME/extension
  discrepancy *before* Telegram opens a file, honor SAF/URI permissions,
  add false-positive controls, and test malicious/benign samples.
- **Catch Me Up live unread summaries, Focus links to source messages, and
  message-linked Workspace:** deep linking and correct read/secret-chat/privacy
  behavior must be verified on actual Telegram message objects.
- **Localization** full product copy, RTL Persian/Urdu, accessibility, security
  disclosures, opt-in/no leakage under background or secret chats.

## Feature-level tests

- Java host tests for Focus/recap/URL parser limits, Arabic questions/decisions,
  non-generative claims and failure boundaries.
- Source preflight verifies actual generated `NabdhV1Engine`,
  `NabdhWorkspace`, category actions and Arabic/English Android resources.
- Workspace device tests: Android 23–36, encryption/decryption, restart,
  tamper/backup key failure, limits, clipboard, explicit delete, no plaintext
  prefs or logs.
- Context Lens device tests: Arabic/English mixed scripts, manual save/view,
  no automatic background reads, secret-chat exclusion, low memory.
- Release checks: exact package, non-debuggable, signature SHA-256 match,
  native ABI list, Firebase notifications, Android launch, Play/license/privacy.

## Merge requirements

1. Foundation, pinned source overlay and Android Debug compile on this **branch**.
2. Real-device regression of all new features AND preexisting chats, media,
   keyboard, fonts, themes, links, notifications and logcat.
3. Owner-only release signing/Firebase secrets from
   `docs/RELEASE_SIGNING.md`, followed by **successful signed Release build**.
4. Release signer certificate retained for future upgrades; test fresh install
   and signing continuity separately from existing debug installs.
5. Finish incomplete v1 signatures or transparently scope a smaller version;
   do not claim this partial feature batch is a completed v1.0.

This document is an engineering checkpoint, not public feature marketing.
