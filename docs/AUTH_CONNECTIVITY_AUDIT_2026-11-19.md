# NabdhGram — authentication and connectivity source audit (2026-11-19)

Scope: pinned Telegram Android source, NabdhGram login overlays and Release CI. This is a **static/source and CI review**, **not** a completed device-memory/performance/security penetration test.

## Verified source behaviors

1. **QR without entering a telephone number**: `LoginActivity` already requests `auth.exportLoginToken` without invoking phone-number validation. The new overlay places the direct QR action above the phone input on the first login screen. A second logged-in Telegram device must accept the QR token. It is not a replacement for first-ever account registration or Telegram server-side authorization.
2. **QR lifecycle**: PR #93 fixed cleanup being lost because native `BaseFragment.showDialog` replaces a dialog's own dismiss listener. The new work retains that fix and guards an explicitly offline QR-token request, with manual retry and without background polling.
3. **Phone login**: native `auth.sendCode` / `resendCode` and server-selected app, email, SMS, call or alternative routes must remain authoritative. The Glass login overlay sets `settings.allow_firebase=false` (third-party app cannot truthfully advertise the official-only Firebase SMS flow). It already captures **privacy-minimized** route names, numeric errors, timings and current connection state when diagnostics are enabled; no phone, code, password, API hash or QR token is deliberately logged.
4. **Telegram network**: the login overlay already calls `ConnectionsManager.checkConnection()` / `resumeNetworkMaybe()` when foregrounded with network available and MTProto disconnected, and resumes after login-state cleanup. Native MTProto manages DC routing, proxy, IPv4/IPv6 and reconnect. **No custom DC addresses, permanent retries, proxy bypasses, or forged official API identifiers were introduced**.
5. **Production baseline**: owner-signed Release #8 succeeded at `6bf5e005bc772cdfc78d96bc8dbff7e10a900f87`, with APK and AAB upload. This does not prove the QR login UI works on all Android devices.

## Findings and confidence

| Priority | Finding | Status |
|---|---|---|
| High | User video shows app returning to Android home on QR login; actual FATAL EXCEPTION unknown | QR lifecycle bug fixed in PR #93; physical-device reproduction/logcat **still required** |
| High | Authentication code may not arrive on third-party API clients or via some carriers | Server-controlled. Must show actual `auth.SentCodeType` and error, not promise SMS delivery; never bypass rate-limits |
| Medium | QR login entry under phone UI can appear to require the telephone number | Moved QR action above number input, with explicit 'no phone number' label |
| Medium | Unavailable network on QR press could cause avoidable unauthenticated RPC attempt | Added bounded offline guard, existing manual refresh retained |
| Medium | QR approval may take up to token expiry refresh if `updateLoginToken` does not trigger an immediate re-export | Inspect authenticated update delivery and test actual scan before claiming reliable instant login |
| Medium | Native C++ / large bundled assets / battery / memory leaks on real phones | No static-only proof of absence; schedule emulator/device profiling and QR/login smoke |
| Low | Release #8 has a larger multi-ABI APK than device-optimized split APK | Play AAB handles device-specific delivery; avoid removing ABI libraries without supported-device QA |

## Required acceptance — not yet demonstrated on a phone

- App starts in both Arabic and English; QR action is visible and accessible before entering a number
- Open QR, cancel, rotate, background/foreground, reopen, disconnect/reconnect, refresh and ensure there are no stale requests or crashes
- Scan from an **authorized** Telegram session on another device; ensure `auth.loginTokenSuccess` authorizes correctly (and 2FA fallback works)
- Exercise app-delivered code, email code and supported SMS/call routes with no unsupported Firebase promise; document Telegram RPC types and redacted statuses
- Test Wi-Fi, mobile data, IPv4-only, IPv6-capable, weak connection, captive portal, and user-enabled Telegram proxy without hardcoding network endpoints
- Obtain sanitized Android `FATAL EXCEPTION` stack trace if the exact QR crash persists
- Rebuild signed Release on the fix commit and verify APK/AAB certificate, package, permissions, 16 KiB alignment and core chat/media functionality

References: https://core.telegram.org/api/qr-login , https://core.telegram.org/api/auth , https://core.telegram.org/api/datacenter
