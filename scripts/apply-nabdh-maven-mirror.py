#!/usr/bin/env python3
"""Route pinned Telegram's Maven Central downloads through Google's hosted mirror.

Release CI only: fixes Maven Central HTTP 429 from shared GitHub runner egress.
Does not change dependency coordinates, versions, signing, or APK contents.
"""
from pathlib import Path
import sys
import tempfile

MIRROR = "https://maven-central.storage-download.googleapis.com/maven2/"
OLD = "mavenCentral()"
NEW = "maven { url '" + MIRROR + "' }"
REQUIRED = (
    "settings.gradle",
    "build.gradle",
    "TMessagesProj/build.gradle",
    "TMessagesProj_App/build.gradle",
)


def apply(root: Path) -> int:
    if not (root / "gradle.properties").is_file():
        raise RuntimeError("Not a pinned Telegram Gradle checkout")
    # Verify the known root repository declarations before modifying anything.
    for relative in REQUIRED:
        file = root / relative
        if not file.is_file() or file.read_text(encoding="utf-8").count(OLD) != 1:
            raise RuntimeError("Pinned Maven Central repository anchor changed: " + relative)

    edits = []
    # Also covers any included native media or auxiliary Groovy build modules.
    # Never rewrite Kotlin DSL (.gradle.kts), dependencies or package versions.
    for file in sorted(root.rglob("*.gradle")):
        if ".git" in file.parts or ".gradle" in file.parts:
            continue
        before = file.read_text(encoding="utf-8")
        if OLD not in before:
            continue
        after = before.replace(OLD, NEW)
        edits.append((file, after))

    if len(edits) < len(REQUIRED):
        raise RuntimeError("Expected Gradle repositories missing")
    for file, updated in edits:
        file.write_text(updated, encoding="utf-8")
    for relative in REQUIRED:
        data = (root / relative).read_text(encoding="utf-8")
        if OLD in data or NEW not in data:
            raise RuntimeError("Failed to apply Google Maven mirror: " + relative)
    print("PASS: Google-hosted Maven Central mirror configured in "
          + str(len(edits)) + " Groovy Gradle files; dependencies unchanged")
    return len(edits)


def self_test() -> None:
    with tempfile.TemporaryDirectory() as path:
        root = Path(path)
        (root / "gradle.properties").write_text("APP_PACKAGE=example\n", encoding="utf-8")
        for rel in (*REQUIRED, "TMessagesProj_AppHuawei/build.gradle"):
            file = root / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("repositories {\n    " + OLD + "\n    google()\n}\n",
                            encoding="utf-8")
        assert apply(root) == len(REQUIRED) + 1
        for rel in REQUIRED:
            contents = (root / rel).read_text(encoding="utf-8")
            assert NEW in contents and OLD not in contents and "google()" in contents
        # Fail closed if the pinned Telegram repository declarations drift.
        (root / "settings.gradle").write_text("repositories { google() }\n",
                                               encoding="utf-8")
        try:
            apply(root)
        except RuntimeError as exc:
            assert "anchor changed" in str(exc)
        else:
            raise AssertionError("Missing upstream anchor was not rejected")
    print("PASS: Maven mirror transformation and pinned-anchor failure self-test")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 2:
        apply(Path(sys.argv[1]).resolve())
    else:
        raise SystemExit("Usage: apply-nabdh-maven-mirror.py --self-test | TELEGRAM_SOURCE")
