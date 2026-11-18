#!/usr/bin/env python3
"""Provision private NabdhGram RELEASE signing and Firebase on an ephemeral CI runner.

NO upstream Telegram dummy keys, NO release-key fallbacks, NO secrets in source,
NO signed-production claim until apksigner cert and app checks pass.
"""
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

PACKAGE = "net.nabdhserv.nabdhgram"
SECRET_NAMES = (
    "NABDH_RELEASE_KEYSTORE_B64", "NABDH_RELEASE_STORE_PASSWORD",
    "NABDH_RELEASE_KEY_ALIAS", "NABDH_RELEASE_KEY_PASSWORD",
    "NABDH_RELEASE_CERT_SHA256", "NABDH_FIREBASE_CONFIG_B64",
)


def required(env):
    missing = [name for name in SECRET_NAMES if not env.get(name)]
    if missing:
        raise ValueError("Required private release configuration missing: " + ", ".join(missing))


def decode(value, purpose, max_bytes):
    if len(value) > max_bytes * 2:
        raise ValueError(purpose + " is too large")
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("Invalid base64 for " + purpose) from e
    if not raw or len(raw) > max_bytes:
        raise ValueError("Invalid size for " + purpose)
    return raw


def firebase_client(config):
    if not isinstance(config, dict):
        raise ValueError("Firebase config must be an object")
    info = config.get("project_info") or {}
    if not info.get("project_id") or not info.get("project_number"):
        raise ValueError("Firebase project info incomplete")
    clients = config.get("client") or []
    if not any(
        c.get("client_info", {}).get("android_client_info", {}).get("package_name") == PACKAGE
        and c.get("client_info", {}).get("mobilesdk_app_id")
        for c in clients if isinstance(c, dict)
    ):
        raise ValueError("Firebase config has no client for NabdhGram's exact package")
    return True


def rewrite_properties(source, env):
    for name, value in (
        ("RELEASE_STORE_PASSWORD", env["NABDH_RELEASE_STORE_PASSWORD"]),
        ("RELEASE_KEY_ALIAS", env["NABDH_RELEASE_KEY_ALIAS"]),
        ("RELEASE_KEY_PASSWORD", env["NABDH_RELEASE_KEY_PASSWORD"]),
    ):
        # Values are consumed through Java properties; line breaks and
        # property escape characters would create injections/ambiguous signing.
        if not value or len(value) > 256 or any(c in value for c in "\n\r\\"):
            raise ValueError("Unsupported character in " + name)
        m = re.findall(r"^" + re.escape(name) + r"=.*$", source, re.M)
        if len(m) != 1:
            raise ValueError("Upstream signing property anchor changed: " + name)
        source = re.sub(r"^" + re.escape(name) + r"=.*$", lambda _: name + "=" + value,
                        source, count=1, flags=re.M)
    return source


def cert_sha(text):
    match = re.search(r"certificate SHA-256 digest:\s*([0-9a-fA-F:]{64,95})", text)
    if not match:
        raise ValueError("Cannot read signing certificate digest")
    return re.sub("[^0-9a-fA-F]", "", match.group(1)).upper()


def self_test():
    env = {name: "demo" for name in SECRET_NAMES}
    assert required(env) is None
    try:
        required({"NABDH_RELEASE_KEYSTORE_B64": "test"})
        raise AssertionError("Expected missing-secrets rejection")
    except ValueError:
        pass
    props = ("RELEASE_STORE_PASSWORD=android\nRELEASE_KEY_ALIAS=androidkey\n"
             "RELEASE_KEY_PASSWORD=android\nAPP_PACKAGE=" + PACKAGE + "\n")
    changed = rewrite_properties(props, env)
    assert "RELEASE_STORE_PASSWORD=demo" in changed
    assert "RELEASE_KEY_ALIAS=demo" in changed
    assert "APP_PACKAGE=" + PACKAGE in changed
    assert cert_sha("Signer #1 certificate SHA-256 digest: " + "a" * 64) == "A" * 64
    assert firebase_client({"project_info": {"project_id":"p","project_number":"1"},
                            "client":[{"client_info":{"mobilesdk_app_id":"id",
                            "android_client_info":{"package_name":PACKAGE}}}]})
    try:
        firebase_client({"project_info": {"project_id":"p","project_number":"1"},
                         "client":[{"client_info":{"mobilesdk_app_id":"id",
                         "android_client_info":{"package_name":"org.telegram.messenger"}}}]})
        raise AssertionError("Expected mismatched-app rejection")
    except ValueError:
        pass
    print("PASS: release keys required, no dummy fallback, exact package and signing digest")


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    if len(sys.argv) != 2:
        raise SystemExit("Usage: configure-release-signing.py TELEGRAM_SOURCE | --self-test")
    env = os.environ
    try:
        required(env)
        root = Path(sys.argv[1])
        props = root / "gradle.properties"
        keystore = root / "TMessagesProj/config/release.keystore"
        config = root / "TMessagesProj_App/google-services.json"
        expected = re.sub("[^0-9A-Fa-f]", "", env["NABDH_RELEASE_CERT_SHA256"]).upper()
        if len(expected) != 64:
            raise ValueError("NABDH_RELEASE_CERT_SHA256 must be the pinned 64-char certificate SHA256")
        key = decode(env["NABDH_RELEASE_KEYSTORE_B64"], "release keystore", 2_000_000)
        conf = decode(env["NABDH_FIREBASE_CONFIG_B64"], "Firebase config", 250_000)
        firebase_client(json.loads(conf))
        previous = keystore.read_bytes() if keystore.exists() else b""
        if key == previous:
            raise ValueError("Refusing upstream/demo Telegram release keystore")
        source = props.read_text(encoding="utf-8")
        if "APP_PACKAGE=" + PACKAGE not in source:
            raise ValueError("Unexpected release package identity")
        changed = rewrite_properties(source, env)
        # Validate supplied keystore AND the expected cert BEFORE mutating
        # build inputs, never print passwords, aliases, or certificate secrets.
        import tempfile
        with tempfile.TemporaryDirectory(prefix="nabdh-release-") as tmp:
            tmp_key = Path(tmp) / "release.keystore"
            tmp_key.write_bytes(key)
            tmp_key.chmod(0o600)
            cp = subprocess.run(
                ["keytool", "-list", "-v", "-keystore", str(tmp_key),
                 "-storepass", env["NABDH_RELEASE_STORE_PASSWORD"],
                 "-alias", env["NABDH_RELEASE_KEY_ALIAS"]],
                capture_output=True, text=True, timeout=30,
            )
            if cp.returncode:
                raise ValueError("Release keystore/alias could not be verified")
            marker = re.search(r"SHA256:\s*([A-Fa-f0-9:]{95})", cp.stdout)
            if not marker or re.sub(":", "", marker.group(1)).upper() != expected:
                raise ValueError("Release signer certificate SHA256 does not match pinned expected certificate")
        keystore.parent.mkdir(parents=True, exist_ok=True)
        keystore.write_bytes(key)
        keystore.chmod(0o600)
        config.write_bytes(conf)
        config.chmod(0o600)
        props.write_text(changed, encoding="utf-8")
        props.chmod(0o600)
        print("PASS: private NabdhGram signing identity and Firebase package configured (redacted)")
    except (ValueError, OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        raise SystemExit("FAIL-CLOSED release configuration: " + str(e))


if __name__ == "__main__":
    main()
