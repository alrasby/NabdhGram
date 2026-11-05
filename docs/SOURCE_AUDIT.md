# Telegram Android source audit — initial findings

Source: https://github.com/DrKLO/Telegram

The following files were inspected directly from the official upstream repository (default branch; **not yet pinned**):
- `README.md`
- `LICENSE`
- `.gitmodules`
- `settings.gradle`
- `gradle/wrapper/gradle-wrapper.properties`
- `TMessagesProj_App/build.gradle`
- `TMessagesProj/build.gradle`

## Findings
- The root `LICENSE` is GNU GPL version 2; check source-file notices and third-party submodule licenses before redistribution.
- The current README requests Android Studio 2025.1.4, Android SDK 36 and NDK 27.2.12479018.
- Gradle wrapper: 8.13.
- `TMessagesProj_App` is an Android application module; `TMessagesProj` is a library module.
- The app's `defaultConfig.applicationId` is assigned from `APP_PACKAGE`, so the unique NabdhGram package needs a full configuration audit, not a blind text replacement.
- Debug builds in the inspected app Gradle script use a signing configuration pointing at `TMessagesProj/config/release.keystore`, with password variables. Replace placeholders and ensure no secrets are committed.
- The debug build type has application ID suffix `.beta`.
- The project contains many Git submodules, including native libraries and media components. Recursive checkout is mandatory.

## Current risks / blockers
1. The upstream commit has not yet been pinned.
2. The full upstream source and submodules have not yet been imported into this repository.
3. A private Telegram API ID/hash, project-specific Firebase settings, and safe signing setup are not yet configured.
4. The approved master icon is not stored in the repository; do not substitute regenerated artwork.
5. No Android compilation or on-device validation has been performed.

## Next implementation checkpoint
Import a pinned upstream commit with submodules, record license notices, and audit all `APP_PACKAGE`, resource, provider-authority, notification and signing references before attempting a build.
