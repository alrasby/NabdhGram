# NabdhGram bundled Telegram themes

The four approved original theme files belong in this directory, as binary assets:

- `nabdh_siri_refined.attheme`
- `nabdh_soft_mint.attheme`
- `nabdh_dark.attheme`
- `nabdh_sand.attheme`

**Preserve original bytes.** The first three include embedded WPS JPEG wallpapers. Do not open and re-save as UTF-8 text.

The build step `scripts/apply-nabdh-bundled-themes.py` checks SHA-256 for all four files, copies them unchanged to Telegram assets, and registers named entries in the native Theme picker. Until the full bundle is present, the script does not alter the upstream theme selector. If only some files are present, the build fails rather than shipping an incomplete bundle.
