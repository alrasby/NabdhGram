#!/usr/bin/env python3
"""Fail closed if a claimed NabdhGram Release APK is debug-signed or mismatched."""
import os
import pathlib
import re
import subprocess
import sys

PACKAGE = "net.nabdhserv.nabdhgram"


def read_cert(stdout):
    m = re.search(r"Signer #1 certificate SHA-256 digest:\s*([A-Fa-f0-9:]{64,95})", stdout)
    if not m:
        raise ValueError("Release signing fingerprint unavailable")
    return re.sub("[^A-Fa-f0-9]", "", m.group(1)).upper()


def check_badging(text):
    if "package: name='" + PACKAGE + "'" not in text:
        raise ValueError("Wrong package ID in release APK")
    if "application-debuggable" in text:
        raise ValueError("Release APK is debuggable")
    if "application-label:'NabdhGram'" not in text:
        raise ValueError("Release branding mismatch")


def main():
    if sys.argv[1:] == ["--self-test"]:
        check_badging("package: name='net.nabdhserv.nabdhgram' versionCode='73039'\napplication-label:'NabdhGram'")
        assert read_cert("Signer #1 certificate SHA-256 digest: " + "b" * 64) == "B" * 64
        for bad in ("package: name='org.telegram.messenger'\napplication-label:'NabdhGram'",
                    "package: name='net.nabdhserv.nabdhgram'\napplication-debuggable\napplication-label:'NabdhGram'"):
            try:
                check_badging(bad)
                raise AssertionError("Bad release accepted")
            except ValueError:
                pass
        print("PASS: release package, debuggable flag and pinned signature checks")
        return
    if len(sys.argv) != 4:
        raise SystemExit("Usage: verify-release-apk.py APK badging.txt manifest.txt | --self-test")
    apk, badging, manifest = map(pathlib.Path, sys.argv[1:])
    expected = re.sub("[^A-Fa-f0-9]", "", os.environ.get("NABDH_RELEASE_CERT_SHA256", "")).upper()
    if len(expected) != 64:
        raise SystemExit("Release cert SHA256 secret required")
    check_badging(badging.read_text())
    xml = manifest.read_text()
    # Android aapt emits binary-XML attribute values; explicit true is fatal.
    if re.search(r"android:debuggable\b[^\\n]*?(0xffffffff|true)", xml, re.I):
        raise SystemExit("FAIL: manifest advertises debuggable")
    tool = pathlib.Path(os.environ["ANDROID_HOME"]) / "build-tools/36.0.0/apksigner"
    v = subprocess.run([str(tool), "verify", "--verbose", "--print-certs", str(apk)],
                       capture_output=True, text=True, timeout=45)
    if v.returncode:
        raise SystemExit("Release APK signature verification failed")
    if "Verified using v2 scheme (APK Signature Scheme v2): true" not in v.stdout:
        raise SystemExit("Release v2 signature missing")
    actual = read_cert(v.stdout)
    if actual != expected:
        raise SystemExit("Release certificate does not match the owned pinned signing key")
    print("PASS: non-debuggable NabdhGram Release APK uses the pinned owner certificate")


if __name__ == "__main__":
    main()
