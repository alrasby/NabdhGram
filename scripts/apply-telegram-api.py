#!/usr/bin/env python3
"""Inject developer-owned Telegram API credentials into pinned upstream BuildVars."""
from pathlib import Path
import os
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-telegram-api.py TELEGRAM_SOURCE_DIRECTORY")
api_id = os.environ.get("NABDHGRAM_API_ID", "").strip()
api_hash = os.environ.get("NABDHGRAM_API_HASH", "").strip()
if not re.fullmatch(r"[1-9][0-9]{0,9}", api_id) or int(api_id) > 2147483647:
    raise SystemExit("Configure a valid NABDHGRAM_API_ID GitHub Actions secret from my.telegram.org")
if not re.fullmatch(r"[0-9a-fA-F]{32}", api_hash):
    raise SystemExit("Configure a valid NABDHGRAM_API_HASH GitHub Actions secret from my.telegram.org")
target = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java"
source = target.read_text(encoding="utf-8")
source, n1 = re.subn(r'public static int APP_ID = 4;', 'public static int APP_ID = ' + api_id + ';', source)
source, n2 = re.subn(r'public static String APP_HASH = "[0-9a-fA-F]{32}";', lambda _: 'public static String APP_HASH = "' + api_hash.lower() + '";', source)
if n1 != 1 or n2 != 1:
    raise SystemExit("Unexpected pinned upstream API credential declarations")
source = source.replace("public static boolean SUPPORTS_PASSKEYS = true;", "public static boolean SUPPORTS_PASSKEYS = false;")
target.write_text(source, encoding="utf-8")
print("Developer-owned Telegram API credentials injected (redacted); official-app-only passkeys disabled.")
