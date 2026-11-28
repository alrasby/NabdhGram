# NabdhGram — Approved Product Roadmap

> Product principle: **Power inside, simplicity outside** (قوة في الداخل، بساطة في الخارج).
> Scope agreement: 2026-11-06. This is an approved product plan, **not** a claim that features have been implemented or tested.

## 2026-11-15 extension to the approved roadmap

The owner requested an ongoing optional on-device AI capability and additional
customization, privacy and media features. This is an **expanded product scope**,
not evidence of implementation, and must not silently weaken the existing
v1 acceptance gates. See [NabdhAI and feature rollout](NABDH_AI_ROLLOUT_AR.md).
NabdhGram's settings should follow the same **relative sequence** as the
matching native Telegram categories, avoiding duplicate Telegram screens.
The new AI integration is not shipped yet.

## Core principles
- Deliver real everyday user value; do not duplicate features simply because other Telegram clients offer them.
- Familiar, fast, uncluttered Telegram experience. Put features in contextual actions, not unnecessary tabs or buttons.
- Local processing by default where practical; opt-in for sending private content to external AI/security services.
- Never bypass Telegram server-side authentication, message deletion, read-receipt or platform rules.
- Maintain official Telegram upstream compatibility and Google Play / license / privacy compliance.
- Security checks are risk signals, **not** guarantees that files or links are safe.
- Freeze v1.0 scope. Future ideas belong in later releases unless explicitly re-approved.

## Foundation / pre-release build milestones
- [x] GitHub repository, source checkout workflow and pinned official Telegram Android revision.
- [x] Baseline upstream Android debug build succeeded in CI (unbranded Telegram).
- [ ] Successful independently packaged NabdhGram debug APK and real-device installation.
- [ ] Apply exact approved user-supplied icon (do not redraw), all required Android icon densities, and NabdhGram label.
- [ ] Distinct package identity (planned: `net.nabdhserv.nabdhgram`; debug `.beta`), safe API credentials and signing.
- [ ] Verify Telegram sign-in, messaging, notifications, media, calls, and Android compatibility.
- [ ] Security, performance, legal/licensing and Google Play compliance tests.

## v1.0 — First public release (approved scope)

### A. Authentication, onboarding and accessibility
- Email login code flow **when Telegram server offers it**, alongside supported code-to-existing-session, QR, passkey, SMS or calls as applicable. Email recovery is not necessarily login email.
- Explain SMS non-delivery, resend timers and official alternatives; cannot bypass Telegram's server-imposed SMS/Premium payments.
- **Multilingual by design from v1.0:** inherit Telegram's supported interface languages and language packs; follow system language by default, with an independent in-app language override. NabdhGram-specific strings are fully reviewed in Arabic and English at launch, with other translations added and tested progressively and English fallback for missing keys. RTL must be tested (Arabic, Persian, Urdu), and Arabic search/typography improved where technically feasible.
- Interface language and message translation target language must be independently configurable. See [Localization Architecture](LOCALIZATION.md).
- Clean, accessible onboarding and settings.

### B. Identity and personalization
- Exact approved NabdhGram icon and brand, with optional app icon switch when supported.
- Glass-style themes, light/dark/dynamic colors, in-app font selection, practical theme customization.
- Rich but **organized** customization, without cluttering the chat interface.

### C. Four integrated productivity and safety signatures
- **Focus Lens:** extract important messages, dates, questions, links, files, and decisions with links back to originals; start with transparent local rules.
- **Message Workspace:** turn messages into local notes, tasks, and reminders; link back to source messages.
- **Catch Me Up:** summarize missed conversations/group activity; basic local/rule-based capability first, with optional advanced AI later.
- **NabdhShield:** combine Safe Link Preview, downloaded-file checks before opening, and scam-warning signals. Detect misleading extensions vs file signatures, executable/APK masquerading as documents, suspicious domains, and common OTP/payment impersonation patterns. Known-bad hash lookup only with suitable trustworthy data. Local-first, consent for external lookups, false-positive controls, no blanket safety claims.

### D. Privacy and messaging
- **Smart Chat Preview:** modal chat preview with no unintended marking as read; optional explicit mark-as-read consistent with Telegram rules.
- **Privacy Screen:** blur sensitive content in Android recents/background previews.
- Local chat lock/passcode when technically feasible; never circumvent Telegram message deletion or self-destruct rules.
- Deleted-message handling only in compliant ways; no recovery of messages against server-side deletion intent.
- Built-in proxy support consistent with Telegram rules.

