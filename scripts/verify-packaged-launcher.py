#!/usr/bin/env python3
"""Audit the real packaged launcher resource, not only source or aapt icon existence."""
from io import BytesIO
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile
from PIL import Image

if len(sys.argv) != 6:
    raise SystemExit("Usage: verify-packaged-launcher.py APK BADGING RESOURCES MANIFEST AAPT")
apk, badging_file, resources_file, manifest_file, tool = map(Path, sys.argv[1:])
badging = badging_file.read_text(encoding="utf-8")
resources = resources_file.read_text(encoding="utf-8")

def fail(msg):
    raise SystemExit("FAIL: packaged launcher verification: " + msg)

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
foreground_element = re.search(r"(?m)^\s*E: foreground\b[^\n]*", result.stdout)
if not foreground_element:
    fail("adaptive foreground element missing in compiled icon")
fragment = result.stdout[foreground_element.end():foreground_element.end() + 400]
match = re.search(r"android:drawable[^\n]*?@0x([0-9a-fA-F]+)", fragment)
if not match:
    fail("adaptive foreground drawable resource missing in compiled icon")
actual_id = "0x" + match.group(1).lower().zfill(8)
expected = re.search(r"(?:spec )?resource\s+(0x[0-9a-fA-F]+)\s+[^\n]*:drawable/nabdhgram_launcher_icon_foreground\b",resources)
if not expected:
    fail("approved NabdhGram adaptive foreground not in compiled resource table")
expected_id = expected.group(1).lower()
if actual_id != expected_id:
    fail("default icon adaptive foreground is NOT the NabdhGram image; actual "
         + actual_id + " versus approved " + expected_id)
print("PASS: compiled first-install launcher icon foreground is approved NabdhGram adaptive artwork")
# The selected Default alias and the application fallback must share the teal
# adaptive background; reject transparent/black platform fallback resources.
background_element = re.search(r"(?m)^\s*E: background\b[^\n]*", result.stdout)
if not background_element:
    fail("Default adaptive icon missing branded background layer")
fragment = result.stdout[background_element.end():background_element.end() + 400]
background_value = re.search(r"android:drawable[^\n]*?@0x([0-9a-fA-F]+)", fragment)
expected_color = re.search(
    r"(?:spec )?resource\s+(0x[0-9a-fA-F]+)\s+[^\n]*:color/nabdhgram_icon_background\b",
    resources)
if not background_value or not expected_color:
    fail("Default adaptive icon background is not a named brand-color resource")
if int(background_value.group(1), 16) != int(expected_color.group(1), 16):
    fail("Default launcher background resolves to the wrong resource")
print("PASS: compiled Default launcher has the explicit teal adaptive background")

# The launchable DefaultIcon activity alias has its OWN icon attribute.
# Checking only the application icon previously missed the paper-plane when
# a fresh install entered the app through the activity-alias.
manifest = manifest_file.read_text(encoding="utf-8")
blocks = re.split(r"(?m)^\s*E: activity-alias\b", manifest)
defaults = [b for b in blocks[1:] if "org.telegram.messenger.DefaultIcon" in b]
if len(defaults) != 1:
    fail("compiled DefaultIcon launcher alias missing or ambiguous")
default = defaults[0]
for attr, resource_name in (
    ("icon", "mipmap/nabdhgram_launcher"),
    ("roundIcon", "mipmap/nabdhgram_launcher_round"),
):
    ref = re.search(r"android:" + attr + r"\b[^\n]*?@0x([0-9a-fA-F]+)", default)
    expected_ref = re.search(
        r"(?m)^\s*spec resource\s+(0x[0-9a-fA-F]+)\s+[^\n]*:"
        + re.escape(resource_name) + r":", resources)
    if not ref or not expected_ref:
        fail("compiled DefaultIcon missing resource: " + resource_name)
    if int(ref.group(1), 16) != int(expected_ref.group(1), 16):
        fail("compiled DefaultIcon " + attr + " resolves to Telegram, not " + resource_name)
