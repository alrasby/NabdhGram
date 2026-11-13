# Telegram 13.2.2 (7303) — isolated upstream migration checkpoint

- Last verified NabdhGram baseline: Telegram 13.1.1 (7237), upstream `3de37c8cfb039452be7398909461da6288babf15`.
- Target: official DrKLO/Telegram commit `21f7d109da6ab3506c9e9577f98c6a38771ab335` (2026-11-12).
- Source: https://github.com/DrKLO/Telegram/commit/21f7d109da6ab3506c9e9577f98c6a38771ab335
- Comparison: https://github.com/DrKLO/Telegram/compare/3de37c8cfb039452be7398909461da6288babf15...21f7d109da6ab3506c9e9577f98c6a38771ab335
- Observed upstream difference: 27 commits; the GitHub compare API exposes at least 300 changed files. Java views, native modules, Gradle and submodule references are affected.
- NabdhGram PR #58 merged into `main` at `f691d32f953c3ab78875735725baa977308e04af`; build #532 and Foundation #870 passed for that *older* baseline.

## Required release gate

1. Clone and validate immutable target including Git submodules.
2. Re-apply each overlay, fixing changed anchors in the relevant scripts only; preserve design and native authentication behavior.
3. Run checks and full Android Gradle build; confirm package `net.nabdhserv.nabdhgram` and APK artifact.
4. Test original settings/Glass and Arabic font switching; verify phone/email/QR login, chat, calls, notifications, downloads, media, icon switching, privacy and imported themes on Android.
5. Only after compatibility passes: merge this migration PR and integrate the approved v1.0 scope as one coordinated release batch.

**Status**: migration candidate; no compatibility/build/device success is claimed merely by updating `upstream/TELEGRAM_COMMIT`. Main remains at the previously verified baseline until testing passes.
