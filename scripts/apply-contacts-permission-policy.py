#!/usr/bin/env python3
"""Disable automatic contacts-permission nags on the main chats screen.

Keep READ_CONTACTS in the manifest and explicit contacts import/permission
flows intact. Other permissions (notifications/media) remain unchanged.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-contacts-permission-policy.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java"
s = p.read_text(encoding="utf-8")
replacements = [
    (
        'private boolean askAboutContacts = true;',
        'private boolean askAboutContacts = false; // NabdhGram: no automatic contacts prompt',
    ),
    (
        'askAboutContacts = MessagesController.getGlobalNotificationsSettings().getBoolean("askAboutContacts", true);',
        'askAboutContacts = false; // Explicit contacts actions can still request access',
    ),
]
for old, new in replacements:
    if s.count(old) != 1:
        raise SystemExit(f"Contacts policy anchor changed: {old!r} ({s.count(old)} matches)")
    s = s.replace(old, new, 1)
# The main dialog onResume uses hasNotContactsPermission to decide whether
# to start the permission sequence; ignore missing contacts permission only.
old = 'boolean hasNotContactsPermission = activity.checkSelfPermission(Manifest.permission.READ_CONTACTS) != PackageManager.PERMISSION_GRANTED;'
new = 'boolean hasNotContactsPermission = false; // Do not nag on opening chats'
if s.count(old) != 1:
    raise SystemExit("Contacts auto-check anchor changed")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("Automatic contacts permission prompts disabled; explicit access retained.")