### E. Communication, media and network
- In-chat translation and optional live translation subject to available engines and privacy choices.
- **Voice Clarity:** useful voice playback clarity/level controls, evaluated for quality and battery impact.
- **Network Intelligence:** configurable Wi-Fi/mobile auto-download, caching, media and storage controls.
- Faster media transfers only through allowed client-side improvements, not bypassing Premium limits.
- Smart Alerts and Media Guardian are candidates for small scoped enhancements if v1.0 schedule permits; no uncontrolled scope expansion.

### F. Optional AI and user trust
- Any external AI processing must be opt-in and explicit about what data is shared.
- Clear user-facing explanations for security warnings and automation actions.
- Test stability, privacy, resource consumption, Arabic usability, and performance before release.

## First post-v1 update — Smart View contextual chat lock (planned, not shipped)

- **Owner request (2026-11-17):** Add **«قفل المحادثة»** as an action in the
  **Smart View** context menu opened by **long-pressing a conversation** in the
  chat list, alongside the existing folder, read/unread, pin, mute and delete
  actions. Do not add a new persistent button or clutter the chat list.
- For an already locked chat, show **«إلغاء قفل المحادثة»** in the same position,
  with a clear lock/unlock icon and accessible Arabic/English labels.
- Reuse **NabdhChatLock** and its existing PIN verification, protected-list
  storage, notification-content suppression and secure-window handling.
  Unlocking must require authenticated authorization; a long-press must
  never bypass the PIN or reveal private message content.
- Keep Telegram's native Smart View/chat-list behavior, gestures, RTL, themes,
  navigation, unread counters, pin/mute/delete controls and secret-chat
  limitations intact. A long press alone must not mark the chat as read.
- **Acceptance before shipping:** test long press → lock → PIN protection →
  notification redaction → long press → authenticated unlock, after app restart
  and when switching accounts. Check Arabic/English, light/dark Glass themes,
  talkback/accessible touch targets, and regression of all existing menu actions.
- **Scope:** This is a roadmap item for the **next update after first release**.
  It is not implemented by this document and must not delay the current
  owner-signed v1 / Google Play internal-testing gate.

## v1.5 — Advanced Intelligence & Productivity (approved 2026-11-24)

Owner approved all fifteen workstreams below. This is planned scope, not implementation or test evidence. Preserve v1.0 acceptance gates and existing functionality; extend native Telegram capabilities rather than duplicate them.

| # | Workstream | Approved scope |
|---|---|---|
| 1 | Nabdh Translate | Incoming/outgoing and conversation translation, language detection, independent target language, optional offline engines where permitted. |
| 2 | Nabdh Forward Pro | Multi-recipient forwarding, permitted source hiding, caption editing and scheduled forwarding; respect protected content. |
| 3 | Nabdh Download Center | Pause/resume, priorities, categories, duplicates, storage and history. |
| 4 | Nabdh Smart Contacts | Favorites, encrypted local notes, categories and follow-up shortcuts. |
| 5 | Nabdh Smart Search | Arabic-aware search, date/sender/file filters, in-chat search and richer File Finder; semantic retrieval subject to compliance review. |
| 6 | Nabdh Smart Reminders | Reply/chat reminders, snooze, recurrence, unified center and contextual chat-card actions. |
| 7 | Nabdh Privacy Center | Locked chats, notification previews, sessions, permissions and recents protection. |
| 8 | Nabdh Smart Replies | Custom quick replies, templates, text shortcuts and categories without mandatory AI. |
| 9 | Focus Lens 2.0 | Local rule-based extraction of dates, questions, links, files, tasks and decisions with source navigation. |
| 10 | Message Workspace | Notes, tasks, checklists, deadlines and source-message links. |
| 11 | Catch Me Up | Local rule-based unread activity digest, mentions, replies and important updates. |
| 12 | NabdhShield 2.0 | Suspicious links, pre-open file checks, misleading extensions, scam signals, trustworthy permitted hash sources and reduced false positives. |
| 13 | Voice Clarity | Playback clarity, leveling, noise reduction, speech enhancement and speed controls. |
| 14 | Media Guardian | Metadata privacy, optional location removal on sharing, cache and duplicate management, local media privacy. |
| 15 | Network Intelligence | Allowed transfer optimization, data controls, connection-aware downloads, caching and background battery efficiency. |

### Delivery sequence
1. Translate, Forward Pro, Smart Replies.
2. Download Center, Smart Search, Smart Contacts.
3. Smart Reminders, Focus Lens, Message Workspace, Catch Me Up.
4. Privacy Center, NabdhShield.
5. Voice Clarity, Media Guardian, Network Intelligence.
6. Regression, security, performance, physical-device testing and signed release.

