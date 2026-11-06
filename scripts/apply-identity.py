#!/usr/bin/env python3
"""Apply the minimal, reproducible NabdhGram identity changes to a pinned Telegram checkout.

Does not modify the original repository or include API credentials.
Usage: python3 scripts/apply-identity.py /path/to/Telegram-upstream
"""
from pathlib import Path
import sys

APP_ID = "net.nabdhserv.nabdhgram"
LABEL = "NabdhGram"

def replace_once(path, before, after):
    text = path.read_text(encoding="utf-8")
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"Expected one match in {path}: {before!r}; found {count}")
    path.write_text(text.replace(before, after), encoding="utf-8")

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-identity.py TELEGRAM_SOURCE_DIRECTORY")
    root = Path(sys.argv[1]).resolve()
    props = root / "gradle.properties"
    app = root / "TMessagesProj_App" / "build.gradle"
    if not props.is_file() or not app.is_file():
        raise SystemExit("Not a Telegram Android source tree")
    replace_once(props, "APP_PACKAGE=org.telegram.messenger", f"APP_PACKAGE={APP_ID}")
    # Debug builds use .beta upstream. Keep this suffix for initial development builds.
    # Override the launcher label in an app-level resource overlay without touching translations.
    values = root / "TMessagesProj_App" / "src" / "main" / "res" / "values"
    values.mkdir(parents=True, exist_ok=True)
    label_file = values / "nabdhgram_identity.xml"
    if label_file.exists():
        raise SystemExit(f"Refusing to overwrite existing resource: {label_file}")
    label_file.write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="NabdhGramAppName">NabdhGram</string>\n</resources>\n', encoding="utf-8")
    # The pinned upstream already has an application-module manifest. Edit its
    # existing <application> element rather than creating a second manifest.
    manifest = root / "TMessagesProj_App" / "src" / "main" / "AndroidManifest.xml"
    if not manifest.is_file():
        raise SystemExit(f"Expected upstream app manifest missing: {manifest}")
    xml = manifest.read_text(encoding="utf-8")
    import re
    match = re.search(r"<application\b[^>]*>", xml, flags=re.DOTALL)
    if not match:
        raise SystemExit("No <application> element in upstream app manifest")
    tag = match.group(0)
    if 'android:label=' in tag:
        tag = re.sub(r'android:label="[^"]*"', 'android:label="@string/NabdhGramAppName"', tag, count=1)
    else:
        tag = tag[:-1] + ' android:label="@string/NabdhGramAppName">'
    if 'tools:replace=' in tag:
        tag = re.sub(r'tools:replace="([^"]*)"', lambda m: 'tools:replace="' + (m.group(1) if 'android:label' in m.group(1).split(',') else m.group(1) + ',android:label') + '"', tag, count=1)
    else:
        tag = tag[:-1] + ' tools:replace="android:label">'
    xml = xml[:match.start()] + tag + xml[match.end():]
    manifest.write_text(xml, encoding="utf-8")
    # The afat debug flavor uses a separate higher-priority manifest. Its
    # application label must agree with the main app manifest or merger fails.
    debug_manifest = root / "TMessagesProj" / "config" / "debug" / "AndroidManifest_SDK23.xml"
    if not debug_manifest.is_file():
        raise SystemExit(f"Expected debug manifest missing: {debug_manifest}")
    debug_xml = debug_manifest.read_text(encoding="utf-8")
    debug_xml = debug_xml.replace('android:label="@string/AppNameBeta"', 'android:label="@string/NabdhGramAppName"')
    if debug_xml == debug_manifest.read_text(encoding="utf-8"):
        raise SystemExit("Expected upstream debug application label was not found")
    debug_xml = debug_xml.replace('tools:replace="android:supportsRtl"', 'tools:replace="android:supportsRtl,android:label"')
    debug_manifest.write_text(debug_xml, encoding="utf-8")
    print(f"Identity overlay applied: {APP_ID}.beta / {LABEL}")
    print("NOTE: This does not yet apply approved icon assets or configure private Telegram API credentials.")

if __name__ == "__main__":
    main()
