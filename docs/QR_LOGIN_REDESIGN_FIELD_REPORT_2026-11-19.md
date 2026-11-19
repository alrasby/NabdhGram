# Login / QR field test — 2026-11-19

Observed directly in the 15.39-second Samsung Android screen recording:
- QR dialog **does open**, with an empty 248dp QR image region.
- Status remains "Requesting a secure code…" during the captured recording.
- The recording does not show a successful token, error code or crash.
- The older phone page places the long QR button above the number field, crowding the layout.
- The floating continuation control uses Telegram's bright blue circular visual.
- Digit touch targets/circles are compact; delete icon already uses the theme accent.

## Changes on this branch
- Include PR #97's server `updateLoginToken` acceptance handling (originally not merged).
- Move QR action to immediately **below** the phone number field, 48dp height, and label it "Log in via QR Only" / "الدخول عبر QR فقط".
- Use the app theme primary accent for the continuation circle gradient and the back navigation arrow; keep all existing native click/animation and verification handlers.
- Slightly enlarge numeric circles by reducing inner gutters, draw the key pressed surface using the **exact** current theme accent, and retain readable number/letter labels.
- Make an unavailable QR service **visible** rather than indefinite: one bounded 20-second watchdog cancels the pending request, invalidates stale response generations, and displays an actionable bilingual network/proxy/retry message. No infinite automatic retries. QR image bitmap errors are recorded through existing error logging without leaking the token.
- Keep official Telegram API credentials, login flow, SMS/email and server rate limits untouched.

## Scope / assurance
Source/CI contract checks validate the actual pinned Telegram overlays and callbacks. A successful APK build cannot itself prove Telegram's third-party server will return an authentication token. The video alone does **not** identify why the server did not answer. Do not claim network server rejection or completed QR authorization until a real scan from the official Telegram Android app succeeds on a phone.

## Acceptance
1. Foundation, Telegram overlay preflight and full Debug build pass on exactly this branch.
2. Manual Android QR launch on Wi-Fi + cellular: QR displayed, or a specific error/timeout rather than indefinite empty loading.
3. Telegram official device scan and approval completes sign-in; QR closes; 2FA still supported.
4. Cancel/reopen, background/foreground, slow/offline, retries, dynamic theme switch, keypad digit presses, delete and original phone login all remain stable.
5. Build owner-signed Release after full QA; verify APK/AAB and package signing. Never replace an already working signed Release based only on source checks.
