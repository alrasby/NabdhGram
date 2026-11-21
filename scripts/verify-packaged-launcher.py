#!/usr/bin/env python3
"""Audit the real packaged launcher resource, not only source or aapt icon existence."""
from pathlib import Path
import re
import subprocess
import sys

if len(sys.argv) != 5:
    raise SystemExit("Usage: verify-packaged-launcher.py APK BADGING RESOURCES AAPT")
apk, badging_file, resources_file, tool = map(Path, sys.argv[1:])
badging = badging_file.read_text(encoding="utf-8")
resources = resources_file.read_text(encoding="utf-8")

def fail(msg):
    raise SystemExit("FAIL: installed launcher may still be Telegram: " + msg)

paths = re.findall(r"^application-icon-\d+:'([^']+)'", badging, re.M)
if not paths:
    fail("aapt did not report a packaged icon path")
path = next((p for p in paths if p.endswith(".xml")), paths[0])
if not path.endswith(".xml"):
    fail("Android 26+ default icon is not an adaptive XML: " + path)
result = subprocess.run([str(tool), "dump", "xmltree", str(apk), path],
                        capture_output=True, text=True, timeout=40)
if result.returncode:
    fail("aapt cannot inspect packaged adaptive icon XML: " + path)
if "adaptive-icon" not in result.stdout:
    fail("package reports an icon XML with no adaptive-icon element")
# Binary Android XML represents <foreground android:drawable="@..."/> as
# an E: foreground element followed by A: android:drawable, not an
# android:foreground attribute on the adaptive-icon parent.
foreground_element = re.search(r"(?m)^\s*E: foreground\\b[^\\n]*", result.stdout)
if not foreground_element:
    fail("adaptive foreground element missing in compiled icon")
fragment = result.stdout[foreground_element.end():foreground_element.end() + 400]
match = re.search(r"android:drawable[^\\n]*?@0x([0-9a-fA-F]+)", fragment)
if not match:
    fail("adaptive foreground drawable resource missing in compiled icon")
actual_id = "0x" + match.group(1).lower().zfill(8)
expected = re.search(r"(?:spec )?resource\s+(0x[0-9a-fA-F]+)\s+[^\n]*:drawable/nabdhgram_launcher_foreground\b",resources)
if not expected:
    fail("approved NabdhGram adaptive foreground not in compiled resource table")
expected_id = "0x" + expected.group(1).lower().zfill(8)
if actual_id != expected_id:
    fail("default icon adaptive foreground is NOT the NabdhGram image; actual "
         + actual_id + " versus approved " + expected_id)
print("PASS: compiled first-install launcher icon foreground is approved NabdhGram adaptive artwork")
