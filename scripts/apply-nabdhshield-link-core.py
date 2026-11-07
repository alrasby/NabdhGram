#!/usr/bin/env python3
"""Install the local-only NabdhShield link signal analyzer in pinned Telegram source."""
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: apply-nabdhshield-link-core.py TELEGRAM_SOURCE JAVA_SOURCE")
    root, source = map(lambda p: Path(p).resolve(), sys.argv[1:])
    target = root / "TMessagesProj/src/main/java/org/telegram/messenger/NabdhShieldLinkAnalyzer.java"
    if not (root / "TMessagesProj/src/main/java/org/telegram/messenger/FileLoader.java").is_file():
        raise SystemExit("Pinned Telegram source missing")
    if target.exists():
        raise SystemExit("Refusing to overwrite upstream NabdhShield class")
    content = source.read_text(encoding="utf-8")
    if "class NabdhShieldLinkAnalyzer" not in content:
        raise SystemExit("Unexpected NabdhShield source")
    target.write_text(content, encoding="utf-8")
    print("Installed local-only NabdhShield link analyzer; not yet connected to chat UI.")

if __name__ == "__main__":
    main()
