# NabdhGram Glass — integration and release gate

This document records the **actual** scope of PR #60 (stacked on PR #58), not a claim that the entire Telegram UI has been redesigned.

## Shared component policy
- Preserve Telegram's original adapter order, read receipts, media lifecycle, authentication and message grouping.
- Theme-facing surfaces use Telegram theme keys at draw/update time; never force a fixed turquoise or gray palette.
- All font **family names** remain English in every locale; textual explanations may be translated.
- Application font choice starts with Device default, Regular weight and the saved UI/chat sizes.
- No decorative overlays may intercept touches or replace message controllers.

## Implementation map
| Surface | Owner / implementation | Verification |
| --- | --- | --- |
| Text + media bubble shells | MessageDrawable, apply-glass-bubble-outline and finishing pass | source checks; device test pending |
| File metadata height | ChatMessageCell / apply-glass-document-layout | source checks; long Arabic filename device test pending |
| Reply/quote/message text | Theme TextPaint / apply-glass-chat-typefaces | source checks; device re-layout pending |
| Chat composer | ChatActivityEnterView | theme-aware color refresh; device test pending |
| Visible native labels | LaunchActivity scan | native font eligibility + original font restoration; device test pending |
| Main Telegram settings | UniversalAdapter opt-in | source checks; device test pending |
| NabdhGram settings | NabdhGramSettingsActivity / feature categories | source checks; device test pending |
| Privacy, notifications, data, theme pages | NabdhGlassRowDecoration | source checks; device test pending |
| Profile actions and details | ProfileActionsView + shared row decoration | source checks; device test pending |
| Bundled and imported themes | ThemeInfo null guard; active theme keys | source checks; reset crash reproduction pending |

## Required before merge into main
1. Build **latest integrated SHA** with Android Gradle and check APK identity and signing. A successful Foundation check alone is insufficient.
2. Switch System/Readex Pro/Vazirmatn/Noto Sans Arabic/Tajawal/Rubik/Sans-serif/Serif, Regular/Bold, UI scaling 85/100/115%; change on a visible Settings page, chat list and chat, then switch back to Device default.
3. Switch all 4 bundled themes, user-imported .attheme, and Telegram default (light/dark); verify no crash, stale surfaces or unreadable contrast.
4. Inspect Arabic RTL and English LTR: dialogs, pinned/archive, verified names, settings, profile, media captions, replies, forwarded messages, voice/video/photo/file/document groups.
5. Inspect login keypad, country/phone fields, five-/six-digit code, backspace, error/call/SMS fallback, without logging sensitive values.
6. Test fast scrolling, selection, long press, swipe/archive, opening chat, calls, media playback, screenshots of changed surfaces, and font-scale accessibility.
7. Capture a short video and actual APK SHA. **No device verification is claimed until these are performed**.

## Known limitations
- A shared rounded border on native settings does not imply every custom Telegram settings cell has a new Glass background.
- Telegram's custom drawn widgets are not all plain TextViews and may need specific re-layout patches.
- Debug APK has Google Services disabled and is not a production release.
