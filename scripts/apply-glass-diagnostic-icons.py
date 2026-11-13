#!/usr/bin/env python3
"""Give Telegram's Experimental/Debug settings rows native icon-backed alignment.

UI only. Preserve all UItem IDs, handlers, visibility conditions and localization.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-diagnostic-icons.py TELEGRAM_SOURCE")

root = Path(sys.argv[1]) / "TMessagesProj/src/main"
java = root / "java/org/telegram/ui/SettingsActivity.java"
source = java.read_text(encoding="utf-8")

# Distinct white vector pictograms for each native gradient icon background.
icons = {
    "video": '<path android:fillColor="#FFFFFFFF" android:pathData="M4,5h11c1.1,0 2,0.9 2,2v3l3,-2v8l-3,-2v3c0,1.1 -0.9,2 -2,2H4c-1.1,0 -2,-0.9 -2,-2V7c0,-1.1 0.9,-2 2,-2z"/>',
    "mic": '<path android:fillColor="#FFFFFFFF" android:pathData="M12,14a3,3 0,0 0,3 -3V5a3,3 0,0 0,-6 0v6a3,3 0,0 0,3 3zM17,11a5,5 0,0 1,-10 0H5a7,7 0,0 0,6 6.93V21h2v-3.07A7,7 0,0 0,19 11z"/>',
    "logs": '<path android:fillColor="#FFFFFFFF" android:pathData="M6,3h9l4,4v13a1,1 0,0 1,-1 1H6a1,1 0,0 1,-1 -1V4a1,1 0,0 1,1 -1zM14,4v4h4M8,11h8v1.6H8zM8,15h8v1.6H8z"/>',
    "history": '<path android:fillColor="#FFFFFFFF" android:pathData="M12,3a9,9 0,1 1,-8.7 11.3h2.2A7,7 0,1 0,5 12H8l-4,4 -4,-4h3a9,9 0,0 1,9 -9zM11,7h2v5l3,2 -1,1.7 -4,-2.7z"/>',
    "trash": '<path android:fillColor="#FFFFFFFF" android:pathData="M8,4h8l1,2h4v2H3V6h4zM5,9h14l-1,12H6zM9,11v7h2v-7zM13,11v7h2v-7z"/>',
}
for name, path_data in icons.items():
    target = root / "res/drawable" / ("nabdh_settings_" + name + ".xml")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    ''' + path_data + '''
</vector>
''', encoding="utf-8")

replacements = {
    '0, getString(R.string.RoundVideoSettings)))':
        'R.drawable.nabdh_settings_video, getString(R.string.RoundVideoSettings)))',
    '0, getString(R.string.AudioRecorderSettings)))':
        'R.drawable.nabdh_settings_mic, getString(R.string.AudioRecorderSettings)))',
    '0, getString(R.string.DebugSendLogs)))':
        'R.drawable.nabdh_settings_logs, getString(R.string.DebugSendLogs)))',
    '0, getString(R.string.DebugSendLastLogs)))':
        'R.drawable.nabdh_settings_history, getString(R.string.DebugSendLastLogs)))',
    '0, getString(R.string.DebugClearLogs)))':
        'R.drawable.nabdh_settings_trash, getString(R.string.DebugClearLogs)))',
}
for original, replacement in replacements.items():
    if source.count(original) != 1:
        raise SystemExit("Diagnostic setting row anchor changed: " + original)
    source = source.replace(original, replacement, 1)
java.write_text(source, encoding="utf-8")
print("Installed five native gradient-backed Experimental/Debug icons.")
