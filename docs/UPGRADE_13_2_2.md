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

## Hardened upgrade preflight (added for NabdhGram 1.0)

After all Python overlays, before native submodule checkout or Gradle, CI now runs:

```bash
python3 nabdhgram/scripts/check-upstream-api-preservation.py --self-test
python3 nabdhgram/scripts/check-upstream-api-preservation.py Telegram-upstream
git -C Telegram-upstream diff --check
```

The API-preservation gate compares method-declaration counts in 15 high-risk upstream classes from the original pinned Git commit against the modified Java, checks brace/parenthesis/bracket structure, and guards selected login/keypad/session fields. A missing method fails immediately with the source filename. This would catch the `CustomPhoneKeyboardView.setButtonBackground` regression from build #548 before a lengthy javac stage. The gate is **not** a guarantee of runtime compatibility or a replacement for compiler and phone testing.

NabdhGram's footer version is no longer hard-coded: the displayed base Telegram version is generated from the pinned checkout's `APP_VERSION_NAME` and `APP_VERSION_CODE`.

## Telegram Devices identity, 2026-11-13

The developer **confirmed updating the API application App title to NabdhGram** at `my.telegram.org/apps`. This server registration is not a GitHub source setting and no API secret is stored in code.

- Telegram's `authorization.app_name` is server-owned and is shown by **official Telegram**. The client cannot retroactively rewrite old session records.
- The client's `authorization.app_version` derives from the actual Android package version. NabdhGram strips historical duplicate `NandhGram` or `NabdhGram` prefixes; it does not impersonate server `app_name`.
- The screenshot showing `NandhGram 13.1.1` is from an older session. After the developer's change, verify on an authorized **new login** using Telegram official > Settings > Devices; do not terminate existing sessions by automation.
- Preserve the actual `versionCode` and development `beta` suffix; do not substitute the branding string for the API ID or expose the API hash.
- See [#61](https://github.com/alrasby/NabdhGram/issues/61) for external session-name verification.

## Release gating

Work on source-level hardening is tracked under [#64](https://github.com/alrasby/NabdhGram/issues/64) as P0. PR #63 stays a draft until Android APK compilation, signing/artifact checks and **device** regression (login, QR/email when supported by Telegram, chats, Glass, RTL/fonts, themes and icons). Only after those pass should the baseline upgrade be merged. Never automatically merge, force-relogin users or claim that the new external App title changed old sessions.

## Upstream release readiness (source, Android, and device)

The P0 upgrade acceptance matrix and reproducible, non-destructive physical-device
launcher test are documented in [UPGRADE_QA_GATE.md](UPGRADE_QA_GATE.md). CI
must pass *and* a fresh device QA pass must be recorded before merging PR #63.
