#!/usr/bin/env python3
"""Bundle immutable Twemoji 17.0.3 PNG artwork into the Android APK.

Only build machines contact GitHub. Production app never requests emoji images.
Pinned commit: https://github.com/jdecked/twemoji/tree/b6b55fef1e8636b540a6d016a4729ca8cdf2e60b
Graphics: CC BY 4.0. Code/library (not used here): MIT.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.request

COMMIT = "b6b55fef1e8636b540a6d016a4729ca8cdf2e60b"
VERSION = "17.0.3"
URL = f"https://codeload.github.com/jdecked/twemoji/tar.gz/{COMMIT}"
ASSET_PREFIX = "/assets/72x72/"
NAME = re.compile(r"^[0-9a-f]+(?:-[0-9a-f]+)*\.png$")
MAX_ARCHIVE = 200 * 1024 * 1024
MAX_PNG = 256 * 1024
MAX_ASSETS = 64 * 1024 * 1024
MIN_IMAGES = 3000
REQUIRED = {"1f600.png", "1f44d.png", "2764.png", "1f1f4-1f1f2.png"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def checked_bundle(source: Path) -> None:
    dest = source / "TMessagesProj/src/main/assets/nabdh_twemoji"
    artwork = dest / "72x72"
    done = dest / ".twemoji17-complete"
    if done.exists():
        count = sum(1 for _ in artwork.glob("*.png"))
        if count < MIN_IMAGES or not all((artwork / icon).exists() for icon in REQUIRED):
            raise RuntimeError("Twemoji asset cache is incomplete or invalid")
        print(f"PASS: reused Twemoji {VERSION} assets, {count} files", flush=True)
        return

    with tempfile.TemporaryDirectory(prefix="nabdh-twemoji17-") as tmp:
        archive = Path(tmp) / "twemoji17.tar.gz"
        request = urllib.request.Request(URL, headers={"User-Agent": "NabdhGram-Twemoji17-Bundler"})
        with urllib.request.urlopen(request, timeout=120) as incoming, archive.open("wb") as out:
            size = 0
            while True:
                chunk = incoming.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_ARCHIVE:
                    raise RuntimeError("Twemoji upstream archive exceeds size budget")
                out.write(chunk)

        staging = Path(tmp) / "assets"
        staging.mkdir()
        artwork_dir = staging / "72x72"
        artwork_dir.mkdir()
        hashes = []
        count = 0
        total = 0
        license_found = False
        with tarfile.open(archive, mode="r:gz") as tar:
            for member in tar:
                if not member.isfile() or member.issym() or member.islnk():
                    continue
                name = member.name
                if name.endswith("/LICENSE-GRAPHICS"):
                    if member.size > 100_000:
                        raise RuntimeError("Unexpected graphics license size")
                    source_file = tar.extractfile(member)
                    if source_file is None:
                        raise RuntimeError("Missing Twemoji license data")
                    (staging / "LICENSE-GRAPHICS").write_bytes(source_file.read())
                    license_found = True
                    continue
                if ASSET_PREFIX not in name:
                    continue
                filename = name.rsplit("/", 1)[-1]
                if not NAME.fullmatch(filename):
                    continue
                if member.size < 64 or member.size > MAX_PNG:
                    raise RuntimeError(f"Unexpected PNG dimensions or size: {filename}")
                total += member.size
                if total > MAX_ASSETS:
                    raise RuntimeError("Twemoji PNGs exceed the 64 MiB release size budget")
                file_obj = tar.extractfile(member)
                if file_obj is None:
                    raise RuntimeError(f"Missing asset data: {filename}")
                data = file_obj.read()
                if not data.startswith(PNG_SIGNATURE) or len(data) != member.size:
                    raise RuntimeError(f"Invalid PNG: {filename}")
                (artwork_dir / filename).write_bytes(data)
                hashes.append((filename, hashlib.sha256(data).hexdigest()))
                count += 1
        if not license_found or count < MIN_IMAGES or not REQUIRED.issubset({n for n, _ in hashes}):
            raise RuntimeError(f"Incomplete Twemoji {VERSION} PNG archive: count={count}")
        hashes.sort()
        (staging / "SHA256SUMS.txt").write_text(
            "".join(f"{digest}  72x72/{name}\n" for name, digest in hashes),
            encoding="utf-8",
        )
        (staging / "ABOUT.txt").write_text(
            f"Twemoji {VERSION} graphics: CC BY 4.0\n"
            "Copyright Twemoji contributors. Modifications: none to original PNGs.\n"
            f"Source commit: https://github.com/jdecked/twemoji/commit/{COMMIT}\n"
            "Graphics license: LICENSE-GRAPHICS\n", encoding="utf-8")
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(staging), str(dest))
        done.write_text(f"{COMMIT}\n{count}\n{total}\n", encoding="utf-8")
        print(f"PASS: bundled {count} Twemoji 17 PNGs ({total / 1024 / 1024:.1f} MiB), "
              "pinned upstream revision with attribution", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: bundle-twemoji17.py TELEGRAM_SOURCE")
    checked_bundle(Path(sys.argv[1]).resolve())
