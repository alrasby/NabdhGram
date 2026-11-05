# NabdhGram identity and configuration

## Product
- English display name: NabdhGram
- Arabic display name: نبض جرام
- Maintainer/brand: NabdhServ
- Proposed application ID: `net.nabdhserv.nabdhgram` (**proposal, not yet applied to Android source**)
- Project repository: https://github.com/alrasby/NabdhGram

## Artwork handling
The user-approved app icon is the immutable visual master. Its merged Arabic `ن`, Latin `G`, integrated paper plane, and original colors must not be redrawn or replaced. Production Android adaptive icons must be checked for masking and launcher compatibility.

**Status:** Identity specification only. Do not claim app resources are integrated until the original image assets are present in the repository.

## Packaging checklist
- [ ] Confirm package ID availability and ownership.
- [ ] Set `APP_PACKAGE` and all dependent package/authority references safely.
- [ ] Set English and Arabic display names and launcher labels.
- [ ] Integrate original app icon into all required Android resource densities.
- [ ] Verify adaptive icon safe zone on multiple launchers.
- [ ] Configure unique Firebase applications and notification handling.
- [ ] Use project-owned Telegram API credentials and release signing.
