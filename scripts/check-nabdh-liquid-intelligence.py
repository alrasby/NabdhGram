#!/usr/bin/env python3
"""Verify opt-in Liquid Glass and PRIVATE local text Lens in pinned Telegram."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

repo = Path(__file__).resolve().parent.parent
glass = (repo / "overlay/java/NabdhGlassStyle.java").read_text(encoding="utf-8")
lens = (repo / "overlay/java/NabdhContextLens.java").read_text(encoding="utf-8")
overlay = (repo / "scripts/apply-nabdh-liquid-intelligence.py").read_text(encoding="utf-8")
workflow = (repo / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")

def guard(test, message):
    if not test: raise SystemExit("FAIL Liquid Intelligence: " + message)

guard(all("public static final int " + label + " = " + str(index) in glass
          for index, label in enumerate(("SOFT", "LIQUID", "CRYSTAL"))),
      "three reversible styles missing")
guard("private static volatile int cachedStyle" in glass and
      "bubble_glass_style" in glass, "style cache/persistence missing")
guard("private static final int LIMIT = 8000;" in lens,
      "unbounded input")
guard(all(x in lens for x in ("summary(source)", "tasks(source)",
                             "linkSignals(source)", "cleanup(source)",
                             "detectLanguage(context, source)")),
      "local text actions missing")
guard("ClipboardManager" in lens and "setPrimaryClip" in lens,
      "explicit copy action absent")
guard(not any(x in lens for x in
              ("HttpURLConnection", "OkHttpClient", "Retrofit", "Socket(", "READ_CONTACTS", "READ_SMS")),
      "local helper unexpectedly accesses network or sensitive APIs")
guard("parentFragment.isSecretChat()" in overlay,
      "secret-chat exclusion missing")
guard("apply-nabdh-liquid-intelligence.py Telegram-upstream" in workflow and
      "check-nabdh-liquid-intelligence.py Telegram-upstream" in workflow,
      "actual pinned Telegram build not wired")
print("PASS: style cache, private Lens behavior and workflow contract")

if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
    sys.exit(0)
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-liquid-intelligence.py --self-test | TELEGRAM_SOURCE")
root = Path(sys.argv[1])
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
def read(path):
    f = ui / path
    guard(f.is_file(), "missing generated Java: " + path)
    return f.read_text(encoding="utf-8")

bubble = read("ActionBar/MessageDrawable.java")
composer = read("Components/ChatActivityEnterView.java")
hub = read("NabdhGramSettingsActivity.java")
page = read("NabdhGramFeatureCategoryActivity.java")
guard("NabdhGlassStyle.current()" in bubble and "nabdhStyle == 2" in bubble
      and "nabdhDrawFrostedWallpaper" in bubble,
      "native cached-path Liquid Glass not applied")
guard("private android.graphics.LinearGradient nabdhLiquidShader;" in bubble
      and "nabdhLiquidShader == null || nabdhLiquidStyleCache != style" in bubble
      and "nabdhLiquidMatrix.setTranslate(0, nabdhLiquidBounds.top);" in bubble
      and "nabdhDrawLiquidLight(canvas, bubblePath, nabdhStyle, accent);" in bubble,
      "native Liquid/Crystal gradient lacks theme/style cache or path alignment")
guard("NabdhContextLens.show" in composer and "isSecretChat()" in composer
      and "new AIEditorAlert" in composer, "composer lost safe integration or native AI Editor")
guard("NabdhIntelligenceTitle" in hub and "addNabdhLensTools" in page
      and "addNabdhGlassPresets" in page, "settings are not navigable")
guard("setLensEnabled" in read("Components/NabdhGlassStyle.java") and
      "No GENERATIVE model" in read("Components/NabdhContextLens.java") and
      "LanguageIdentification.getClient()" in read("Components/NabdhContextLens.java") and
      "classifier.close();" in read("Components/NabdhContextLens.java"),
      "bundled on-device ML language recognition or privacy controls missing")
for loc in ("values", "values-ar"):
    f = root / "TMessagesProj/src/main/res" / loc / "nabdh_liquid_intelligence.xml"
    guard(f.exists(), "missing locale " + loc)
    names = [node.get("name") for node in ET.parse(f).getroot()]
    guard(len(names) == len(set(names)), "duplicate resource " + loc)
    guard(all(n in names for n in ("NabdhSoftGlass", "NabdhLiquidGlass",
                                  "NabdhCrystalGlass", "NabdhLensPrivacyNote")),
          "missing resource in " + loc)
print("PASS: native generated Liquid Glass/Context Lens and localized UI")
