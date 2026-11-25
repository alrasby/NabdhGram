#!/usr/bin/env python3
"""Read-only APK footprint audit. ZIP payload is not installed app/data size."""
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile
import sys

MIB = 1024 * 1024

def category(name):
    if name.startswith("lib/"): return "Native libraries"
    if name.startswith("classes") and name.endswith(".dex"): return "DEX code"
    if name.startswith("assets/fonts/") or name.lower().endswith((".ttf", ".otf", ".woff2")): return "Fonts"
    if name.lower().endswith(".attheme"): return "Themes"
    if name.lower().endswith((".tflite", ".onnx", ".task", ".lite")): return "Model files"
    if name.startswith("assets/"): return "Other assets"
    if name.startswith("res/") or name == "resources.arsc": return "Android resources"
    return "Other metadata"

def report(path):
    totals = defaultdict(lambda: [0, 0])
    with ZipFile(path) as archive:
        entries = [x for x in archive.infolist() if not x.is_dir()]
        for x in entries:
            pair = totals[category(x.filename)]
            pair[0] += x.compress_size
            pair[1] += x.file_size
        print("### APK footprint audit")
        print(f"\nAPK file: {Path(path).stat().st_size / MIB:.2f} MiB\n")
        print("| Component | ZIP MiB | Raw MiB |")
        print("|---|---:|---:|")
        for name, (packed, raw) in sorted(totals.items(), key=lambda x: -x[1][1]):
            print(f"| {name} | {packed/MIB:.2f} | {raw/MIB:.2f} |")
        print("\nLargest entries (uncompressed):")
        for x in sorted(entries, key=lambda x: -x.file_size)[:25]:
            print(f"- {x.file_size/MIB:.2f} MiB / {x.compress_size/MIB:.2f} MiB ZIP: {x.filename}")
        print("\nRaw ZIP totals do not measure ART output, extracted libraries, app databases or downloaded user files.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: report-apk-size.py APP.apk")
    report(sys.argv[1])
