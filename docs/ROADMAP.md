# NabdhGram — Approved Product Roadmap

> Product principle: **Power inside, simplicity outside** (قوة في الداخل، بساطة في الخارج).
> Scope agreement: 2026-11-06. This is an approved product plan, **not** a claim that features have been implemented or tested.

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
- Arabic RTL and English/localization following system; improve Arabic search and typography where technically feasible.
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

## v1.5 — Advanced intelligence (future)
- Opt-in advanced AI summaries, semantic retrieval, better task/decision extraction.
- More sophisticated scam classification and reduced false positives.
- Smart Alerts / Media Guardian improvements if not completed in v1.0.
- Optional Arabic-aware semantic search and richer File Finder.

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

## Status snapshot
- The upstream unbranded Telegram debug APK has built in GitHub Actions.
- NabdhGram identity build is still being debugged; do **not** describe v1.0 features as implemented.
- Approved icon binaries have not yet been verified as integrated into the APK.
