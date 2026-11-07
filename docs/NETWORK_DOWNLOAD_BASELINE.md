# NabdhGram: Network and download performance baseline

## Evidence
- User reports direct Telegram is intermittent on Wi-Fi and cellular, foreground and background.
- Official Telegram has same symptoms. Login initially required VPN.
- Private DNS is enabled; DNS resolution alone cannot guarantee reachability to Telegram data centers.
- User's launcher video shows adaptive icon artwork is disproportionately small.

## Included in this PR
- Larger adaptive icon foreground based on approved original PNG (no redesign).
- Debug-only connection-state diagnostics in pinned Telegram ConnectionsManager.checkConnection().
- No proxy/VPN or DNS modifications. No extra retry loops or persistent battery-consuming service.

## Next measurable connection improvements
- Compare connection-state transitions and recovery duration over 10 foreground/background trials on each network.
- Check whether proxy is enabled in Telegram settings; don't log proxy endpoints or credentials.
- Only if baseline shows a client-specific stale state: add a throttled recheck on a validated network change or foreground transition, at most once per 30 seconds, without forcing reconnect while connected. Test calls and multi-account first.
- Do not claim direct access can defeat blocked Telegram transport.

## Download performance audit
- Upstream FileLoader already handles media operations; preserve its resume/cache behavior.
- Collect controlled 10MB/100MB download timing on Wi-Fi/cellular, cold vs warm cache, interruption/resume, and battery impact.
- Profile FileLoadOperation queues, parallel request limits, DC selection, and cache read/write before changing concurrency.
- Do not indiscriminately increase parallelism: it can worsen congested or throttled connections and waste data.
- Do not bypass Telegram Premium server limits.
- Compare against official Telegram on same network and file.

## Validation
- Build the debug APK and visually inspect launcher on One UI and splash.
- Test messaging, media, voice calls, background/foreground, Wi-Fi/cellular, offline/online.
- Debug logging is conditional on upstream BuildVars.LOGS_ENABLED and may be disabled in some builds.
- No verified speed increase or recovery improvement is claimed yet.
