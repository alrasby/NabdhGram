#!/usr/bin/env python3
"""Fail-closed Google Play AAB upload-key and artifact verification.

An AAB is not an installable APK. Google Play re-signs generated APK splits
using Play App Signing; this check confirms the *upload* certificate used
by the owner's Release pipeline, not the eventual Google signing key.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile


def fingerprint(text):
    marker = re.search(r"SHA256:\\s*([A-Fa-f0-9:]{64,95})", text)
    if marker is None:
        raise ValueError("AAB upload certificate SHA256 missing")
    value = re.sub(r"[^A-Fa-f0-9]", "", marker.group(1)).upper()
    if len(value) != 64:
        raise ValueError("AAB upload certificate SHA256 invalid")
    return value


def check_archive(path):
    if not path.is_file() or path.stat().st_size < 500_000:
        raise ValueError("AAB missing or unexpectedly tiny")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        for required in ("BundleConfig.pb", "base/manifest/AndroidManifest.xml",
                         "base/dex/classes.dex"):
            if required not in names:
                raise ValueError("Missing mandatory Android bundle entry: " + required)
        if not any(n.startswith("base/lib/arm64-v8a/") for n in names):
            raise ValueError("Play bundle missing ARM64 shared libraries")
        if not any(n.startswith("base/lib/armeabi-v7a/") for n in names):
            raise ValueError("Play bundle missing 32-bit ARM shared libraries")
        if any("twemoji" in n.lower() or "nabdh_emoji" in n.lower() for n in names):
            raise ValueError("Removed third-party emoji package is present in the AAB")
        rejected = archive.testzip()
        if rejected is not None:
            raise ValueError("AAB ZIP CRC verification failed: " + rejected)
    return True


def run(*args):
    completed = subprocess.run(args, capture_output=True, text=True, timeout=90)
    if completed.returncode:
        raise ValueError("Signed AAB verification command failed: " + args[0])
    return completed.stdout + "\n" + completed.stderr


def main():
    if sys.argv[1:] == ["--self-test"]:
        assert fingerprint("SHA256: " + "AA:" * 31 + "AA") == "AA" * 32
        for text in ("no certificate", "SHA256: 1234"):
            try:
                fingerprint(text)
                raise AssertionError("Malformed certificate digest was accepted")
            except ValueError:
                pass
        print("PASS: Play AAB fingerprint parsing guards")
        return
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify-release-aab.py signed.aab | --self-test")
    path = Path(sys.argv[1])
    expected = re.sub(r"[^A-Fa-f0-9]", "",
                      os.environ.get("NABDH_RELEASE_CERT_SHA256", "")).upper()
    if len(expected) != 64:
        raise SystemExit("Owner upload certificate secret missing")
    try:
        check_archive(path)
        result = run("jarsigner", "-verify", "-verbose", str(path))
        if "jar verified" not in result.lower():
            raise ValueError("AAB JAR signature did not verify")
        actual = fingerprint(run("keytool", "-J-Duser.language=en",
                                 "-printcert", "-jarfile", str(path)))
        if actual != expected:
            raise ValueError("Play upload AAB is signed by the wrong certificate")
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
        raise SystemExit("FAIL-CLOSED Play AAB: " + str(error))
    print("PASS: owner-signed Google Play upload AAB, verified certificate, "
          "ARM32/ARM64 and no removed emoji artwork")


if __name__ == "__main__":
    main()
