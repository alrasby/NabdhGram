# Upstream integration checkpoint

This branch adds a manually triggered GitHub Actions workflow that clones Telegram Android and its recursive submodules on a GitHub runner, verifies expected files, and uploads a revision manifest.

## Why validation first?
The upstream repository includes large native submodules, several application variants, and signing/credential placeholders. A clone alone is not a safe distributable NabdhGram app.

## Procedure
1. Merge the integration-prep pull request after review.
2. Open GitHub Actions → Telegram upstream checkout validation → Run workflow.
3. Use an immutable upstream commit SHA for reproducibility (the default `master` is only for exploration).
4. Inspect the revision manifest and job logs.
5. Record the selected commit in the project documentation.
6. Integrate the actual upstream source and submodules into a dedicated source branch with full license attribution.
7. Apply unique NabdhGram identifiers and original approved assets.
8. Configure private credentials securely and compile an actual debug APK.

## Security and compliance
Do not commit Telegram API hash, Firebase private credentials, release keystores, or user data. The root upstream repository declares GPL-2.0; third-party component licenses require separate review.

## Status
**Source checkout workflow prepared, not yet run.** No source import or APK build is claimed.
