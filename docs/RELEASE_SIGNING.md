# NabdhGram — production Release signing and distribution gate

**Status:** Release build infrastructure is code-reviewed and isolated; it **must not** be called public/stable until the signed APK and production services are actually verified.

## Source & build types

- Official Telegram pin: `upstream/TELEGRAM_COMMIT` (13.2.2 / 7303 at this checkpoint).
- Debug CI: `assembleAfatDebug`, `net.nabdhserv.nabdhgram`, arm64 test APK, Firebase disabled. This is not suitable for distribution.
- Owner Release: `assembleAfatRelease`, `net.nabdhserv.nabdhgram`, native ARM (32+64) and other declared ABI filters, R8 and resource shrinking, no debuggable flag.
- Production APK is built only by a **manual dispatch on main** of [NabdhGram owner-signed Release APK](../.github/workflows/nabdhgram-signed-release.yml). There is no automatic push-to-public release or Play Store action.
- The release flow applies the same pinned source overlays/compatibility checks and final day/night logo checks used by Debug. Firebase must be configured for the exact package.

## Private GitHub Actions secrets required

Create these **outside the repository**, at Settings → Secrets and variables → Actions:
1. `NABDH_RELEASE_KEYSTORE_B64`: Base64 of a NabdhGram-owner-generated private Android keystore, never an upstream sample/demo key. Preserve the original offline for future updates.
2. `NABDH_RELEASE_STORE_PASSWORD`: keystore password.
3. `NABDH_RELEASE_KEY_ALIAS`: release key alias.
4. `NABDH_RELEASE_KEY_PASSWORD`: key password.
5. `NABDH_RELEASE_CERT_SHA256`: pinned SHA-256 signing certificate fingerprint from the original owner key (64 hex digits, colons optional). Do **not** change it between upgrades.
6. `NABDH_FIREBASE_CONFIG_B64`: base64 of the project-owned Android `google-services.json` with `client_info.android_client_info.package_name` exactly `net.nabdhserv.nabdhgram`. This is required to build with the normal Google Services plugin for production notifications.
7. Existing `NABDHGRAM_API_ID` and `NABDHGRAM_API_HASH` from the owner-registered Telegram API app.

Private key bytes and Firebase config are decoded only in ephemeral CI; the workflow validates the certificate fingerprint and package identity before building, removes the temporary files afterwards, and rejects Debug-signed or wrong-certificate APKs. Keep workflow logs and build artifacts private until privacy and security approval.

### Pre-release checks

- All v1 product requirements actually implemented and tested; do not pass from static feature cards.
- Foundation AST/tests, pinned native API preservation and signed Release Gradle compilation.
- `apksigner` v2 verification, package name, signing certificate fingerprint, non-debuggable manifest, APK resource/branding and ABI inspection.
- Real install and upgrade test with the production certificate, sign-in and Telegram sessions, notifications (Firebase), calls, media transfers, RTL, appearance and chat features.
- Privacy policy, data safety, Google Play requirements, licensing and attribution (Telegram upstream GPL and third parties), security review and versioning.

### Important upgrade-signing warning

**A Release signed with a new key cannot be installed as an update over the previously installed Debug APK signed with another certificate, even though both use the same package name.** Never silently re-sign or overwrite a debug install: use a device backup/known fresh install and avoid promising lossless in-place migration. Once the public Release key is selected, reuse the same signing certificate for every public upgrade.

Passing source checks does not prove the device release. Missing secrets are an explicit blocker, not an invitation to generate a disposable signing key or publish a dummy-key APK.
