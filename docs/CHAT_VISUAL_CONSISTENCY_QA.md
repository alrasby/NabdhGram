# NabdhGram native chat visual consistency — 2026-11-13

## Problem observed on the user's own screenshot
Same channel shows a solid gray document/card adjacent to a more
transparent cyan file card while similar messages use incompatible
underlying bubble paints. Some document names and mixed Arabic/Latin
message paths use the previous Telegram font after a font change.

## Fix (isolated, pinned Telegram 13.2.2)

- `NabdhBubblePalette`: one deterministic alpha/contrast policy and one
  consistent rim opacity/width for **both** native MessageDrawable
  `TYPE_TEXT` and `TYPE_MEDIA`, with the existing cached NinePatch
  and Path/gradient drawing branches. The native incoming/outgoing colors,
  imported Telegram themes, tails, grouped bubbles, selection, crossfade
  and preview remain authoritative. Files have a slightly more opaque
  lower bound for metadata readability.
- Existing live wallpaper blur remains **text-only** to protect real
  photo/video thumbnails, but file/attachment bubble backgrounds follow
  the same palette. No per-frame ML model; adaptive contrast uses
  simple integer luma from native theme colors and is reproducible.
  The Liquid/Crystal specular shader remains cached.
- `NabdhTypefaceManager`: one central selector for 29+ existing native
  `Theme.chat_...TextPaint` roles, including document filename, audio
  title/performer, forward/reply, captions, location, contact, time and
  context results. It follows the selected Readex Pro/Vazirmatn/etc via
  `AndroidUtilities.getTypeface` and preserves native bold roles.
  Native code/monospace and emoji paints are **not** overridden.
- Hooked after Telegram creates its chat paint resources and on each
  actual font/weight/size change, before the existing
  `NotificationCenter.didSetNewTheme` and visible-row refresh;
  preserves cached layout invalidation and the selected account/theme.

## Acceptance and compatibility
1. Foundation parser/source unit checks must pass, then real
   pinned-upstream overlays and native method preservation checks.
2. Android debug build must compile and launch; no assertion of
   visual success from Python alone.
3. On device inspect **the same chat** with plain Arabic, mixed script
   `ج1-اسم-ملف.epub`, Arabic file title, audio, long caption,
   forwarded/reply text, 3-line document name, GIF, photos and videos.
4. Verify imported theme + dark/light, incoming/outgoing, Soft/Liquid/
   Crystal styles, selection and archived/saved chat bubbles.
5. Switch every Arabic font, global size and Bold while chat is open
   and after background/foreground; check file metadata spacing and
   that no old Typeface or stale StaticLayout survives scrolling.
6. Profile GPU frames and allocation/jank for a long active channel;
   compare before/after; fallback to Soft Glass on weak devices only
   when measured, not by guessing device capability.
7. All screenshot/visual QA must use sanitized synthetic content;
   never upload real user contacts, files, chat history or tokens.

## Scope boundaries
This does **not** create a generative AI renderer; the same appearance
inputs always yield the same output. The real ML Kit language identifier
and local Context Lens remain independent. A visual QA agent can later
assist with screen comparisons, but cannot be relied upon for runtime
drawing or override user's choice of bubble preset.

Build #567 and independent Experimental Header PR #71 remain
unmodified until their jobs finish; do not cancel running Android CI.
Do not merge draft upgrade PR #63 into main until phone QA passes.
