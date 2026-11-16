#!/usr/bin/env python3
"""Verify V1 exposes only usable features; preserve postponed code for V2."""
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[1]
flags = (repo / "overlay/java/NabdhFeatureGates.java").read_text(encoding="utf-8")
patch = (repo / "scripts/apply-nabdh-feature-visibility.py").read_text(encoding="utf-8")
ai = (repo / "overlay/java/NabdhAiActivity.java").read_text(encoding="utf-8")
workflow = (repo / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")

def check(ok, reason):
    if not ok:
        raise SystemExit("FAIL V1 feature visibility: " + reason)

check("id != 203 && id != 401" in flags
      and "verifiedAiChat(Context context)" in flags
      and "noteVerifiedAiInference(Context context)" in flags
      and "PUBLIC_AI_RELEASE_ACCEPTED = false" in flags
      and "publicAiEnabled(Context context)" in flags,
      "deferred IDs and verified model gate must remain explicit")
check("203, 401" in patch
      and "NabdhAiChatLaunch" in patch
      and "NabdhFeatureGates.verifiedAiChat(context)" in patch
      and "NabdhGramSettingsActivity.java" in patch
      and "NabdhIntelligenceTitle" in patch
      and "NabdhFeatureGates.publicAiEnabled(context)" in patch,
      "unimplemented pages or unverified AI Chat still visible")
check("NabdhFeatureGates.verifiedAiChat(this)" in ai
      and "NabdhFeatureGates" in ai
      and "noteVerifiedAiInference(NabdhAiActivity.this)" in ai
      and 'payload.containsKey(NabdhAiCoreService.NANO_CAN_DOWNLOAD)' in ai,
      "AI Chat must unlock only on real, non-status on-device model output")
check("apply-nabdh-feature-visibility.py Telegram-upstream" in workflow
      and "check-nabdh-v1-visibility.py Telegram-upstream" in workflow,
      "visibility gate not installed in final CI sequence")
if sys.argv[1:] == ["--self-test"]:
    print("PASS: V1 source visibility and deferred feature contract")
    raise SystemExit(0)
if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-v1-visibility.py --self-test | TELEGRAM_SOURCE")
root = Path(sys.argv[1])
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
page = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
hub = (ui / "NabdhGramSettingsActivity.java").read_text(encoding="utf-8")
check("NabdhIntelligenceTitle" in hub and
      "NabdhFeatureGates.publicAiEnabled(context)" in hub,
      "unaccepted NabdhAI category is visible in the release hub")
native_ai = (ui / "NabdhAiActivity.java").read_text(encoding="utf-8")
native_gates = (ui / "Components/NabdhFeatureGates.java").read_text(encoding="utf-8")
check(native_gates == flags, "generated feature gates differ from source")
for id in (203, 401):
    check(f"NabdhFeatureGates.visible({id})" in page
          and f"nabdhFeatureRow(context, content, {id});" in page,
          f"deferred V2 feature {id} must retain native activation ID")
check("NabdhFeatureGates.verifiedAiChat(context)" in page
      and "NabdhFeatureGates.verifiedAiChat(this)" in native_ai,
      "AI Chat placeholder must remain hidden before real inference")
check("NabdhAiCoreService.class" in page
      or "NabdhAiActivity.class" in page,
      "AI source and model setup must remain compiled for future releases")
print("PASS: V1 suppresses unaccepted NabdhAI in root and feature menus; engines preserved")
