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

# The Contacts tab is itself a persistent main navigation destination. Do not
# ask for address-book access merely because the user switches to that tab.
contacts = p.parent / "ContactsActivity.java"
s = contacts.read_text(encoding="utf-8")
old = 'checkPermission = UserConfig.getInstance(currentAccount).syncContacts;'
new = 'checkPermission = !hasMainTabs && UserConfig.getInstance(currentAccount).syncContacts;'
# hasMainTabs is populated from arguments later in onFragmentCreate, so use
# a post-arguments guard instead of changing the earlier initialization.
if s.count(old) != 1:
    raise SystemExit("ContactsActivity initial permission check anchor changed")
anchor = '    public boolean onFragmentCreate() {'
if s.count(anchor) != 1:
    raise SystemExit("ContactsActivity onFragmentCreate anchor changed")
# The tab argument is parsed in onFragmentCreate, so suppress its permission
# request at the actual visibility check, leaving standalone selection intact.
old = 'if (checkPermission && Build.VERSION.SDK_INT >= 23) {'
new = 'if (checkPermission && !hasMainTabs && Build.VERSION.SDK_INT >= 23) {'
if s.count(old) != 1:
    raise SystemExit("ContactsActivity visibility permission anchor changed")
s = s.replace(old, new, 1)
contacts.write_text(s, encoding="utf-8")

# Exact origin of the red ! icon in the supplied video: the contacts tab
# counter is set by MainTabsActivity.checkContactsTabBadge().
tabs = p.parent / "MainTabsActivity.java"
s = tabs.read_text(encoding="utf-8")
start = s.index("    private void checkContactsTabBadge() {")
end = s.index("\n    @Override\n    public void onPause()", start)
old_block = s[start:end]
if 'tabs[INDEX_CONTACTS].setCounter("!", true, true);' not in old_block:
    raise SystemExit("Contacts badge source changed")
new_block = '''    private void checkContactsTabBadge() {
        // Contacts permission is optional. Never show a red warning badge
        // merely because the user has not granted address-book access.
        if (tabsView != null && tabs[INDEX_CONTACTS] != null) {
            tabs[INDEX_CONTACTS].setCounter(null, true, true);
        }
    }
'''
s = s[:start] + new_block + s[end:]
tabs.write_text(s, encoding="utf-8")
print("Automatic contacts prompts and contacts permission warning badge disabled.")

