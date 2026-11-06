# NabdhGram approved brand artwork

The approved icon was supplied by the project owner and **must not be regenerated or approximated**.

## Source

The owner selected the second of two 1536x1536 supplied images. Although its uploaded filename ended in `.png`, the file contents were JPEG. Convert using an image decoder (e.g. Pillow), never by renaming the extension.

The source image itself is **not committed** to this repository by this change. Keep the original file in a controlled asset archive and supply it to the generator when integrating resources.

## Generate Android density resources

```sh
python3 -m pip install Pillow
python3 scripts/generate-brand-icons.py /path/to/approved-icon.png output/brand-icons
```

The generator produces a 512x512 store icon, an unmodified-size PNG master, and mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi launcher assets.

## Integration gate

1. Inspect the pinned Telegram Android resource structure and adaptive icon XML files before replacing any resource.
2. Create a **separate** Android application ID `net.nabdhserv.nabdhgram`, and audit provider authorities, permissions, deep links, app widgets, and build flavors.
3. Ensure app label and branding change consistently without overwriting the official Telegram package.
4. Configure developer-owned Telegram API credentials using GitHub Actions secrets, never commit credentials.
5. Preserve upstream license notices and comply with Telegram's API terms.
6. Build and test a separate debug APK; do not claim a NabdhGram APK exists until the branded build actually passes.

The earlier `android-debug-apk.yml` workflow builds unmodified upstream Telegram only. It is not a branded NabdhGram build.