Smart Alerts remains in scope through contextual notifications and reminders. Preserve Arabic/English and RTL, native UI integration, accessibility, local-first privacy, and no mandatory paid services. Hide unfinished features. Verify existing native capabilities before implementation; respect Telegram API, licensing and Google Play rules. Measure memory, battery, responsiveness and false positives where applicable. No feature is shipped until tested in a downloadable build.

### NabdhAI — deferred independent research
Owner explicitly deferred NabdhAI on 2026-11-24 to study a distinctive, correct implementation. Retain the research scope (advanced AI summaries, semantic retrieval, task/decision extraction and optional on-device models), but exclude AI-dependent functionality from mandatory v1.5 release gates until separately approved. Keep unfinished AI UI hidden. Local execution alone does not establish Telegram API compliance; review applicable terms, data permissions, privacy, licensing, model quality, device compatibility and resource costs before implementation. Do not remove existing approved research plans or claim AI is shipped.

## v2.0 — NabdhTools (future; **not v1.0**)
- Extract still images from video; trim and compress video; extract audio.
- Merge, split, reorder PDF pages; combine images into PDF.
- Resize/compress/convert images and remove sensitive metadata before sharing.
- Contextual actions within media/document menus; process on-device where practical.

## v2.5 — Professional productivity and media tools (future)
- More capable video editing and joining, audio editing/combining, advanced file management.
- Unified File Finder across permitted locally available content and chats.
- Additional document/asset workflows chosen from real user demand.

## v3.0 — Next generation (exploratory)
- Optional personal assistant for organizing permitted chat information and tasks.
- Useful local automations and deeper integration between NabdhShield, productivity and media.
- Final scope driven by user feedback; no premature commitments.

## Release conventions
- Major versions: substantial, tested user value.
- Minor versions: complete smaller improvements.
- Patch versions: fixes, security and stability.
- Telegram upstream security/compatibility updates are not held back for a major release.
- No feature is called shipped until implemented, tested and included in a downloadable build.

## Development sequence
1. Independent identity APK and working Telegram login.
2. Exact icon, localization, themes and baseline privacy.
3. NabdhShield local-first protections.
4. Focus Lens, Message Workspace, Catch Me Up, Smart Chat Preview.
5. Translation, voice, network and storage refinements.
6. Security/performance/regression tests, beta feedback, stable release.

## v1.0 acceptance snapshot

The [owner-signed Release run #11](https://github.com/alrasby/NabdhGram/actions/runs/46065138487)
produced the signed APK and the Google Play upload AAB from
`235681903985f077dc2a9da24d22df54262a5fe4`. That run includes Android
validation for its own revision. Google Play acceptance and physical-device
QA require separate evidence.

| Scope | Implementation evidence | Open acceptance checks |
|---|---|---|
| A — Sign-in and languages | Pinned Telegram login and language settings, separate translation preference, NabdhGram Arabic and English resources | Server-offered login routes, native QR and session recovery on a phone, Persian and Urdu RTL, TalkBack, system/app language selection, independent translation target |
| B — Identity and personalization | Verified app identity and launcher resources in Release, four bundled themes, native theme and font controls | OEM launcher variations, user theme restoration on device, large text and contrast across themes |
| C — Productivity and safety | [V1 integration branch](https://github.com/alrasby/NabdhGram/pull/115) with contextual Focus, linked notes/tasks/reminders, on-demand cached unread digest, and local header warnings in the external-viewer path for downloaded chat documents | Source-message navigation, task round trip and account isolation, reminder delivery, unread counters, warnings and actual viewer handoff on Android |
| D — Privacy and messaging | Native chat preview and proxies, NabdhGram local PIN and recents controls | Verify read receipts from a second session, protected content during app switching, notifications, deletion and self-destruct behavior |
| E — Media and network | Native translation, download, cache and proxy controls, opt-in voice gain | Phone tests for calls, media and audio quality, battery, Wi-Fi/mobile transitions and background delivery |
| F — User trust and Release | Signed APK/AAB tooling and evidence in Actions, NabdhAI remains deferred | Compare memory, battery and stability against the prior Release on a physical device. Review Play declarations and licensing before distribution |

The first Android acceptance pass should cover a fresh install and a signed
upgrade, with the device/Android version and the exact commit recorded in
the results. See the [device acceptance cases](V1_RELEASE_QA_2026-11-16_AR.md)
and [Play Console acceptance requirements](V1_PLAY_INTERNAL_TESTING_AR.md).
