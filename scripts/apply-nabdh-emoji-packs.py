#!/usr/bin/env python3
"""Install real, opt-in PNG emoji packs into Telegram's native emoji drawable path.

Telegram and Android system remain fully native. Other packs fetch independent
licensed artwork on demand and cache locally with safe fallback.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-emoji-packs.py TELEGRAM_SOURCE")

root = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram"
here = Path(__file__).resolve().parents[1] / "overlay/java"
module = root / "messenger/NabdhEmojiPacks.java"
if module.exists():
    raise SystemExit("Emoji-packs collision: " + str(module))
module.write_bytes((here / "NabdhEmojiPacks.java").read_bytes())

emoji = root / "messenger/Emoji.java"
code = emoji.read_text(encoding="utf-8")
before = """        EmojiDrawable ed = new SimpleEmojiDrawable(info, endsWithRightArrow(code));
        ed.setBounds(0, 0, drawImgSize, drawImgSize);
        return ed;"""
after = """        EmojiDrawable ed = new SimpleEmojiDrawable(info, endsWithRightArrow(code));
        // Per-codepoint, native EmojiSpan-compatible renderer. Default is
        // unchanged Telegram; never intercepts custom/animated emoji.
        ed = NabdhEmojiPacks.wrap(code, ed);
        ed.setBounds(0, 0, drawImgSize, drawImgSize);
        return ed;"""
if code.count(before) != 1:
    raise SystemExit(f"Emoji upstream API changed: {code.count(before)} drawable anchors")
emoji.write_text(code.replace(before, after, 1), encoding="utf-8")
print("PASS: independent opted-in PNG emoji packs hooked into native EmojiDrawable")
