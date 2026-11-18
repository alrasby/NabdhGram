#!/usr/bin/env python3
"""Keep approved emoji-panel stability adjustment without any third-party packs."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-stable-emoji-tabs.py TELEGRAM_SOURCE")
view = (Path(sys.argv[1]).resolve()
        / "TMessagesProj/src/main/java/org/telegram/ui/Components/EmojiView.java")
source = view.read_text(encoding="utf-8")
scroll_old = """            if (!smoothScrolling) {
                checkBottomTabScroll(dy);
            }"""
scroll_new = """            // NabdhGram: keep emoji/GIF/sticker tabs stable during scroll.
            // Explicit search/selection controls still manage their visibility."""
position_old = "            bottomTabContainer.setTranslationY(bottomTabMainTranslation + bottomTabAdditionalTranslation);"
position_new = """            final float nextBottomTabTranslation =
                    bottomTabMainTranslation + bottomTabAdditionalTranslation;
            if (Math.abs(bottomTabContainer.getTranslationY() -
                    nextBottomTabTranslation) >= 0.5f) {
                bottomTabContainer.setTranslationY(nextBottomTabTranslation);
            }"""
for old, new, label in (
    (scroll_old, scroll_new, "native scroll"),
    (position_old, position_new, "bottom-tab translation"),
):
    if source.count(old) != 1:
        raise SystemExit("Telegram API drift: " + label)
    source = source.replace(old, new, 1)
view.write_text(source, encoding="utf-8")
print("PASS: native emoji tabs remain stable, no external emoji artwork installed")
