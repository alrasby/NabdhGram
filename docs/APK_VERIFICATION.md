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

**CI integration:** The workflow now looks for `branding/approved/nabdhgram-master.png` inside the NabdhGram repository checkout. If this file exists, it applies the exact master image to the upstream checkout before compiling. If it is absent, the workflow explicitly reports `not-configured` and builds without branded launcher art. The approved PNG is **not currently committed**. Do not describe a build as fully branded until the original approved master is added and the result is checked on an Android device. Never replace the approved original with a generated approximation. The original approved icon is expected to have its intended background and safe padding; adaptive launcher masks may crop its edges.

## Remaining production blockers
- NabdhGram-owned Telegram API credentials and compliant login behavior.
- NabdhGram-owned Firebase/FCM configuration or a tested alternative push strategy. The experimental workflow disables upstream Google Services processing; background notifications may fail.
- Production signing, verified app icon, device install, voice/calls, privacy/security, licensing and store policy checks.
- Implementation of roadmap features and localization acceptance tests.
