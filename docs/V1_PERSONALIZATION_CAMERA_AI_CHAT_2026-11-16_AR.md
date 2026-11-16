# NabdhGram V1 personalization and Camera2 acceptance — 2026-11-16

## Requested and implemented in this development change

- **Main appearance** under NabdhGram Settings → Appearance/Language → after Themes & Colors: title centering, hide stories strip, hide floating compose button, hide normal search bar, and native Telegram folder tab labels as icon+name, name only or icon only.
- **Folder integrity:** native Telegram `DialogFilter` objects and navigation are retained; no dummy folders, changes to folder membership or server calls. All Chats remains a native tab when filters exist. Explicit search is retained even if the normal search bar is hidden.
- **Bubble shape:** three presets (12dp, 19dp, 24dp) using Telegram's native `SharedConfig.bubbleRadius`, persisted in native `mainconfig`. Display preview uses the same theme bubble colors, not an independent design that cannot be applied.
- **Camera2:** remember last front/back lens, optional mirrored selfie, enable optical stabilization only on camera hardware with OIS, prefer high-resolution JPEG capture, optional zoom slider. Existing capture, save and Telegram share path remain native. Front mirror uses bounded JPEG processing.
- **NabdhAI Chat:** a private, manually entered, in-memory chat with the **existing isolated on-device AI service**, no cloud fallback, no Telegram chat/call hooks, no fake responses. A local model still must be available through AICore or compatible verified Gemma for actual replies.
- **Video reference:** `Screen_Recording_20261116_115456_exteraGram.mp4` (17.5 sec) shows exteraGram Camera X/Camera2, smooth switch, FPS, stabilization, mirror, retain lens, high quality, zoom bar, and video-message features. Nabdh Camera2 currently implements **photos**, so extended FPS, video recording messages, stabilization of video capture and PiP are **not** presented as completed functionality.

## Device verification needed after successful Debug

1. Change each layout switch; leave Settings and return without restarting. Verify main NabdhGram title and premium status, existing stories not deleted, FAB visibility and explicit search.
2. On an account with one or more Telegram folders, switch folder display mode 0 / 1 / 2. Confirm All Chats, tab counts, lock state and selected tab are preserved, and folder changes do not move or delete conversations.
3. Change all three bubble presets in a conversation with text, media, replies and long RTL names; verify both incoming/outgoing shapes, themes, gradients and contrast. No chat layout break on upgrading.
4. Camera: switch repeatedly and relaunch with remember enabled/disabled; take front mirror on/off, high-res JPEG on/off, OIS supported/unsupported, flash, zoom slider, save/share and resume after backgrounding. Compare orientation and EXIF handling.
5. AI Chat: enter multiple explicit prompts, clear while request is pending, leave and return, check the model-unavailable message. On a compatible model-equipped device, verify actual local answers and no Telegram message access. No model availability means **not accepted** for inference.
6. Run native Foundation/Preflight/Debug compilation on the **final commit**, followed by hardware QA. No production merge or signed public release before evidence.

## Exclusions, not shipped

- No AI cloud provider, API key UI, automatic chat monitoring or fake AI output.
- No unimplemented exteraGram video features, FPS switch or PiP toggle.
- No removal of Telegram stories, search index or user-created folder metadata.

## Resume

Files: `overlay/java/NabdhHomePrefs.java`, `overlay/java/NabdhPersonalizeActivity.java`, `overlay/java/NabdhCameraActivity.java`, `overlay/java/NabdhAiChatActivity.java`, `overlay/java/NabdhAiActivity.java`, `overlay/java/NabdhAiCoreService.java`; scripts `apply-nabdh-personalization.py`, `apply-nabdh-ai-core.py`, `check-nabdh-personalization.py`, CI workflow and this acceptance file. Tests must be checked against new GitHub run SHA.
