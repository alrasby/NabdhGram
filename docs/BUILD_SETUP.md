# NabdhGram — Source and build preparation

## Verified upstream requirements
Official source: https://github.com/DrKLO/Telegram

As stated in upstream README at the time of inspection:
- Android Studio 2025.1.4
- Android SDK 36
- Android NDK 27.2.12479018
- Gradle wrapper distribution 8.13
- Recursive Git submodules

## Fetch and verify source

From a Linux/macOS or Git Bash shell:

```bash
bash scripts/bootstrap-upstream.sh Telegram-upstream
bash scripts/verify-upstream.sh Telegram-upstream
```

The bootstrap deliberately creates a separate upstream checkout; it does **not** overwrite the NabdhGram repository or claim to be a completed fork. Once a specific revision is selected and licenses reviewed, source integration will be performed as a separate, auditable step.

## Before an actual Android build

1. Obtain your own Telegram `api_id` and `api_hash` through https://my.telegram.org, following https://core.telegram.org/api/obtaining_api_id.
2. Configure unique NabdhGram package/application IDs, app name, resources, and notification identifiers.
3. Replace upstream placeholder signing configuration and any placeholder Firebase configuration with project-owned credentials. Do not commit secrets.
4. Verify Gradle/JDK/SDK/NDK compatibility against the **pinned** upstream revision.
5. Audit applicable licenses and required attributions.
6. Run a local debug build, inspect output, install on a test device, and record results.

Do **not** publish APKs using upstream dummy release keys or credentials.

## CI status
The `foundation-checks` workflow checks shell syntax and documentation only. It does **not** compile Android or create an APK. Android CI will be enabled after source import and credential-safe configuration.
