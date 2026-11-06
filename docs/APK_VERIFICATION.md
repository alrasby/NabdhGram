# Post-build verification and brand integration

## Verified foundation
The identity debug build has produced an APK, but passing Gradle alone does not prove that the installed package, launcher icon, signing, login, push notifications, or Telegram API credentials are ready for release.

## Automated APK checks
The identity build workflow now checks:
- Expected package ID: `net.nabdhserv.nabdhgram.beta`.
- Launcher label: `NabdhGram`.
- Android APK signature v2 validity.
- SHA-256 checksum and Android manifest metadata.
These checks are to be validated in the next workflow run. They do not substitute for real-device tests.

## Approved icon integration
`scripts/apply-brand-icons.py` accepts the **exact original approved PNG** (square, >=512px), creates Android density assets, and overlays the launcher adaptive icon. It never generates a new logo.

Example after cloning the pinned Telegram checkout:

```bash
python3 -m pip install Pillow
python3 scripts/apply-brand-icons.py /path/to/Telegram-upstream /secure/path/nabdhgram-master-1536.png
```

**Important:** The approved PNG is not yet committed to this repository or wired into the CI build. Do not describe a build as fully branded until the exact approved master has been supplied to the build and the result has been checked on an Android device. Prefer an explicitly reviewed binary asset commit or a secure controlled asset source; do not download an unverified internet image.

## Remaining production blockers
- NabdhGram-owned Telegram API credentials and compliant login behavior.
- NabdhGram-owned Firebase/FCM configuration or a tested alternative push strategy. The experimental workflow disables upstream Google Services processing; background notifications may fail.
- Production signing, verified app icon, device install, voice/calls, privacy/security, licensing and store policy checks.
- Implementation of roadmap features and localization acceptance tests.
