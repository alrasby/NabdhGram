#!/usr/bin/env python3
"""Fail-closed source integration checks for explicit local V1 tools."""
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
engine = (ROOT / "overlay/java/NabdhV1Engine.java").read_text(encoding="utf-8")
workspace = (ROOT / "overlay/java/NabdhWorkspace.java").read_text(encoding="utf-8")
fileguard = (ROOT / "overlay/java/NabdhFileGuard.java").read_text(encoding="utf-8")
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
check("public static String scam(CharSequence input, boolean ar)" in engine
      and "NabdhV1Engine.scam(value, arabic)" in overlay,
      "local opt-in scam indicators not connected to native V1 actions")
check("public static String inspect(" in fileguard
      and "byte[] header" in fileguard
      and "No known mismatch found" in fileguard,
      "manual file guard lacks bounded file-header check and safety disclaimer")
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
      "NabdhNetworkTitle" in overlay and "new DataSettingsActivity()" in overlay and
      "new CacheControlActivity()" in overlay and "new ProxyListActivity()" in overlay and
      "NabdhWorkspace.show(" in overlay,
      "V1 tools lack real user-facing category actions")
hierarchy = (ROOT / "scripts/apply-nabdh-v1-hierarchy.py").read_text(encoding="utf-8")
check("apply-nabdh-v1-hierarchy.py Telegram-upstream" in workflow,
      "hierarchical feature routing overlay not installed")
for contract in ("featureId == 0", "nabdhFeatureRow", "NabdhHShieldOverview",
                 "NabdhHAppearanceOverview", "featureId == 601",
                 "featureId == 201", "featureId == 301", "featureId == 302",
                 "featureId == 303", "featureId == 501", "featureId == 502",
                 "featureId == 503", "NabdhGlassRowDecoration.newCardBackground()",
                 "ACTION_OPEN_DOCUMENT", "NabdhFileGuard.inspect",
                 "NabdhHChooseFile", "featureId == 103"):
    check(contract in hierarchy, "missing hierarchy / retained-control contract: " + contract)

# Prevent Liquid Glass presets from leaking into the parent Appearance page
# and its Fonts subpage (all three share the same titleRes).
check('if (featureId == 602) {' in hierarchy
      and 'addNabdhGlassPresets(context, content);' in hierarchy
      and 'exclusive Glass presets detail routing' in hierarchy,
      "Glass presets are not explicitly routed to the Themes detail")

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
for name in ("NabdhV1Engine", "NabdhWorkspace", "NabdhFileGuard"):
    f = ui / "Components" / (name + ".java")
    check(f.is_file(), "Missing generated " + name)
    check(f.read_text(encoding="utf-8") == (ROOT / "overlay/java" / (name + ".java")).read_text(encoding="utf-8"),
          name + " differs from pinned template")
page = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
# Exactly one route: featureId 602 = Appearance > Glass Themes. Both the
# Appearance index (0) and Fonts (601) must remain free of preset controls.
glass_route = re.findall(
    r"if\\s*\\(\\s*featureId\\s*==\\s*602\\s*\\)\\s*\\{\\s*addNabdhGlassPresets\\(context, content\\);\\s*\\}",
    page)
check(len(glass_route) == 1
      and page.count("addNabdhGlassPresets(context, content);") == 1
      and not re.search(
          r"if\\s*\\(\\s*titleRes\\s*==\\s*R\\.string\\.NabdhAppearanceTitle\\s*\\)"
          r"\\s*\\{\\s*addNabdhGlassPresets\\(",
          page),
      "Glass presets must appear only under Appearance > Glass Themes, not index/fonts")
check("if (featureId == 601)" in page and "addNabdhFeatureMenu(context, content);" in page,
      "Appearance fonts and navigation must remain independent of themes")
for symbol in ("addNabdhV1Tools", "addNabdhNetworkTools", "NabdhShieldTitle", "NabdhProductivityTitle", "NabdhNetworkTitle",
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
for contract in ("private final int featureId;", "addNabdhFeatureMenu(context, content);",
                 "nabdhFeatureRow(context, content, 101);",
                 "nabdhFeatureRow(context, content, 201);",
                 "nabdhFeatureRow(context, content, 301);",
                 "nabdhFeatureRow(context, content, 401);",
                 "nabdhFeatureRow(context, content, 501);",
                 "nabdhFeatureRow(context, content, 601);",
                 "if (featureId == 601)", "if (featureId == 201)",
                 "if (featureId == 302)", "if (featureId == 303)",
                 "if (featureId == 501)", "if (featureId == 502)",
                 "if (featureId == 503)", "featureId == 103",
                 "NabdhFileGuard.inspect"):
    check(contract in page, "generated hierarchy missing: " + contract)
for locale in ("values", "values-ar"):
    resource = target / "TMessagesProj/src/main/res" / locale / "nabdh_v1_hierarchy.xml"
    check(resource.is_file(), "hierarchy translations missing: " + locale)
    nodes = ET.parse(resource).getroot()
    keys = [n.attrib.get("name") for n in nodes]
    check(len(keys) == len(set(keys)), "duplicate hierarchy resource: " + locale)
    for key in ("NabdhHLinks", "NabdhHFiles", "NabdhHScam", "NabdhHPreview",
                "NabdhHWorkspace", "NabdhHVoice", "NabdhHData",
                "NabdhHFonts", "NabdhHThemes", "NabdhHStatusPending",
                "NabdhHChooseFile", "NabdhHFileError"):
        check(key in keys, "missing " + locale + " label: " + key)
check("if (titleRes == R.string.NabdhShieldTitle) {" not in page.split("private void addNabdhV1Tools",1)[1].split("private int nabdhCategoryDescription",1)[0],
      "shield actions must route by selected feature, not parent category")

print("PASS: generated native local tools, opt-in UI controls and AR/EN resources")
