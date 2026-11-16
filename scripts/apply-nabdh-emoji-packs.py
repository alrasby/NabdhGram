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

# Telegram 13.2.2 calls onScrolled even after adapter/layout updates.
# Those IDLE callbacks must not repeatedly show/hide the bottom emoji/GIF/
# sticker tab strip; only user drag/fling should affect its scroll visibility.
# Preserve native tab switching, gestures and animation for real scrolling.
view = root / "ui/Components/EmojiView.java"
native = view.read_text(encoding="utf-8")
scroll_anchor = """            if (!smoothScrolling) {
                checkBottomTabScroll(dy);
            }"""
scroll_fixed = """            if (!smoothScrolling &&
                    recyclerView.getScrollState() != RecyclerView.SCROLL_STATE_IDLE) {
                checkBottomTabScroll(dy);
            }"""
if native.count(scroll_anchor) != 1:
    raise SystemExit(f"EmojiView native idle-scroll anchor changed ({native.count(scroll_anchor)})")
native = native.replace(scroll_anchor, scroll_fixed, 1)

# updateBottomTabContainerPosition() runs from dispatchDraw() each frame.
# Do not request a redundant translation/repaint for subpixel geometry noise.
pos_anchor = "            bottomTabContainer.setTranslationY(bottomTabMainTranslation + bottomTabAdditionalTranslation);"
pos_fixed = """            final float nextBottomTabTranslation =
                    bottomTabMainTranslation + bottomTabAdditionalTranslation;
            if (Math.abs(bottomTabContainer.getTranslationY() -
                    nextBottomTabTranslation) >= 0.5f) {
                bottomTabContainer.setTranslationY(nextBottomTabTranslation);
            }"""
if native.count(pos_anchor) != 1:
    raise SystemExit(f"EmojiView bottom-tab position anchor changed ({native.count(pos_anchor)})")
native = native.replace(pos_anchor, pos_fixed, 1)
view.write_text(native, encoding="utf-8")

print("PASS: emoji packs and stable native emoji tab scroll/translation")