print("PASS: compiled DefaultIcon activity-alias uses owner NabdhGram standard and round launcher")



# Release resource shrinking can shorten packaged file names. AAPT2
# reports each compiled file entry under its stable resource ID.
table = subprocess.run([str(tool.with_name("aapt2")), "dump", "resources", str(apk)],
                       capture_output=True, text=True, timeout=90)
if table.returncode:
    fail("aapt2 could not inspect the compiled resource table")
file_entries = {}
resource_id = None
for line in table.stdout.splitlines():
    header = re.match(r"\s*resource (0x[0-9a-fA-F]+)\b", line)
    if header:
        resource_id = int(header.group(1), 16)
    elif resource_id is not None:
        entry = re.search(r"\(file\)\s+(\S+)", line)
        if entry:
            file_entries.setdefault(resource_id, set()).add(entry.group(1))

# Check installed resources for the original user-selectable aliases.
# A correct in-app preview is not enough: the launcher uses each alias's
# android:icon/roundIcon from the packaged merged manifest.
for activity, mipmap in (
    ("NabdhSilverCircleIcon", "nabdh_icon_silver"),
    ("NabdhDarkCircleIcon", "nabdh_icon_dark"),
    ("NabdhGlassCircleIcon", "nabdh_icon_glass"),
    ("NabdhIphoneIcon", "nabdh_icon_iphone"),
):
    matches = [b for b in blocks[1:] if
               ("org.telegram.messenger." + activity) in b]
    if len(matches) != 1:
        fail("missing or duplicate selectable launcher alias: " + activity)
    for attr in ("icon", "roundIcon"):
        icon_ref = re.search(r"android:" + attr + r"\b[^\n]*?@0x([0-9a-fA-F]+)",
                             matches[0])
        expected_ref = re.search(
            r"(?m)^\s*spec resource\s+(0x[0-9a-fA-F]+)\s+[^\n]*:"
            + re.escape("mipmap/" + mipmap) + r":", resources)
        if not icon_ref or not expected_ref:
            fail(activity + ": compiled launcher icon resource missing: " + attr)
        if int(icon_ref.group(1), 16) != int(expected_ref.group(1), 16):
            fail(activity + ": launcher maps to wrong resource " + attr)
    icon_files = file_entries.get(int(expected_ref.group(1), 16), set())
    modern = [entry for entry in icon_files if entry.endswith(".xml")]
    if len(modern) != 1:
        fail(activity + ": expected one modern adaptive icon XML in the resource table")
    compiled = subprocess.run([str(tool), "dump", "xmltree", str(apk), modern[0]],
                              capture_output=True, text=True, timeout=40)
    if compiled.returncode or "E: adaptive-icon" not in compiled.stdout:
        fail(activity + ": invalid compiled adaptive icon XML")
    for layer in ("background", "foreground"):
        element = re.search(r"(?m)^\s*E: " + layer + r"\b[\s\S]*?(?=^\s*E: |\Z)",
                            compiled.stdout)
        ref = re.search(r"android:drawable[^\n]*?@0x([0-9a-fA-F]+)", element.group(0)) if element else None
        expected = re.search(
            r"(?m)^\s*spec resource\s+(0x[0-9a-fA-F]+)\s+[^\n]*:drawable/"
            + re.escape(mipmap + "_" + layer) + r":", resources)
        if not ref or not expected or int(ref.group(1), 16) != int(expected.group(1), 16):
            fail(activity + ": compiled adaptive " + layer + " points to the wrong artwork")
        layer_files = file_entries.get(int(ref.group(1), 16), set())
        if not layer_files:
            fail(activity + ": compiled adaptive " + layer + " has no packaged file")
        if layer == "background":
            with ZipFile(apk) as package:
                for entry in layer_files:
                    with Image.open(BytesIO(package.read(entry))) as bitmap:
                        if bitmap.convert("RGBA").getchannel("A").getextrema() != (255, 255):
                            fail(activity + ": adaptive backing is not completely opaque")
print("PASS: all four selectable aliases have installed opaque adaptive backing and approved artwork")
