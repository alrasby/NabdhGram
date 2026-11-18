#!/usr/bin/env python3
"""Reduce Google Play AAB native debug metadata while retaining symbol names.

Only pinned Telegram's Release buildTypes are edited; Debug, ABI coverage,
R8, dependencies, application ID and signing configuration remain unchanged.
"""
from pathlib import Path
import re
import sys
import tempfile

MODULES = ("TMessagesProj_App/build.gradle", "TMessagesProj/build.gradle")
RELEASE = re.compile(r"(?ms)^(?P<open> {8}release \{\n)(?P<body>.*?)(?P<close>^ {8}\})")
FROM = "ndk.debugSymbolLevel = 'FULL'"
TO = "ndk.debugSymbolLevel = 'SYMBOL_TABLE'"


def adjust(content, module):
    matches = list(RELEASE.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"{module}: expected exactly one release buildType")
    match = matches[0]
    body = match["body"]
    if body.count(FROM) != 1 or TO in body:
        raise ValueError(f"{module}: release native symbol policy changed")
    if not re.search(r"(?m)^ {12}" + re.escape(FROM) + r"\s*$", body):
        raise ValueError(f"{module}: symbol policy not a release-level declaration")
    if module.startswith("TMessagesProj_App/") and (
            "debuggable false" not in body or "minifyEnabled true" not in body):
        raise ValueError("Release safeguards unexpectedly changed")
    updated = content[:match.start("body")] + body.replace(FROM, TO, 1) + content[match.end("body"):]
    assert updated.count(FROM) == content.count(FROM) - 1
    assert updated.count(TO) == content.count(TO) + 1
    assert updated[:match.start("body")] == content[:match.start("body")]
    assert updated.endswith(content[match.end("body"):])
    return updated


def apply(root):
    if not (root / "gradle.properties").is_file():
        raise ValueError("Expected pinned Telegram checkout")
    changes = []
    for relative in MODULES:
        path = root / relative
        changes.append((path, adjust(path.read_text(encoding="utf-8"), relative)))
    for path, content in changes:
        path.write_text(content, encoding="utf-8")
    print("PASS: Release SYMBOL_TABLE applied to app/library; Debug FULL, R8 and ABIs untouched")


def self_test():
    body = """    buildTypes {
        debug {
            ndk.debugSymbolLevel = 'FULL'
        }
        standalone {
            ndk.debugSymbolLevel = 'FULL'
        }
        release {
            debuggable false
            minifyEnabled true
            ndk.debugSymbolLevel = 'FULL'
        }
    }
"""
    for module in MODULES:
        result = adjust(body, module)
        assert result.count(FROM) == 2 and result.count(TO) == 1
        assert "debug {\n            ndk.debugSymbolLevel = 'FULL'" in result
        assert "standalone {\n            ndk.debugSymbolLevel = 'FULL'" in result
        for modified in (
            body.replace("        release {", "        releaseBad {"),
            body.replace("            ndk.debugSymbolLevel = 'FULL'\n        }\n    }",
                         "            ndk.debugSymbolLevel = 'SYMBOL_TABLE'\n        }\n    }"),
        ):
            try:
                adjust(modified, module)
            except ValueError:
                pass
            else:
                raise AssertionError("Gradle upstream drift was accepted")
    with tempfile.TemporaryDirectory() as path:
        root = Path(path)
        (root / "gradle.properties").write_text("TEST=1\n", encoding="utf-8")
        for relative in MODULES:
            p = root / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        apply(root)
    print("PASS: release-only native symbol optimization regression tests")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 2:
        apply(Path(sys.argv[1]).resolve())
    else:
        raise SystemExit("Usage: configure-release-native-symbols.py --self-test | TELEGRAM_SOURCE")
