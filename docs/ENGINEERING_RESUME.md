# NabdhGram — verified engineering resumption checkpoint

**Updated:** 2026-11-13, source-hardening track. This file deliberately
distinguishes **proved** results from Android checks that are still pending.

## Branches and builds

- Production `main`: proven pre-upgrade PR #58 baseline at
  `f691d32f953c3ab78875735725baa977308e04af`,
  Telegram 13.1.1 (7237). **Do not overwrite until P0 QA passes.**
- Telegram 13.2.2 (7303) draft [PR #63](https://github.com/alrasby/NabdhGram/pull/63),
  pinned upstream `21f7d109da6ab3506c9e9577f98c6a38771ab335`,
  latest source fix at `2fe32562c6d4755ff46842be0c2736cc23f5e85f`.
  #561 compiled, but device video exhibited severe ghost section text and
  overlapping settings. `2fe3256` targets themed opaque page canvases
  and Telegram 13.2 bitmap section fill conflicts. Foundation #931 passed.
  Android [#562](https://github.com/alrasby/NabdhGram/actions/runs/43396554358)
  was in progress when this checkpoint was written.
- Hardening draft [PR #65](https://github.com/alrasby/NabdhGram/pull/65)
  is **based on PR #63's branch** (not main), separate while #562 runs.
  The hardening branch is `hardening/upstream-api-and-device-gates`.
  Its Foundation source checks, Git-fixture tests and fake-ADB tests passed
  in [#43400559904](https://github.com/alrasby/NabdhGram/actions/runs/43400559904)
  and [#43400567360](https://github.com/alrasby/NabdhGram/actions/runs/43400567360).

## Hardening files

- `scripts/check-upstream-api-preservation.py`: scan all modified upstream
  Java classes + critical baseline, check removed files/types, overload arities,
  generated Java and current key-field invariants; include disposable Git and
  lexical self-tests.
- `scripts/device-smoke-check.sh`: optional physical-device install-state,
  launcher, startup and live-process smoke (no install, deletion, session changes,
  logcat or screenshots unless explicitly requested).
- `scripts/test-device-smoke.sh`: isolated mock-ADB success/error tests.
- `.github/workflows/foundation-checks.yml`: syntax and smoke unit checks.
- `docs/UPGRADE_QA_GATE.md`, `docs/UPGRADE_13_2_2.md`: mandatory
  source/build/device acceptance and rollback plan.

## Unresolved blockers — DO NOT CLAIM RELEASE READINESS

1. **#562 full Android compilation and artifact verification** must finish
   successfully. Do not update the PR #63 upgrade branch while #562 runs:
   concurrency cancels the previous run and wastes the compilation.
2. Once #562 completes, integrate **PR #65 into PR #63 upgrade branch**
   (never directly to main), then run the **expanded live-upstream preflight**
   and full Android build. Foundation-only tests cannot prove compatibility
   with all ~40 applied overlay scripts and the pinned upstream revision.
3. Test the resulting APK on a physical Android device, using
   `docs/UPGRADE_QA_GATE.md`. The prior video demonstrated **P0** layered
   settings bleeding/ghosting, and the main header still showed
   **Telegram** despite the source assertion. Confirm fixes by real video;
   do not mark them resolved from code review alone.
4. Check phone/QR/email as officially supported, chats and notifications,
   media, calls, Arabic/RTL and immediate fonts, imported themes, icons, and
   Telegram's new session registration title. A new server-owned session
   title needs real authorized external confirmation.
5. Leave #63 draft and main unchanged until source checks, full APK build,
   and all P0 device QA are actually passed. Track [#64](https://github.com/alrasby/NabdhGram/issues/64).

**Important:** A successful compiler does not prove a stable app, and this
document does not certify zero future upstream regressions. Its purpose is
to make each future upgrade detectable, reviewable and reversible.

## Android video follow-up (13:42, Nov 13)

Root cause: main Settings SizeNotifierFrameLayout had no opaque canvas
after suppression of Telegram 13.2 section fills. The earlier nested
RecyclerListView canvas didn't cover independent avatar/header layers or
overscroll. PR #65 source change adds the root canvas, removes redundant
main-only ItemDecoration and avoids doubled hero insets. User supplied
logs.zip contained no explicit FATAL EXCEPTION for this visual bug.
Android build #562 completed success, but this new root fix still needs
a fresh preflight/build and physical-device regression. Do not equate
successful CI with a fixed visual until demonstrated on the device.

## V1 login / Account / title follow-up (2026-11-13)

Branch `fix/v1-login-settings-account-branding` derives from PR #63.
Changes: remove duplicate phone/country background; retain floating labels
but skip three native outline strokes only on login country/phone;
shrink QR horizontally without changing 52dp height; fix Account page's
missing UniversalFragment root background and disable native white row fills;
avoid redundant account row decoration; soften the hero; brand real
`AppName` resources and restore main Chats title on resume.
Source contracts and generated-Java checks are added; a full device build
and real on-device pass are required before merging into production.

## Main settings screenshot — white group backdrop / Arabic row truncation

Source patch on `fix/settings-sections-arabic-text-v1`: add Glass-only
guards in both RecyclerListView group draw entrypoints and UniversalAdapter
white-section fallback; move main Settings `nabdhHideSectionBackgroundOnly`
opt-in AFTER `setSectionsDrawBackground(true)`. Replace SettingsActivity
SettingCell's EXACTLY-60dp described rows with measured content plus
original height minima (bounded maximum). Add generated Java invariants.
Must pass real pinned Telegram overlay preflight and merged APK build,
then demonstrate a real Arabic screenshot with no white group slabs or
clipped subtitles. Existing `main` remains unchanged.

## 2026-11-14 — Android #572 night splash and Profile bio P0

Confirmed by real packaged APK #572 resource table (not only source):
`Theme.TMessages.Start` day-v31 = NabdhGram foreground, night-v29 =
`tg_splash_320`. The missing night-style patch is added on
`fix/night-splash-bio-and-upgrade-gate`. A mandatory APK binary
resources.arsc verification now checks every day/night style variant.
User screenshot shows 12dp white line under Profile bio, sourced from
`AboutLinkCell.bottomShadow` manual draw; new scoped Glass flag removes
this overlay without altering links or general cells.

Required next: Foundation + pinned Telegram preflight on the new branch;
merge only to draft PR #63 after green checks; full Gradle APK then
inspect final resource configurations and UI on an Android device.
Never claim final device reliability from source/compiled tests only.
`main` still unchanged.
