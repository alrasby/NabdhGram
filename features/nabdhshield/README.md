# NabdhShield URL signals — first implementation

A standalone, local-only Java URL classifier and JUnit tests are now in `features/nabdhshield/`.

**Not wired into the APK yet.** The pinned Telegram upstream is cloned at build time, and the existing workflow does not compile these files. Do not describe this as a shipped Safe Link Preview.

Signals: invalid URL, HTTP, userinfo, punycode hostname, IP literal. No remote reputation service, logging, DNS or browsing; signals are *not* proof of danger. These are conservative warning inputs, not an automatic blocklist.

Next integration PR: inspect Telegram's external-link click path and insert an **opt-in** preview UI, localized Arabic/English, before external navigation; preserve internal Telegram links and user choice. Integrate unit tests into CI and verify false positives, RTL, safe fallbacks and lifecycle. Never transmit links or message content to third parties without opt-in.

Keep existing connection, notifications, media, calls, account state and download code untouched.
