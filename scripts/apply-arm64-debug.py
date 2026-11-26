#!/usr/bin/env python3
"""Limit the pinned Telegram AFAT debug build to arm64-v8a for phone testing."""
from pathlib import Path
import sys

if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != "--emulator"):
    raise SystemExit("Usage: apply-arm64-debug.py TELEGRAM_SOURCE [--emulator]")
p = Path(sys.argv[1]) / "TMessagesProj_App/build.gradle"
s = p.read_text(encoding="utf-8")
anchor = '''        afat {
            ndk {
                abiFilters "armeabi-v7a", "arm64-v8a", "x86", "x86_64"
            }'''
replacement = '''        afat {
            ndk {
                abiFilters "arm64-v8a"
            }'''
abi = "x86_64" if len(sys.argv) == 3 else "arm64-v8a"
replacement = replacement.replace("arm64-v8a", abi)
if s.count(anchor) != 1:
    raise SystemExit(f"Expected one pinned afat flavor ABI declaration, found {s.count(anchor)}")
p.write_text(s.replace(anchor, replacement, 1), encoding="utf-8")
print(f"Experimental afat build limited to {abi}.")
