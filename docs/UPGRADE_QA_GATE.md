# NabdhGram — mandatory upgrade and release QA gate

## Why this gate exists

Telegram 13.2.2's changes to themed RecyclerListView section bitmaps
caused nested settings to paint ghost sections, repeated text and underlying
wallpapers, even though Android build #561 passed. Build success alone is
never a release criterion.

## Source-only overlay preflight (fast, before Gradle)

On relevant pull requests the **Pinned Telegram overlay preflight** workflow runs the same pinned Telegram checkout, every overlay and the generated-Java compatibility guard automatically, without invoking Gradle. To run the same check manually, use the GitHub Actions
**NabdhGram identity debug build** via `workflow_dispatch` with
`source_preflight_only=true`. This runs the exact same pinned-source
checkout, all overlays and the Java API preflight, but **skips** native
submodules, SDK/NDK, Gradle, APK publication and release claims. After
a clean source-only run, use the full build for actual Android verification.

## Source preservation (automatic — before Gradle)

Run `scripts/check-upstream-api-preservation.py --self-test` and then run it
against the pinned, modified Telegram checkout. The check compares **all
tracked native Java files touched by overlays**, plus the high-risk baseline
files, with their immutable upstream originals. It checks method names and
argument arities, class/interface/enum/record declarations, balanced
delimiters, generated Java helpers, and login/session critical symbols.
`git diff --check` is mandatory. All overlay anchors must fail closed on
unrecognized upstream code; the automated Gradle build must also pass.

The source guard is deliberately not a complete Java compiler or guarantee of
runtime behavior. Do not treat its pass as an Android QA pass.

## Device smoke (automatic on a connected physical ARM64 Android device)

After downloading the verified **experimental** APK from GitHub Actions and
installing it with the owner's normal test procedure, run:

```bash
bash scripts/device-smoke-check.sh --expect-version 13.2.2
```

This script **does not install, uninstall, clear app data, log out, read chats,
capture logs, or take screenshots** by default. It checks the package,
launcher resolution, launch result and a live app process. Optional
`--serial DEVICE` picks a device; `--screenshot ./private-qa.png` is
explicitly opt-in and stores potentially sensitive content locally. A
successful script run cannot replace the manual screen and functional tests.

## Human acceptance matrix — record Pass / Fail / Not run

Each item below requires a real Android observation on the newly built APK.
Record Android version, device, APK SHA-256, Telegram pinned commit, result,
and a *redacted* screenshot where appropriate. Keep personal account/session
data off GitHub.

| Area | Acceptance / expected behavior |
| --- | --- |
| Install, app icon, startup | Branded launcher is visible, app opens with no crash, package and version match |
| Main chats | Header actually reads **NabdhGram**, archive/pinned/regular rows align and can scroll |
| Settings navigation | Repeatedly open/back/scroll main settings, Privacy, Notifications, Data, Devices, Folders and Chat Settings: **no ghost content**, doubled labels, disappearing rows or bleed-through |
| Theme switching | Light/dark, imported theme and back transitions retain actual Glass cards, readable contrast, clipped ripple, no static color overriding user's theme |
| RTL and fonts | Arabic/English, Readex Pro / other bundled fonts, size/weight apply immediately including nested settings, mixed Arabic/Latin names and badge alignment |
| Chats, saved/archived | Text/media/voice/file and grouped bubbles, composer, replies/forwards, long text and selection, real touch/navigation |
| Login and devices | Phone, QR and native email flow only when officially available; successful session, Telegram Devices title in a **new** session, no forced logout |
| Media, downloads, calls | Send/receive media, progress/resume, voice, notification taps, microphone and video calls, network recovery |
| Contacts and permissions | No unsolicited contacts permission on initial login; contacts page still opens and explicitly requests permission when needed |
| App icons and login keypad | Original six variants selectable, return to launcher without icon disappearance, circular keyboard and language/proxy controls aligned |
| Privacy & NabdhShield | Privacy Screen and official Telegram protections do not bypass disappearing or read receipts; session data remains safe |
| Stability | Repeated navigation, rotation/back, background/foreground, scrolling, theme toggles without crash, white screen, stale overlays or severe jank |

**Reject upgrade** if any P0 visual overlap, broken login/session state,
unrecoverable crash, missing launcher, privacy violation, or native Telegram
feature regression is observed. Record a clear fix and rerun the affected
row and nearby navigation flows. Existing `main` remains the rollback
baseline until all required checks pass. PRs stay draft until actual device QA
is recorded; never auto-merge just because CI turns green.

## Compatibility governance

Keep the pinned upstream commit immutable within a migration PR. Upstream
version changes go to a new isolated branch; do not patch the existing
production branch in place. Every upstream bump must execute this gate.
Prefer component-level, theme-aware integrations over broad string splices.
When a risky native API change is necessary, review its exact method,
preserve every unrelated native member and add a focused regression check.
Do not bypass the source guard with a wildcard allowlist.

