#!/usr/bin/env python3
"""Owner-only setup for NabdhGram Release signing. NEVER prints any secret."""
import argparse, base64, getpass, json, os, re, shutil, subprocess
from pathlib import Path

REPO = "alrasby/NabdhGram"
PACKAGE = "net.nabdhserv.nabdhgram"
ALIAS = "nabdhgram-release"

def die(msg):
    raise SystemExit("ERROR: " + msg)

def strong(value):
    if not 16 <= len(value) <= 256 or any(c in value for c in "\r\n\\"):
        die("Password must have 16-256 characters, no backslash/newline.")
    return value

def cert_from_output(text):
    m = re.search(r"SHA256:\s*((?:[0-9a-fA-F]{2}:){31}[0-9a-fA-F]{2})", text)
    if not m:
        die("Cannot verify keytool certificate SHA-256.")
    return m.group(1).replace(":", "").upper()

def firebase(raw):
    try:
        x = json.loads(raw)
        ok = x["project_info"]["project_id"] and x["project_info"]["project_number"]
        ok = ok and any(c["client_info"]["android_client_info"]["package_name"] == PACKAGE and
                            c["client_info"]["mobilesdk_app_id"] for c in x["client"])
        if not ok:
            raise ValueError("Firebase application does not match " + PACKAGE)
    except (KeyError, ValueError, TypeError, IndexError) as e:
        die("Incorrect google-services.json: " + str(e))

def keytool(args, store_password):
    env = dict(os.environ, NABDH_LOCAL_STORE_PASSWORD=store_password)
    x = subprocess.run(["keytool", "-J-Duser.language=en", *args,
                        "-storepass:env", "NABDH_LOCAL_STORE_PASSWORD"],
                       env=env, text=True, capture_output=True)
    if x.returncode:
        die("keytool failed: verify JDK, alias, path, and password.")
    return x.stdout + x.stderr

def upload_secret(name, value):
    # stdin: no CLI argument secrets, temp dotenv, console print, or Git commit.
    r = subprocess.run(["gh", "secret", "set", name, "-R", REPO, "--app", "actions"],
                       input=value.encode(), stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    if r.returncode:
        die("GitHub secret upload failed for " + name + ". Check gh auth.")
    print("Set:", name)

def main():
    ap = argparse.ArgumentParser(description="Owner's private NabdhGram Release setup")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--create", help="New owner .jks path OUTSIDE repository")
    group.add_argument("--existing", help="Existing owner release .jks; NEVER rotate")
    ap.add_argument("--firebase-json", help="Downloaded exact-app google-services.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    p = ap.parse_args()
    if p.self_test:
        assert cert_from_output("SHA256: " + ":".join(["ab"] * 32)) == "AB" * 32
        firebase(json.dumps({"project_info":{"project_id":"x","project_number":"1"},
            "client":[{"client_info":{"android_client_info":{"package_name":PACKAGE},
                                       "mobilesdk_app_id":"x"}}]}))
        # Prove the installed JDK accepts :env password handling and the
        # fingerprint parser against a disposable 1-off test key (not Release).
        import tempfile
        if not shutil.which("keytool"):
            die("JDK keytool missing for self-test")
        with tempfile.TemporaryDirectory(prefix="nabdh-keytool-test-") as temp:
            test_path = Path(temp) / "temporary-test-only.jks"
            test_pass = "NabdhTestOnly!12345"
            env = dict(os.environ, NABDH_LOCAL_STORE_PASSWORD=test_pass)
            cmd = ["keytool", "-J-Duser.language=en", "-genkeypair", "-noprompt",
                   "-keystore", str(test_path), "-storetype", "PKCS12",
                   "-alias", "test-only", "-keyalg", "RSA", "-keysize", "2048",
                   "-validity", "2", "-dname", "CN=NabdhSelfTest",
                   "-keypass:env", "NABDH_LOCAL_STORE_PASSWORD",
                   "-storepass:env", "NABDH_LOCAL_STORE_PASSWORD"]
            t = subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            if t.returncode:
                die("JDK could not create ephemeral test key")
            report = keytool(["-list", "-v", "-keystore", str(test_path),
                              "-alias", "test-only"], test_pass)
            assert len(cert_from_output(report)) == 64
        print("PASS: disposable keytool key generation, fingerprint and Firebase package guards")
        return
    if not (p.create or p.existing):
        ap.error("Choose --create or --existing")
    if not shutil.which("keytool"):
        die("Install JDK 17+ and add keytool to PATH.")
    if not p.dry_run:
        if not shutil.which("gh"):
            die("Install GitHub CLI and run: gh auth login")
        auth = subprocess.run(["gh", "auth", "status"], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        if auth.returncode:
            die("Run gh auth login first.")

    path = Path(p.create or p.existing).expanduser().resolve()
    if p.create:
        if path.exists():
            die("Refusing to overwrite existing keystore.")
        if any((q / ".git").exists() for q in (path.parent, *path.parents)):
            die("Choose a private path OUTSIDE the Git repository.")
        path.parent.mkdir(parents=True, exist_ok=True)
        storepass = strong(getpass.getpass("New release password (min 16 chars): "))
        if storepass != getpass.getpass("Repeat password: "):
            die("Passwords do not match; nothing created.")
        keypass, alias = storepass, ALIAS
        env = dict(os.environ, NABDH_LOCAL_STORE_PASSWORD=storepass)
        r = subprocess.run([
            "keytool", "-J-Duser.language=en", "-genkeypair", "-noprompt",
            "-keystore", str(path), "-storetype", "PKCS12",
            "-alias", alias, "-keyalg", "RSA", "-keysize", "4096",
            "-validity", "10000",
            "-dname", "CN=NabdhGram, OU=Android, O=NabdhServ, C=OM",
            "-keypass:env", "NABDH_LOCAL_STORE_PASSWORD",
            "-storepass:env", "NABDH_LOCAL_STORE_PASSWORD"
        ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode:
            die("Cannot generate private signing keystore.")
        if os.name != "nt":
            path.chmod(0o600)
    else:
        if not path.is_file():
            die("Existing keystore not found.")
        alias = input("Existing private key alias: ").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", alias):
            die("Invalid alias.")
        storepass = strong(getpass.getpass("Store password: "))
        keypass = strong(getpass.getpass("Key password (Enter = same): ") or storepass)
    cert = cert_from_output(keytool(["-list", "-v", "-keystore", str(path),
                                     "-alias", alias], storepass))
    print("Public signing certificate SHA-256:", cert)
    print("Keep this .jks and password in a secure OFFLINE backup; do not commit.")
    values = {
        "NABDH_RELEASE_KEYSTORE_B64": base64.b64encode(path.read_bytes()).decode(),
        "NABDH_RELEASE_STORE_PASSWORD": storepass,
        "NABDH_RELEASE_KEY_ALIAS": alias,
        "NABDH_RELEASE_KEY_PASSWORD": keypass,
        "NABDH_RELEASE_CERT_SHA256": cert,
    }
    if p.firebase_json:
        raw = Path(p.firebase_json).expanduser().read_bytes()
        firebase(raw.decode("utf-8"))
        values["NABDH_FIREBASE_CONFIG_B64"] = base64.b64encode(raw).decode()
    if p.dry_run:
        print("Dry run completed; no GitHub values changed.")
    else:
        for name, value in values.items():
            upload_secret(name, value)
    if not p.firebase_json:
        print("PENDING: Firebase google-services.json for " + PACKAGE)
    print("Existing NABDHGRAM_API_ID/HASH unchanged. No private data printed.")

if __name__ == "__main__":
    main()
