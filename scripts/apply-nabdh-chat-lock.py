#!/usr/bin/env python3
"""Install an opt-in per-chat PIN gate without touching Telegram login or transport."""
from pathlib import Path
from xml.sax.saxutils import escape
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-chat-lock.py TELEGRAM_SOURCE")

root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
templates = Path(__file__).resolve().parents[1] / "overlay/java"

for name, relative in (("NabdhChatLock.java", "Components/NabdhChatLock.java"),
                       ("NabdhChatLockActivity.java", "NabdhChatLockActivity.java")):
    target = ui / relative
    if target.exists():
        raise SystemExit("Chat lock: component collision: " + relative)
    target.write_bytes((templates / name).read_bytes())

def once(text, marker, replacement, label):
    found = text.count(marker)
    if found != 1:
        raise SystemExit(f"Chat lock {label}: expected 1 pinned anchor, got {found}")
    return text.replace(marker, replacement, 1)

manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
anchor = "        <!-- NabdhGram user-launched tools; never exported or reachable by implicit intents -->"
m = once(m, anchor, anchor + """
        <activity android:name="org.telegram.ui.NabdhChatLockActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />""",
         "private manager activity")
manifest.write_text(m, encoding="utf-8")

hub = ui / "NabdhGramSettingsActivity.java"
h = hub.read_text(encoding="utf-8")
anchor = """        nabdhExpandedButton(context, parent, R.string.NabdhExpandedChannelFeed,
                () -> context.startActivity(new android.content.Intent(
                        context, NabdhChannelFeedActivity.class)));"""
h = once(h, anchor, anchor + """
        nabdhExpandedButton(context, parent, R.string.NabdhChatLockTitle,
                () -> context.startActivity(new android.content.Intent(
                        context, NabdhChatLockActivity.class)));""", "manager entry")
hub.write_text(h, encoding="utf-8")

chat = ui / "ChatActivity.java"
s = chat.read_text(encoding="utf-8")
return_anchor = """        return fragmentView;
    }

    private void createSearchHashtagViewsIfNeeded() {"""
s = once(s, return_anchor, """        // Hide protected chat before the first frame, not after rendering.
        if (fragmentView != null && getParentActivity() != null
                && org.telegram.ui.Components.NabdhChatLock.isLocked(
                        getParentActivity(), currentAccount, dialog_id)
                && !org.telegram.ui.Components.NabdhChatLock.isUnlocked(
                        currentAccount, dialog_id)) {
            fragmentView.setVisibility(View.INVISIBLE);
        }
        return fragmentView;
    }

    private void createSearchHashtagViewsIfNeeded() {""", "pre-render gate")
resume = """    public void onResume() {
        super.onResume();
        checkShowBlur(false);"""
s = once(s, resume, """    public void onResume() {
        super.onResume();
        // Consent-based local PIN. No interception of messages, keys or calls.
        if (getParentActivity() != null &&
            org.telegram.ui.Components.NabdhChatLock.isLocked(
                    getParentActivity(), currentAccount, dialog_id)) {
            final android.app.Activity lockActivity = getParentActivity();
            if (fragmentView != null) fragmentView.setVisibility(View.INVISIBLE);
            lockActivity.getWindow().addFlags(
                    android.view.WindowManager.LayoutParams.FLAG_SECURE);
            org.telegram.ui.Components.NabdhChatLock.authenticate(
                    lockActivity, currentAccount, dialog_id,
                    () -> { if (fragmentView != null) fragmentView.setVisibility(View.VISIBLE); },
                    () -> finishFragment());
        }
        checkShowBlur(false);""", "resume PIN challenge")
pause = """    public void onPause() {
        super.onPause();
        scrolling = false;"""
s = once(s, pause, """    public void onPause() {
        super.onPause();
        if (getParentActivity() != null &&
            org.telegram.ui.Components.NabdhChatLock.isLocked(
                    getParentActivity(), currentAccount, dialog_id)) {
            getParentActivity().getWindow().clearFlags(
                    android.view.WindowManager.LayoutParams.FLAG_SECURE);
        }
        scrolling = false;""", "recents privacy lifecycle")
chat.write_text(s, encoding="utf-8")

for locale, title in (("values", "Chat locks (local PIN)"),
                      ("values-ar", "قفل المحادثات برمز محلي")):
    path = root / "TMessagesProj/src/main/res" / locale / "nabdh_chat_lock.xml"
    if path.exists():
        raise SystemExit("Chat lock resource collision")
    path.write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                    '    <string name="NabdhChatLockTitle">' +
                    escape(title) + '</string>\n</resources>\n', encoding="utf-8")

print("PASS: opt-in chat PIN manager, pre-render gate and FLAG_SECURE lifecycle installed")
