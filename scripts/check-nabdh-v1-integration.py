#!/usr/bin/env python3
"""Fail-closed source integration checks for explicit local V1 tools."""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
engine = (ROOT / "overlay/java/NabdhV1Engine.java").read_text(encoding="utf-8")
workspace = (ROOT / "overlay/java/NabdhWorkspace.java").read_text(encoding="utf-8")
lens = (ROOT / "overlay/java/NabdhContextLens.java").read_text(encoding="utf-8")
overlay = (ROOT / "scripts/apply-nabdh-v1-signatures.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")


def check(condition, why):
    if not condition:
        raise SystemExit("FAIL V1 local tools: " + why)


check("NabdhV1Engine.focus(source, arabic())" in lens and
      "NabdhV1Engine.catchUp(source, arabic())" in lens and
      "NabdhV1Engine.shield(source, arabic())" in lens,
      "opt-in original native Context Lens lacks all V1 tools")
check("NabdhWorkspace.saveWithFeedback(context, source, arabic())" in lens and
      "NabdhWorkspace.show(context, arabic())" in lens,
      "encrypted workspace not accessible on explicit action")
check("AndroidKeyStore" in workspace and "AES/GCM/NoPadding" in workspace and
      "setRandomizedEncryptionRequired(true)" in workspace and
      "Cipher.DECRYPT_MODE" in workspace and "Cipher.ENCRYPT_MODE" in workspace,
      "Workspace must use strong platform-keystore authenticated encryption")
check("context.getSharedPreferences(FILE, Context.MODE_PRIVATE)" in workspace and
      "putString(DATA, envelope)" in workspace and "putString(DATA, value)" not in workspace,
      "Workspace must not persist plaintext")
check("NabdhV1Engine.bounded(text)" in workspace and
      "private static final int MAX_ENTRY = 1600;" in workspace and
      "private static final int LIMIT = 40;" in workspace,
      "private workspace data budget missing")
check(not any(term in (engine + workspace) for term in (
      "HttpURLConnection", "OkHttpClient", "Retrofit", "Socket(", "READ_SMS",
      "READ_CONTACTS", "READ_MEDIA", "getAllDialogs", "getMessagesController()")),
      "V1 local tools unexpectedly process background chats or network")
check("MAX_INPUT = 8000" in engine and "No basic signals detected; this does NOT mean safe." in engine,
      "input bound or URL safety disclaimer missing")
check("NabdhShieldTitle" in overlay and "NabdhProductivityTitle" in overlay and
      "NabdhWorkspace.show(" in overlay,
      "V1 tools lack real user-facing category actions")
check("apply-nabdh-v1-signatures.py Telegram-upstream" in workflow and
      "check-nabdh-v1-integration.py Telegram-upstream" in workflow,
      "Native v1 overlay not installed/checked before building")
if sys.argv[1:] == ["--self-test"]:
    print("PASS: privacy, AES-GCM storage and native V1 overlay source contracts")
    raise SystemExit(0)
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-v1-integration.py --self-test | TELEGRAM_SOURCE")
target = Path(sys.argv[1])
ui = target / "TMessagesProj/src/main/java/org/telegram/ui"
for name in ("NabdhV1Engine", "NabdhWorkspace"):
    f = ui / "Components" / (name + ".java")
    check(f.is_file(), "Missing generated " + name)
    check(f.read_text(encoding="utf-8") == (ROOT / "overlay/java" / (name + ".java")).read_text(encoding="utf-8"),
          name + " differs from pinned template")
page = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
for symbol in ("addNabdhV1Tools", "NabdhShieldTitle", "NabdhProductivityTitle",
               "NabdhV1Engine.focus", "NabdhV1Engine.catchUp",
               "NabdhV1Engine.shield", "NabdhWorkspace.saveWithFeedback"):
    check(symbol in page, "Missing native UI action: " + symbol)
for locale in ("values", "values-ar"):
    src = target / "TMessagesProj/src/main/res" / locale / "nabdh_v1_tools.xml"
    check(src.is_file(), "V1 translation not installed: " + locale)
    root = ET.parse(src).getroot()
    names = [node.attrib.get("name") for node in root]
    check(len(names) == len(set(names)), "Duplicate translation: " + locale)
    for key in ("NabdhV1Focus", "NabdhV1CatchUp", "NabdhV1Shield", "NabdhV1Save",
                "NabdhV1OpenWorkspace", "NabdhV1ManualDisclosure", "NabdhV1Empty"):
        check(key in names, "Missing translated Android resource: " + key)
print("PASS: generated native local tools, opt-in UI controls and AR/EN resources")