## Main Settings root canvas — P0 Android regression 2026-11-13

The second user video and logs.zip show that main Settings still had
black/dark side rails and remnants of the underlying screen at rest after
scrolling or returning from nested settings. This is not an evident crash.

Modern upstream SettingsActivity uses a SizeNotifierFrameLayout ROOT with
independently drawn camera/avatar/header and an over-scrolling list whose
top/bottom can extend outside normal RecyclerView bounds. A background on
the RecyclerView alone cannot protect those surrounding root layers.
The root must own an **opaque, live-theme** backdrop while the cards remain
translucent. The profile hero uses exactly one horizontal inset, matching
the cards, and the main UniversalAdapter is the sole Glass row painter
(no second ItemDecoration fallback on the main list).

Physical acceptance: open main Settings, scroll avatar to bottom and back,
open Account, Chat Settings, Privacy, Devices, Language, return and repeat,
change light/dark theme, change font, background/foreground and rotate.
No ghost text or dark rails should remain after navigation completes.
A source-level assertion alone cannot certify this until a real APK is
installed and the sequence is repeated.

## V1 combined device acceptance: login, main settings, Account and title

On a newly compiled APK, verify the following together, without clearing
the account or altering Telegram credentials:
- Country/phone fields have one soft rounded fill and **no second border**;
  labels, phone editing, country selection, cursor and validation still work.
- QR button keeps 52dp height and an accessible touch area but is visibly
  narrower and horizontally centered. Open and dismiss the native QR dialog.
- Main Settings and Account scroll, back navigation, light/dark and imported
  theme transitions show **no old-page content**, duplicate account text or
  rectangular opaque white sections. The account hero is a single softer
  Glass surface and has the same horizontal inset as its row cards.
- Home Chats title reads NabdhGram both on first startup and after returning
  from Settings. Telegram FAQ/Premium/Features retain their official names.

These are actual phone QA requirements, not implied by successful source
preflight or Gradle compilation. PR #63 remains unmerged until observed.

## 2026-11-13 screenshot regression — native white sections and Arabic clipping

The white rounded rectangular *parent groups* in main Settings are not
NabdhGram's individual blue Glass cards. Telegram 13.2.2 retains a legacy
section decorator, bitmap section background and UniversalAdapter fallback.
The original source callback nulling was insufficient in all paths. On
main Settings, disable section paint AFTER native
`setSectionsDrawBackground(true)`; guard the final legacy and bitmap
drawing entrypoints only on explicitly opted-in Glass RecyclerListViews;
skip UniversalAdapter white fallback only on opted-in Glass Settings.
Keep native section geometry and adapter content.

The real SettingsActivity.SettingCell previously requested EXACTLY 60dp
for any title with a subtitle even when Arabic text wraps into 3 lines or
when an app-wide selected font expands glyph metrics. Row measurement now
uses AT_MOST with actual child text layouts and native minimum row heights.
No global font/weight is overwritten by the correction.

**Acceptance on Android:** in Arabic with Readex Pro and enlarged fonts,
open Settings at top, scroll through all grouped cards and to Debug. There
must be **zero broad white parent backgrounds** behind blue row cards.
Descriptions can use two or more lines but cannot overlap adjacent cards
or become clipped by fixed 60dp height. Repeat in English, light/dark and
imported themes. Validate on the actual new APK and record screenshots
before merging PR #63 into main. Passing source tests alone is insufficient.

## Android #566 typography regression (2026-11-13 user video)

The 128-second user QA recording confirms #566 runs and navigates, but is
**not release approved**. The normal chats header STILL displays "Telegram"
visually although source asserts NabdhGram. New Appearance/Intelligence/
Privacy pages become excessively bold and wrapped after the global Bold
option is toggled. The clip does NOT cover switching all three Liquid Glass
presets or directly using the composer Lens, so those remain untested.

The first scoped source correction preserves user-selected font family and
size but tags only secondary explanatory TextViews with
`nabdh:secondary-text`; the global font walker preserves the native
weight on those text blocks while Bold continues to apply to headings and
ordinary labels. Do not override the user's entire font preference or
truncate body text to hide overlap.

Before release: reopen Chats after full process restart and theme/language
changes and confirm visible NabdhGram title. Investigate the **runtime**
title owner rather than relying on the presence of a string in
DialogsActivity source alone; the existing source-only test had a false
sense of UI coverage. Validate normal/Bold font, smallest and largest UI
scale, long Arabic help text, actual scroll/touch/hit regions and the three
bubble presets on a real device. Do not post or upload QA screens that
contain personal chats or one-time login codes.
