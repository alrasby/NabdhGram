#!/usr/bin/env python3
"""Install pinned, OFL-licensed font files into Telegram's assets."""
from pathlib import Path
from urllib.request import urlopen
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: install-open-fonts.py TELEGRAM_SOURCE")
commit = "5bb28733cec313b63fbd415b574b5ae35c8aa8b8"
base = f"https://raw.githubusercontent.com/google/fonts/{commit}/ofl"
fonts = {
    "Vazirmatn": ("vazirmatn", "Vazirmatn[wght].ttf"),
    "NotoSansArabic": ("notosansarabic", "NotoSansArabic[wdth,wght].ttf"),
    "Tajawal": ("tajawal", "Tajawal-Regular.ttf"),
    "Rubik": ("rubik", "Rubik[wght].ttf"),
}
out = Path(sys.argv[1]) / "TMessagesProj/src/main/assets/fonts"
out.mkdir(parents=True, exist_ok=True)
for name, (directory, filename) in fonts.items():
    for source, target in ((filename, out / f"{name}.ttf"), ("OFL.txt", out / f"{name}-OFL.txt")):
        with urlopen(f"{base}/{directory}/{source.replace('[', '%5B').replace(']', '%5D')}", timeout=45) as response:
            data = response.read()
        if source.endswith(".ttf") and (len(data) < 10000 or data[:4] not in (b"\x00\x01\x00\x00", b"OTTO")):
            raise SystemExit(f"Invalid font binary: {name}")
        if source == "OFL.txt" and b"SIL OPEN FONT LICENSE" not in data.upper():
            raise SystemExit(f"Missing OFL license: {name}")
        target.write_bytes(data)
    print(f"Installed {name} with OFL license")
