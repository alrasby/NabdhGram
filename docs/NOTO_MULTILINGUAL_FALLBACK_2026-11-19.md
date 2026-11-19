# Noto Sans ↔ Noto Sans Arabic fallback — implementation and acceptance

## User-visible behavior

Appearance now offers **Noto Sans** as an independent selectable font while retaining **Noto Sans Arabic**, DejaVu Sans Condensed, Readex Pro, Vazirmatn, Tajawal, Rubik, serif and device default.

When **Noto Sans** is selected:

- Android **10+ (API 29+)** builds a single Android Typeface using `Typeface.CustomFallbackBuilder` with **Noto Sans** as the primary face, **Noto Sans Arabic** as an explicit second face, and `sans-serif` as the final **system fallback** (for unsupported scripts, emoji, CJK, Indic and other glyphs).
- Regular and Bold use variable `wght` axes **400** and **700** consistently for both Latin and Arabic fonts. Italics request the native slant style; no font binary or message content is mutated.
- Android **9 and earlier** lack public `CustomFallbackBuilder`: the code uses Noto Sans with the **platform system fallback** for Arabic/other scripts; it does **not** guarantee selecting the bundled Noto Sans Arabic face on these older devices. Never inject spans into Telegram messages just to emulate a font fallback.
- The same selected family is used for Telegram's `AndroidUtilities.getTypeface`, chat `TextPaint`, chat-list `Canvas` labels and settings preview. Native icon, code, math and emoji fonts remain excluded.
- Resetting to **device default** preserves existing Telegram original font behavior. Other selected families are unchanged.

## Provenance and licensing

Noto Sans and Noto Sans Arabic are downloaded from the **same pinned** Google Fonts revision `5bb28733cec313b63fbd415b574b5ae35c8aa8b8`, with separate OFL notices saved as `NotoSans-OFL.txt` and `NotoSansArabic-OFL.txt`. Source:
https://github.com/google/fonts/tree/5bb28733cec313b63fbd415b574b5ae35c8aa8b8/ofl/notosans

## Regression checks

`scripts/check-nabdh-font-catalog.py` checks unique menu choices and native Typeface routing. `scripts/check-nabdh-noto-fonts.py` checks the **actual bundled font cmap tables** for Latin (`Hello NabdhGram`), Greek (`Ελληνικά`), Cyrillic (`Привет`), Arabic (`مرحبا بالعالم`), required license files and damaged font detection. The CI step checks generated `NabdhNotoFallback.java` and all existing Telegram Glass/native API preservation guards.

These are **source and font-glyph checks, not an emulator rendering assertion**. Before declaring device QA complete, run an actual **Arabic/English mixed** chat and settings smoke on **API 29+ and API <29**, in right-to-left and left-to-right locales, normal/bold and font scaling; verify emoji, message links, hashtags, code, bot keyboard, chat list, editing, notifications, system languages and Android Accessibility.

**No signed Release or actual device interaction is claimed until separately verified.**
