# NabdhGram — Localization Architecture (v1.0 requirement)

**Status:** Approved architecture and acceptance criteria; implementation is not yet complete.

## Goals
1. Preserve Telegram Android's existing localization framework and available Telegram language packs. Do not restrict the client to Arabic and English.
2. On first launch, use the Android/system language when supported; fall back gracefully to English when not.
3. Let users select a different **interface language** inside the app without changing the phone's language.
4. Keep **message translation target language** as a separate preference; it must not be tied to interface language.
5. Make every new NabdhGram UI string localizable from the first implementation (NabdhShield, Focus Lens, Catch Me Up, Message Workspace, privacy, media, login help, settings, notifications).
6. Provide complete, human-reviewed **Arabic and English** translations of NabdhGram-specific strings for v1.0. Other Telegram UI languages remain available, but untranslated NabdhGram strings may fall back to English until reviewed translations are added. Never claim all feature strings are translated into every language.
7. Respect RTL for Arabic, Persian, Urdu and other RTL locales; test icon mirroring, mixed-direction numbers/phone numbers, timestamps, URLs, punctuation, dialogs and accessibility.
8. Do not embed user-visible strings directly in Java/Kotlin/XML UI logic; use the localization resources or Telegram's localization mechanisms. Define stable keys and placeholders; do not concatenate translated sentence fragments.
9. Protect placeholders and plurals; support locale-appropriate dates/numbers where relevant, while preserving phone-number and protocol formatting.
10. Prefer existing Telegram language infrastructure rather than introducing a competing locale manager.

## Suggested implementation sequence
- Audit Telegram pinned source localization implementation, locale override, language pack loading and fallback behavior.
- Create NabdhGram-specific string keys and Arabic/English catalogs using the same resource mechanism.
- Connect locale selection and independent translation-target setting to existing settings where feasible.
- Apply localization to each new feature as it is developed; no feature is complete with hard-coded strings.
- Test system language switching, app-only override, missing-key fallback, RTL layouts and accessibility on Android devices.

## Release acceptance checks
- [ ] Arabic and English reviewed for every new NabdhGram string.
- [ ] Telegram-supported languages remain selectable/usable.
- [ ] First launch follows device language when available.
- [ ] User can override app interface language.
- [ ] Message translation target can differ from interface language.
- [ ] Missing translations fall back gracefully without raw keys or crashes.
- [ ] RTL and LTR navigation, layout and mixed-direction content pass device tests.
- [ ] New features, authentication guidance and NabdhShield warnings are localized and understandable.

**Important:** This document records requirements; no implementation or build validation is implied.
