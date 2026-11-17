#!/usr/bin/env python3
"""Minimize Play-only Release permissions without changing working Debug builds.

Google Play disallows ordinary messaging apps using REQUEST_INSTALL_PACKAGES
for self-updates. READ_CALL_LOG is restricted to qualifying default dialer
apps; Telegram's outgoing/in-app VoIP does not require a full device call log.
Only run after the overlay checks, and before signed Release manifest merging.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

EXPECTED = {
    "TMessagesProj/src/main/AndroidManifest.xml":
        ('    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />\n',),
    "TMessagesProj/config/release/AndroidManifest_SDK23.xml":
        ('    <uses-permission android:name="android.permission.READ_CALL_LOG" />\n',),
}
DANGEROUS = ("REQUEST_INSTALL_PACKAGES", "READ_CALL_LOG")


def apply(root):
    for path, removals in EXPECTED.items():
        file = root / path
        data = file.read_text(encoding="utf-8")
        for unwanted in removals:
            if data.count(unwanted) != 1:
                raise SystemExit("Release permission overlay upstream drift: " + path)
            data = data.replace(unwanted, "", 1)
        # Validate the file before overwriting, even if build checks are skipped.
        ET.fromstring(data)
        file.write_text(data, encoding="utf-8")
    for rel in ("TMessagesProj/src/main/AndroidManifest.xml",
                "TMessagesProj/config/release/AndroidManifest.xml",
                "TMessagesProj/config/release/AndroidManifest_SDK23.xml"):
        tree = ET.parse(root / rel)
        permissions = [node.get("{http://schemas.android.com/apk/res/android}name", "")
                       for node in tree.getroot().findall("uses-permission")]
        for banned in DANGEROUS:
            if "android.permission." + banned in permissions:
                raise SystemExit("Play Release contains restricted permission: " + banned)
    print("PASS: Play Release permission policy: no app-install or call-log scope")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-nabdh-play-permissions.py TELEGRAM_SOURCE")
    apply(Path(sys.argv[1]).resolve())
