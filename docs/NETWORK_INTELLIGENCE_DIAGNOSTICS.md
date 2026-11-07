# NabdhGram — Network Intelligence: intermittent direct connection diagnosis

Status: **diagnostic plan only; no network behavior changed**. User confirmed on 2026-11-07 that Telegram sign-in succeeds, but direct connection without proxy/VPN is intermittently slow or disconnected on Galaxy S25 Ultra / Android 17.

## Non-negotiable
- Prefer official Telegram networking code; do not bypass Telegram authentication, platform limits, or assume all failures are censorship.
- Never promise direct networking will defeat IP/protocol blocking.
- Do not hardcode untrusted datacenter IPs, proxy endpoints, DNS-over-HTTPS relays, or external network probes.
- Never collect messages, phone numbers, auth keys, proxy secrets, chat identifiers, or unredacted IPs in exported diagnostics.
- Feature must be opt-in, lightweight, reversible, and local-first.

## Source audit
Pinned upstream: `TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java`.
- `checkConnection()` already calls `native_setIpStrategy` and `native_setNetworkAvailable`.
- `getIpStrategy()` already handles IPv4, IPv6-only and mixed strategies, including `forceTryIpV6`.
- Native networking is under `TMessagesProj/jni/tgnet/`. Avoid ad hoc reconnect loops or native changes before measuring.
- Preserve official proxy settings as an optional user-controlled fallback, never silently enable one.

## Phase N0 — reproduce and compare (no APK code changes)
1. Record whether the symptom occurs on Wi-Fi, mobile data, or both, with proxy/VPN disabled.
2. For each network, compare 3 attempts: launch, send a short message to Saved Messages, load one existing image, wait 2 minutes and return.
3. Record qualitative connection status (Connecting/Updating/Connected), approximate duration and whether recovery occurred after network switching. No account details.
4. Test with Android app battery setting **Unrestricted** only if disconnections occur while backgrounded; compare without it.
5. Distinguish app-specific from network-wide symptoms by testing official Telegram on the same network at the same time, if available.

## Phase N1 — optional in-app diagnostic panel (v1.0 Network Intelligence)
- Show Telegram connection state, Android transport type (Wi-Fi/cellular), whether the OS reports validated connectivity, and anonymized counts of transitions/retries.
- Display active IP strategy (IPv4-only / IPv6-only / mixed) without printing addresses.
- Offer a **manual** 'Recheck connection' control using existing official check/update mechanisms, with rate limiting and no reconnect storm.
- Offer a 5-minute opt-in local diagnostic capture and redacted text export; no telemetry by default.
- Distinguish 'Internet available but Telegram unreachable' from 'No network' without claiming a definite cause.
- Provide user guidance on background battery restrictions and media auto-download; never silently change system settings.
- Keep proxy controls user-initiated and disclose if active.

## Phase N2 — measured optimizations only
- Compare existing IP strategy behavior across actual failing networks before any adaptation.
- Consider temporary per-network strategy adjustments only after evidence, with automatic rollback, safe defaults, and no permanent preference changes without user consent.
- Avoid repeated native reconnects, battery drain, parallel login requests, and interference with calls/downloads.
- Regression test multi-account, Wi-Fi↔cellular, airplane mode, background/foreground, voice calls, media, and Android 17.

## Acceptance
- No regression in login, message sending, notifications, media, calls, or battery.
- Measured improvement in repeated connection recovery on the affected network, not anecdotal single attempt.
- All added UI strings localized Arabic/English and RTL-safe.
- No claim of bypassing total network blocking.
- Report implementation, build, and device-test status separately.

## Current next input
Ask user whether slow/intermittent connection occurs on Wi-Fi, mobile data, or both, and whether only in background. Do not select an optimization before this baseline.
