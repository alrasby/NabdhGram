#!/usr/bin/env python3
"""Opt-in recents screenshot protection on Android 13+, without FLAG_SECURE."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-privacy-screen.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
page = root / "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramSettingsActivity.java"
launch = root / "TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java"
s = page.read_text(encoding="utf-8")
anchor = "        section(context, content, R.string.NabdhPrivacyTitle, R.string.NabdhPrivacyExplanation);"
if s.count(anchor) != 1:
    raise SystemExit("NabdhGram privacy section anchor changed")
s = s.replace(anchor, anchor + '''
        android.widget.CheckBox privacyToggle = new android.widget.CheckBox(context);
        privacyToggle.setText(context.getString(R.string.NabdhPrivacyScreenToggle));
        privacyToggle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        privacyToggle.setChecked(context.getSharedPreferences("nabdhgram_privacy", Context.MODE_PRIVATE)
                .getBoolean("hide_recents", false));
        privacyToggle.setEnabled(android.os.Build.VERSION.SDK_INT >= 33);
        privacyToggle.setOnCheckedChangeListener((button, checked) -> {
            context.getSharedPreferences("nabdhgram_privacy", Context.MODE_PRIVATE)
                    .edit().putBoolean("hide_recents", checked).apply();
            if (android.os.Build.VERSION.SDK_INT >= 33 && getParentActivity() != null) {
                getParentActivity().setRecentsScreenshotEnabled(!checked);
            }
        });
        content.addView(privacyToggle);
        TextView privacyNote = new TextView(context);
        privacyNote.setText(context.getString(R.string.NabdhPrivacyScreenNote));
        privacyNote.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        content.addView(privacyNote);
''', 1)
page.write_text(s, encoding="utf-8")
s = launch.read_text(encoding="utf-8")
anchor = "    protected void onResume() {\n        super.onResume();"
if s.count(anchor) != 1:
    raise SystemExit("Pinned upstream LaunchActivity.onResume anchor changed")
s = s.replace(anchor, anchor + '''
        // Opt-in: suppress only the system's Recents snapshot on Android 13+.
        // Do not use FLAG_SECURE: normal screenshots remain available.
        if (android.os.Build.VERSION.SDK_INT >= 33) {
            boolean hideRecents = getSharedPreferences("nabdhgram_privacy", MODE_PRIVATE)
                    .getBoolean("hide_recents", false);
            setRecentsScreenshotEnabled(!hideRecents);
        }
''', 1)
launch.write_text(s, encoding="utf-8")
for lang, title, note in [
    ("values", "Hide app preview in Recents", "Android 13+ only. Hides new Recents snapshots, not screenshots taken normally. Existing snapshots may persist until refreshed."),
    ("values-ar", "إخفاء معاينة التطبيق في التطبيقات الأخيرة", "متاح على Android 13 والأحدث. يمنع لقطات المعاينة الجديدة، ولا يمنع لقطات الشاشة العادية. قد تبقى المعاينات القديمة حتى تتجدد.")
]:
    f = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    x = f.read_text(encoding="utf-8")
    if x.count("</resources>") != 1:
        raise SystemExit("NabdhGram settings XML changed: " + str(f))
    from xml.sax.saxutils import escape
    x = x.replace("</resources>", '    <string name="NabdhPrivacyScreenToggle">' + escape(title) + '</string>\n' +
                  '    <string name="NabdhPrivacyScreenNote">' + escape(note) + '</string>\n</resources>')
    f.write_text(x, encoding="utf-8")
print("Installed opt-in Privacy Screen Recents snapshot toggle for Android 13+.")
