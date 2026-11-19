# NabdhGram font catalog review — 2026-11-19

## Curated font catalog
Source of truth: `scripts/apply-glass-settings.py`, `scripts/apply-glass-global-font.py` and `scripts/install-open-fonts.py`.

| Display option | Android family / bundled file | Primary role |
|---|---|---|
| Device default | system-default / native Telegram fallback | Broadest device language fallback; default |
| Readex Pro | ReadexPro.ttf | Arabic and Latin interface |
| Vazirmatn | Vazirmatn.ttf | Modern Arabic/Persian text |
| Noto Sans Arabic | NotoSansArabic.ttf | Arabic-family comprehensive shaping |
| Tajawal | Tajawal.ttf | Distinct modern Arabic display |
| Rubik | Rubik.ttf | Distinct Latin/European/Hebrew; relies on system for unsupported scripts |
| **DejaVu Sans Condensed** | **DejaVuSansCondensed.ttf + -Bold.ttf** | Compact Latin/Greek/Cyrillic/Arabic (not universal) |
| Serif | Android serif family | Serif presentation, platform fallback |

### Duplicate removed safely
The explicit **Sans-serif** option duplicated the practical device-default Android sans-serif choice on many devices. Remove only that catalog entry; retain all visually different Arabic-focused and serif families. Existing saved `font_family=sans-serif` is migrated to `system-default` on entry to font settings. No native font file was deleted; only the redundant option is removed.

### License and provenance
DejaVu version **2.37** sourced from the **official** release ZIP:
https://sourceforge.net/projects/dejavu/files/dejavu/2.37/dejavu-fonts-ttf-2.37.zip/download

Pinned SHA-256: `7576310b219e04159d35ff61dd4a4ec4cdba4f35c00e002a136f00e96a908b0a` (official release page https://dejavu-fonts.github.io/Download.html). The **Bitstream Vera / DejaVu** permissive font license is not SIL OFL. Redistribute the original full `LICENSE` from the verified ZIP as `fonts/DejaVu-LICENSE.txt` together with the two original unmodified TTFs; abort if the archive hash, font signature or license is unexpected.

### Global/multilingual recommendations
No single compact TTF covers every world language or modern color emoji. Let Android and Telegram use **font fallback**, not package hundreds of megabytes of fonts or replace the specialized emoji/monospace fonts.

- Keep **device default** as safest multilingual option and honor Android/Telegram's CJK, Indic, Thai, Hebrew, emoji and other script fallbacks.
- **Noto Sans / Noto Serif family** is the most appropriate scalable *multi-script design system* for future upgrades, not one universal file. Add scripts only on demand, with verified OFL licenses and correct fallback.
- **DejaVu Sans Condensed** is useful for a denser compact look but not a Tahoma clone and does **not** cover all scripts.
- **Readex Pro, Vazirmatn, Noto Sans Arabic, Tajawal** serve different Arabic visual preferences and should not be deleted on subjective similarity alone.
- **Rubik** is a different Latin style; fallback remains required for Arabic and several scripts.

## Engineering checks
- Existing global font switching, preferences, instant rebind and chat canvas text paints remain wired.
- Real Regular/Bold DejaVu fonts; preserve native weight semantics for heading labels, no icon/emoji/monospace replacement.
- Verify package font binary hashes and license at build time; preflight checks catalog uniqueness and font mapping.
- **Pending:** device/emulator visual review at Arabic/Latin mix, line-wrapping at 85–115% text scale, English/Russian/Greek, and fallback for Hindi/Chinese/Japanese; final production APK and AAB checks.
