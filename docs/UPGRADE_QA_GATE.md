# NabdhGram — mandatory upgrade and release QA gate

## Why this gate exists

Telegram 13.2.2's changes to themed RecyclerListView section bitmaps
caused nested settings to paint ghost sections, repeated text and underlying
wallpapers, even though Android build #561 passed. Build success alone is
never a release criterion.

## Source preservation (automatic — before Gradle)

For an inexpensive migration sanity check, run the GitHub Actions
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
