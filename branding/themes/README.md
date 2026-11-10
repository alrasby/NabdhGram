# NabdhGram bundled Telegram themes

The user-approved theme bundle is stored as **NabdhGram_Bundled_Themes.zip** in this directory.

The archive must contain these exact binary entries:

- `branding/themes/nabdh_siri_refined.attheme`
- `branding/themes/nabdh_soft_mint.attheme`
- `branding/themes/nabdh_dark.attheme`
- `branding/themes/nabdh_sand.attheme`

The build script `scripts/apply-nabdh-bundled-themes.py` reads these files **directly from ZIP** and verifies individual SHA-256 digests before copying bytes unchanged to Telegram assets and registering all four in the native theme picker. Three themes contain embedded wallpaper data; do not re-save the theme files as text.

Individual extracted assets are accepted as a fallback only when the ZIP is absent. A missing or incomplete bundle fails the build instead of silently omitting the themes.
