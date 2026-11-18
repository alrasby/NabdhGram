#!/usr/bin/env python3
"""Mirror Telegram's native section order for NabdhGram's overlapping settings.

Telegram 13.2.2 native order is Chat, Privacy, Notifications, Data,
Folders, Devices, Power, Language. NabdhGram must NOT duplicate native
pages for categories it does not extend. The corresponding categories are
Chat/Appearance, Privacy, Data/Network, Language; Nabdh-only additions follow.

Preserves feature IDs, detail navigation, icons, Glass drawing and preferences.
Runs after Liquid Glass adds the seventh (Intelligence) entry.
"""
from pathlib import Path
import sys

CATEGORIES = {
    "Appearance": ("NabdhAppearanceTitle", "NabdhAppearanceExplanation"),
    "Privacy": ("NabdhPrivacyTitle", "NabdhPrivacyExplanation"),
    "Network": ("NabdhNetworkTitle", "NabdhNetworkExplanation"),
    "Language": ("NabdhLanguageTitle", "NabdhLanguageExplanation"),
    "Shield": ("NabdhShieldTitle", "NabdhShieldExplanation"),
    "Productivity": ("NabdhProductivityTitle", "NabdhProductivityExplanation"),
    "Intelligence": ("NabdhIntelligenceTitle", "NabdhIntelligenceDescription"),
}
ORDER = list(CATEGORIES)

def section(category):
    title, description = CATEGORIES[category]
    return (f"        section(context, content, R.string.{title}, "
            f"R.string.{description});")

def order_in(source):
    indices = {}
    for category in ORDER:
        statement = section(category)
        count = source.count(statement)
        if count != 1:
            raise ValueError(
                f"Settings navigation {category}: expected one real section, got {count}")
        indices[category] = source.index(statement)
    return sorted(ORDER, key=lambda key: indices[key])

def rewrite(source):
    slots = order_in(source)
    if slots == ORDER:
        return source
    for index, category in enumerate(slots):
        source = source.replace(section(category),
                                f"        // NABDH_NATIVE_ORDER_SLOT_{index}", 1)
    for index, category in enumerate(ORDER):
        source = source.replace(
            f"        // NABDH_NATIVE_ORDER_SLOT_{index}", section(category), 1)
    if order_in(source) != ORDER:
        raise ValueError("Native NabdhGram settings order check failed")
    return source

def self_test():
    original = (
        "before\n" +
        "\n".join(section(k) for k in (
            "Shield", "Privacy", "Productivity", "Language", "Network",
            "Appearance", "Intelligence")) +
        "\nafter\n"
    )
    expected = rewrite(original)
    assert order_in(expected) == ORDER
    assert rewrite(expected) == expected
    assert "before\n" in expected and "\nafter\n" in expected
    assert "NABDH_NATIVE_ORDER_SLOT" not in expected
    assert expected.count("section(context, content") == len(ORDER)
    try:
        rewrite(original.replace(section("Shield"), ""))
    except ValueError:
        pass
    else:
        raise AssertionError("Missing settings route should fail closed")
    print("PASS: Telegram-native mirrored NabdhGram settings order / 7 intact routes")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
    elif len(sys.argv) == 3 and sys.argv[1] == "--verify":
        source = (Path(sys.argv[2]) /
                  "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramSettingsActivity.java"
                  ).read_text(encoding="utf-8")
        if order_in(source) != ORDER:
            raise SystemExit("FAIL: NabdhGram Settings do not match native Telegram relative order")
        print("PASS: native Telegram order preserved in NabdhGram navigation")
    elif len(sys.argv) == 2:
        target = (Path(sys.argv[1]) /
                  "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramSettingsActivity.java")
        source = target.read_text(encoding="utf-8")
        target.write_text(rewrite(source), encoding="utf-8")
        print("PASS: NabdhGram settings mirror Telegram's main feature sequence")
    else:
        raise SystemExit(
            "Usage: apply-nabdh-settings-order.py [--self-test|--verify TELEGRAM_SOURCE|TELEGRAM_SOURCE]")
