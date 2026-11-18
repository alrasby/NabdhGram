#!/usr/bin/env python3
"""Inspect compressed AAB payload categories without changing the bundle."""
from collections import defaultdict
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile

MIB = 1024 * 1024


def classify(name):
    if name.startswith("BUNDLE-METADATA/com.android.tools.build.debugsymbols/"):
        return "Native debug symbols"
    if name.startswith("BUNDLE-METADATA/com.android.tools.build.obfuscation/"):
        return "R8 mapping (retain)"
    if name.startswith("base/lib/"):
        return "Native libraries (retain)"
    if name.startswith("base/dex/"):
        return "DEX bytecode"
    return "Other resources and metadata"


def report(aab):
    result = defaultdict(int)
    top_debug = []
    with ZipFile(aab) as archive:
        for item in archive.infolist():
            bucket = classify(item.filename)
            result[bucket] += item.compress_size
            if bucket == "Native debug symbols":
                top_debug.append((item.compress_size, item.filename))
    total = Path(aab).stat().st_size
    if not result["Native libraries (retain)"] or not result["DEX bytecode"]:
        raise ValueError("AAB missing app code or native libraries")
    lines = [
        "### Signed Play AAB size audit",
        f"AAB file size: **{total / MIB:.2f} MiB**",
        "",
        "| Compressed component | MiB | Share |",
        "|---|---:|---:|",
    ]
    for label, size in sorted(result.items(), key=lambda x: -x[1]):
        lines.append(f"| {label} | {size / MIB:.2f} | {size / total:.1%} |")
    lines += ["", "Largest native debug-symbol entries:"]
    for size, name in sorted(top_debug, reverse=True)[:8]:
        lines.append(f"- {size / MIB:.2f} MiB — `{name}`")
    lines += [
        "",
        "Native-symbol metadata is upload/debugging data, not end-user download size.",
        "Verify device-specific delivered APK size using bundletool or Play Console.",
    ]
    return "\n".join(lines) + "\n"


def self_test():
    assert classify(
        "BUNDLE-METADATA/com.android.tools.build.debugsymbols/arm64-v8a/a.dbg"
    ) == "Native debug symbols"
    assert classify(
        "BUNDLE-METADATA/com.android.tools.build.obfuscation/proguard.map"
    ) == "R8 mapping (retain)"
    with tempfile.TemporaryDirectory() as directory:
        p = Path(directory) / "test.aab"
        with ZipFile(p, "w") as archive:
            archive.writestr("base/lib/arm64-v8a/libabc.so", b"hello")
            archive.writestr("base/dex/classes.dex", b"dexdata")
            archive.writestr(
                "BUNDLE-METADATA/com.android.tools.build.debugsymbols/arm64-v8a/libabc.so.dbg",
                b"symbols",
            )
        assert "Native debug symbols" in report(p)
        assert "Native libraries (retain)" in report(p)
    print("PASS: compressed AAB size report categorization regression tests")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 2:
        print(report(sys.argv[1]), end="")
    else:
        raise SystemExit("Usage: report-play-aab-size.py --self-test | APP.aab")
