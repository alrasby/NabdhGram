# NabdhGram | نبض جرام

Independent Telegram Android client by NabdhServ, with the approved NabdhGram
branding, Glass UI and localization. Not affiliated with Telegram.

## Current stable source baseline

- Telegram Android **13.2.2 (7303)** pinned to an exact upstream commit.
- `main` was promoted after passing Foundation, pinned overlay/source API
  preservation, full Android build and owner-reported on-device installation.
- Android Debug APK builds are reproducible from
  [GitHub Actions](https://github.com/alrasby/NabdhGram/actions).
  **A Debug APK is not an owner-signed public Release.**
- Source architecture applies focused overlays to the pinned official Telegram
  repository, retaining upstream message transport, account, login, privacy and
  deletion behavior.

## v1 feature integration branch

`release/v1-feature-integration-and-signing` is a **work-in-progress** batch:

- Existing tested foundation: NabdhGram identity, themed Glass, font selection,
  icon variants, supported Telegram auth flows, Privacy Screen, on-demand local
  Context Lens, native Telegram translation and playback controls.
- New, opt-in source: local Focus extraction for explicit text, manual pasted
  excerpt recap, offline URL warning signals, encrypted on-device notes.
- Not yet complete or accepted as a public V1: integrated message-source
  Workspace and deep links, actual unread chat digest, pre-open file scan,
  expanded Smart Chat Preview and Voice Clarity processing, advanced Network
  Intelligence and final multilingual/privacy/device release QA.
- Detailed status and acceptance criteria:
  [V1 feature acceptance](docs/V1_FEATURE_ACCEPTANCE.md).

## Signed Release safety

An independent, **manually triggered main-only** signed Release workflow is
prepared but requires project-owner Android release signing/Firebase credentials.
It fails closed rather than using Telegram's bundled demo keystore. Read
[release signing](docs/RELEASE_SIGNING.md). A Release signed by a different key
cannot be installed on top of the earlier Debug APK with the same app package.

## Attribution

Upstream: https://github.com/DrKLO/Telegram.
Keep the source, GPL obligations, third-party notices and privacy policies under
review before any public distribution. Never commit signing keys, API hashes,
private message content or Firebase configuration.
