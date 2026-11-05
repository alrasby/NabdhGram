# Android build preflight

The manually triggered workflow `android-preflight.yml` runs a **Gradle configuration smoke test**, not an APK build.

It fetches the exact Telegram Android revision from `upstream/TELEGRAM_COMMIT`, initializes its native submodules, sets up JDK 17 and Android SDK 36 / NDK 27.2.12479018, and runs `./gradlew help`.

## Why this comes first

Telegram Android's build includes project-specific configuration, API identifiers, Firebase services and signing conventions. The preflight identifies missing prerequisites without distributing a misleading or improperly signed APK.

## How to run

1. Merge the pull request adding this workflow.
2. Go to Actions → Android build preflight (pinned Telegram source).
3. Choose Run workflow on `main`.
4. Inspect the job summary and download `android-preflight-log` if the job fails.

## Interpretation

- A green run means source checkout and Gradle project configuration completed; **it does not mean an APK compiled**.
- A red run means configuration or environment failed. Inspect the uploaded log before making fixes.
- Never place `api_hash`, signing keystores, passwords or Firebase secrets into public GitHub issues or commits.

## Next

After resolving preflight failures, add NabdhGram-specific package identity, approved icon resources, project-owned API configuration, and a debug APK build workflow with appropriate secret handling.
