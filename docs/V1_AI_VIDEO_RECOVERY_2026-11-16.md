# NabdhGram release QA update — 2026-11-16, Android video + local AI

## Confirmed findings

**Build #695** failed in Java (not Android SDK or the build machine):
`DialogsActivity.java:12684,12700,12704` complained `local variables referenced from an inner class must be final or effectively final`. The appearance patch mutated upstream `newVisibility` after control-flow assignments and before an anonymous animator callback. Corrected overlay now computes **final** `nabdhVisibleStories` and redirects only post-declaration display uses. Fails closed on Telegram upstream source drift.

**Phone**: screenshot from Samsung SM-S938B (Android 17) shows `AICORE_CHECK_FAILED`, an AICore connection/status-check failure. This does NOT establish the phone is unsupported. Google lists **Galaxy S25 Ultra** among devices for Gemini Nano 4 direct model access (support depends on RAM, OS and AICore availability). ML Kit Prompt `1.0.0-beta5`, published Oct 26 2026, specifically fixes Gemini Nano 4 `checkStatus()` failures on non-Pixel devices. We updated dependency from beta4 to beta5 with a matching source contract. **No hardware result has yet been measured after this update**.

**Gemma**: Google LiteRT Community Gemma3-1B-IT hosts a gated **555 MB int4 `.task`** which requires user acceptance of the Gemma license on Hugging Face. Two independent mirrors list SHA-256 `e3d981c01aeaaac69a84ffa0d4be13281b3176731063f1bea1c9fe6887bd9dee` for the matching `.task` file. The app now provides a guided model/license link and pre-fills that hash **after explicit user tap**, and continues to verify the full 555 MB file bytes on import. These mirrors are not authoritative manufacturer provenance, and the digest alone cannot verify licensing. **No model weights are embedded** in the APK. The user must download from an authorized source before installation and verify on-device inference. Bundling 555 MB inside base APK would make upgrades and distribution impractical.

## Video recording implementation

Added an independent **Camera2 + MediaRecorder** record screen accessed from Nabdh Camera. Actual H.264/MP4 with AAC audio recording, MediaStore persistence and native Telegram share, front/back camera switching, feature-checked video EIS setting, FPS selection 24/30/60 (clamped to supported AE ranges, encoder can still reject unsupported combinations), and Android 8+ opt-in PiP while the recorder remains visible. Camera and microphone use runtime Android permissions. PiP is not Telegram video-call PiP.

**Testing required**: physical-camera compatibility, start/stop/early stop, 24/30/60 FPS, EIS, PiP transitions, microphone refusal, leaving app and callback races, low storage, Android 26 & older, saving and sharing. Unsupported configurations must fail without corrupting recordings. No photo/Telegram call engine modifications.

## Release acceptance

- On model-equipped Samsung, run new Nano status and actual prompt from NabdhAI and AI Chat; else download licensed Gemma and import exact matching verified `.task` file; test actual local reply before marketing NabdhAI as production-ready.
- Latest GitHub CI status after final commit must prove Java compilation and APK.
- Video recorder and UI options require real device proof; code and CI alone do not certify them.
- `main` stays untouched; PR #79 stays draft pending QA.
