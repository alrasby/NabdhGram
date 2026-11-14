# NabdhGram — Telegram 13.2.2 (7303) Release Candidate #575

**Checkpoint date:** 2026-11-14. This is a **test candidate**, not an accepted production release.

## Immutable source and rollback

- Candidate branch: `release-candidate/telegram-13.2.2-575`
- Candidate NabdhGram commit: `e0c569dfe916146f6f5de580ae3c4f261da73fe6`
- Pinned official Telegram commit: `21f7d109da6ab3506c9e9577f98c6a38771ab335`
- Telegram version: **13.2.2 (7303)**
- Candidate pull request: https://github.com/alrasby/NabdhGram/pull/63 (still draft)
- Baseline `main` rollback: `f691d32f953c3ab78875735725baa977308e04af` (Telegram 13.1.1)
- App package: `net.nabdhserv.nabdhgram`
- Android runner build: https://github.com/alrasby/NabdhGram/actions/runs/43568614706 (run **#575**)
- Downloadable experimental debug APK artifact: https://github.com/alrasby/NabdhGram/actions/runs/43568614706/artifacts/14104952678

## Evidence (verified in GitHub Actions)

| Check | Result |
| --- | --- |
| Foundation run #995 | PASS |
| Pinned Telegram overlay preflight run #52 | PASS |
| Android build run #575 | PASS |
| APK packaging / identity / signing checks inside run #575 | PASS |
| Compiled Android day/night branded splash resource checks | PASS |
| Native switch ON thumb physically on the left: generated source | PASS |
| Native switch ON thumb physically on the left: physical-device screenshot | **NOT RUN / NO EVIDENCE** |
| Installation, account login, notifications, messaging, media, calls | **NOT RUN on this exact APK** |
| RTL, Glass, imported themes, fonts, icons, Saved/archived, settings navigation | **NOT RUN on this exact APK** |
| Session name in official Telegram after an authorized NEW login | **NOT VERIFIED** |
| Security, memory and Play Store release signing review | **NOT COMPLETE** |

Artifact availability is time-limited by the GitHub Actions retention policy. The supplied APK is an **arm64 experimental debug build** and must not be marketed or distributed as a stable/public release.

## Manual acceptance required BEFORE merging PR #63 to main

Test the *exact* APK from #575, not #574 or an older build; keep personal chats, OTPs and API credentials out of GitHub artifacts.

1. On Android 12+ cold start with system light/dark and logo changes: approved NabdhGram splash/icon; no Telegram logo.
2. Arabic and English: switch thumb **ON = physical LEFT**, **OFF = physical RIGHT** in Power Saver, Notifications, Chat Settings and NabdhGram settings. Check the row still toggles, persists after restart and keeps its click area.
3. Chat Settings: icon carousel stays inside rounded Glass card under scrolling; 2-/3-line chat-list previews both visible.
4. Repeated Settings -> Account/Privacy/Notifications/Data/Devices/Chats -> back/scroll: no white parent panels, bleeding old screens, duplicate labels, hidden rows or cropped RTL text.
5. Imported and bundled light/dark themes, global Readex Pro and other fonts with instant UI/chat size + weight changes.
6. Chat list pinned/unpinned/archive, Saved Messages, text/file/photo/video/voice bubbles, composer, reply and forwarding.
7. Phone + officially available QR/email login, network recovery, media transfers/resume, notifications and calls.
8. Verify the separate server-owned Telegram API app title in **a newly authorized session**. Never log out working sessions just for CI.

See `docs/UPGRADE_QA_GATE.md` for the full matrix. Record on-device outcomes and APK SHA-256 before changing PR #63 from draft; hard fail for P0 issues. An automated compile passing is not proof of device stability.

## Next stage: v1.0 feature batch

After RC acceptance and stable upstream integration, build one coordinated v1.0 feature branch anchored on this certified baseline, preserving the approved `docs/ROADMAP.md` scope. Distinguish existing working features (Glass, font selector, Privacy Screen, local Context Lens) from planned work (Focus Lens on messages, Message Workspace, Catch Me Up, Safe Link/attachment warnings, Smart Chat Preview, voice/network enhancements). Features are not called complete before integrated functional device tests. Do not merge unrelated stale PRs or fake stubs as shipped functionality.

**Current approval status: BLOCKED on exact #575 physical-device QA. The production main baseline is intentionally unchanged.**
