#!/usr/bin/env python3
"""Retain NabdhGram's Arabic Android resources in the APK.

Telegram's upstream app intentionally filters Android locale resources to zz:
that is fine for Telegram's own downloadable language packs, but it removes our
new values-ar/nabdhgram_settings.xml translations at packaging time.
Do not expand filtering to unrelated locales.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-arabic-resources.py TELEGRAM_SOURCE")

root = Path(sys.argv[1])
gradle = root / "TMessagesProj_App/build.gradle"
source = gradle.read_text(encoding="utf-8")
old = 'localeFilters += ["zz"]'
new = 'localeFilters += ["zz", "ar"]'
if source.count(old) != 1:
    raise SystemExit("Upstream Android locale filter changed")
source = source.replace(old, new, 1)
gradle.write_text(source, encoding="utf-8")

for folder in ("values", "values-ar"):
    path = root / "TMessagesProj/src/main/res" / folder / "nabdhgram_settings.xml"
    if not path.is_file():
        raise SystemExit(f"Missing NabdhGram translations in {folder}")
print("Arabic NabdhGram strings retained in Android APK alongside Telegram locale zz.")
