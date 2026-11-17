#!/usr/bin/env python3
"""Release gate: no Twemoji/Noto/OpenMoji code/assets or network-dependent emoji packs."""
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-native-emojis.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main"
java = root / "java/org/telegram"
picker = (java / "ui/NabdhAppearancePickerActivity.java").read_text(encoding="utf-8")
native = (java / "ui/Components/EmojiView.java").read_text(encoding="utf-8")
emoji = (java / "messenger/Emoji.java").read_text(encoding="utf-8")
assert "NabdhEmojiPacks" not in picker + emoji
assert "Twemoji" not in picker and "OpenMoji" not in picker and "Noto" not in picker
assert "SharedConfig.useSystemEmoji = useSystem;" in picker
assert "SharedConfig.saveConfig();" in picker
assert "Emoji.invalidateUiRunnable.run();" in picker
assert "NotificationCenter.didSetNewTheme" in picker
assert "keep emoji/GIF/sticker tabs stable during scroll" in native
assert "checkBottomTabScroll(dy);" not in native
assert "nextBottomTabTranslation) >= 0.5f" in native
assert not (java / "messenger/NabdhEmojiPacks.java").exists()
assert not (root / "assets/nabdh_twemoji").exists()
print("PASS: native Telegram/Android emojis only; stable tabs, no bundled third-party assets")
