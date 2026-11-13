#!/usr/bin/env python3
"""Replace Telegram's empty-chat newborn animation with approved NabdhGram art.

The original filter-empty animations remain untouched. No network or behavior
changes; the resource is copied without recompression from approved branding.
"""
from pathlib import Path
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-empty-state.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
source = Path(__file__).resolve().parents[1] / "branding/approved/nabdhgram-welcome-transparent.png"
if not source.is_file() or source.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("Approved transparent NabdhGram logo is missing or not PNG")
destination = root / "TMessagesProj/src/main/res/drawable-nodpi/nabdh_empty_logo.png"
destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, destination)

path = root / "TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogsEmptyCell.java"
s = path.read_text(encoding="utf-8")
old = """            if (prevIcon != icon) {
                imageView.setAnimation(icon, 100, 100);
                imageView.playAnimation();
                prevIcon = icon;
            }"""
new = """            if (prevIcon != icon) {
                if (currentType == TYPE_WELCOME_WITH_CONTACTS
                        || currentType == TYPE_WELCOME_NO_CONTACTS) {
                    // NabdhGram welcome branding; retain Telegram's help and
                    // contact-empty behavior. Never replay the Utyan egg.
                    imageView.setImageResource(R.drawable.nabdh_empty_logo);
                    imageView.setScaleType(ImageView.ScaleType.FIT_CENTER);
                } else {
                    imageView.setScaleType(ImageView.ScaleType.CENTER);
                    imageView.setAnimation(icon, 100, 100);
                    imageView.playAnimation();
                }
                prevIcon = icon;
            }"""
if s.count(old) != 1:
    raise SystemExit("DialogsEmptyCell welcome image anchor changed")
s = s.replace(old, new, 1)
path.write_text(s, encoding="utf-8")
print("PASS: approved NabdhGram logo replaces egg on empty welcome chats")
