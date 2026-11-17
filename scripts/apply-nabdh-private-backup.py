#!/usr/bin/env python3
"""Release-only privacy policy: no backup/transfer of app-private session state.

Telegram's upstream BackupAgent includes 'saved_tokens' and
'saved_tokens_login'. Nabdh Camera originals also reside under filesDir.
No silent changes to Debug or Telegram login logic; this policy prevents
these private artifacts from being transferred through Android app backups.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

RULES = '''<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="root" path="." />
        <exclude domain="device_root" path="." />
        <exclude domain="external" path="." />
        <exclude domain="sharedpref" path="saved_tokens.xml" />
        <exclude domain="sharedpref" path="saved_tokens_login.xml" />
    </cloud-backup>
    <device-transfer>
        <exclude domain="root" path="." />
        <exclude domain="device_root" path="." />
        <exclude domain="external" path="." />
        <exclude domain="sharedpref" path="saved_tokens.xml" />
        <exclude domain="sharedpref" path="saved_tokens_login.xml" />
    </device-transfer>
</data-extraction-rules>
'''

def main(root):
    manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
    content = manifest.read_text(encoding="utf-8")
    original = 'android:allowBackup="true"'
    if content.count(original) != 1:
        raise SystemExit("FAIL Release backup: upstream allowBackup anchor changed")
    if "android:dataExtractionRules=" in content or "android:fullBackupContent=" in content:
        raise SystemExit("FAIL Release backup: upstream backup policy already configured")
    content = content.replace(original, '''android:allowBackup="false"
        android:fullBackupContent="false"
        android:dataExtractionRules="@xml/nabdh_private_backup_rules"''', 1)
    ET.fromstring(content)
    manifest.write_text(content, encoding="utf-8")
    folder = root / "TMessagesProj/src/main/res/xml"
    folder.mkdir(parents=True, exist_ok=True)
    rules = folder / "nabdh_private_backup_rules.xml"
    if rules.exists():
        raise SystemExit("FAIL Release backup: conflicting pre-existing rules")
    ET.fromstring(RULES)
    rules.write_text(RULES, encoding="utf-8")
    print("PASS: owner Release excludes token backups and app-private Camera gallery from Android cloud/device migration")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-nabdh-private-backup.py TELEGRAM_SOURCE")
    main(Path(sys.argv[1]).resolve())
