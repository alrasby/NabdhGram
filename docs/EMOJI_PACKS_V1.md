# NabdhGram Emoji Packs — V1 implementation and license notice

## What the switch actually changes

`Telegram` (default) keeps the pinned Telegram sprite engine intact.
`Android system` uses Android's currently installed emoji font.
`Google Noto Emoji`, `Twemoji`, and `OpenMoji` select independent PNG artwork
through `NabdhEmojiPacks.wrap()` in Telegram's ordinary `Emoji.getEmojiDrawable()`
path. For standard Unicode emoji spans this draws the chosen PNG image instead
of relabeling the system emoji. Telegram's custom, animated and compound-emoji
paths remain native. Existing emoji spans consult the selected renderer at draw
time. The style affects only the NabdhGram display, not remote recipients.

## Privacy and network behavior

The default Telegram pack does not trigger requests. After explicit selection
of an independent art pack, NabdhGram fetches only individual emoji Unicode
codepoint identifiers (not full message text, user IDs or contacts) over HTTPS
from jsDelivr. Fetched PNGs are checked for size, PNG signature and image
dimensions, decoded with Android BitmapFactory, cached in the app's private
cache, and displayed. There are two bounded download workers and a 6 MiB
in-memory LRU; the per-pack disk cap is 20 MiB. If an image is missing, an
unsupported emoji sequence is encountered, or the network fails, the native
Telegram glyph remains visible. Previously downloaded glyphs can display
offline; an entire external pack is **not** bundled or guaranteed offline.

The PNG source revisions are pinned to:

- Google Noto Emoji: `99701e07d3d1fe1bdbcdb14964547f0fd592966f`
- Twemoji: `b6b55fef1e8636b540a6d016a4729ca8cdf2e60b`
- OpenMoji: `3e01de523ddefe9c5e46a7765b15efef04bf9002`

## Credits and licenses

- **Google Noto Emoji** by Google and contributors; 2D PNG artwork,
  [Apache License 2.0](https://github.com/googlefonts/noto-emoji/blob/main/LICENSE).
  Source: https://github.com/googlefonts/noto-emoji
- **Twemoji** by Twemoji contributors; PNG graphics,
  [Creative Commons Attribution 4.0](https://github.com/jdecked/twemoji/blob/main/LICENSE-GRAPHICS).
  Source: https://github.com/jdecked/twemoji
- **OpenMoji** by HfG Schwäbisch Gmünd, Benedikt Groß, Daniel Utz,
  students and external contributors; PNG graphics,
  [Creative Commons Attribution-ShareAlike 4.0](https://github.com/hfg-gmuend/openmoji/blob/master/LICENSE).
  Source: https://github.com/hfg-gmuend/openmoji

NabdhGram does not redistribute Samsung or Facebook's proprietary emoji
artwork. Selecting Android system emoji may display those glyphs only when
they genuinely exist on the device; this is not a standalone pack.

## QA acceptance

A static CI contract checks selection, source routing, fallback, cache limits,
security and Java type-shadow regressions. Runtime acceptance must additionally
check 😀 ❤️ 🇴🇲 👩‍💻 and mixed skin-tone/ZWJ glyphs across all packs; successful
HTTPS fetch, consistent text baseline, LTR/RTL, screen rotation, theme changes,
offline cache and per-device screen capture. Source checks alone are not device
acceptance.
