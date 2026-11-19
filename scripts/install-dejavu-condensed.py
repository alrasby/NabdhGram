#!/usr/bin/env python3
"""Install DejaVu Sans Condensed from the official 2.37 release.

The official bundle uses the permissive Bitstream Vera / DejaVu font license,
not SIL OFL. Retain the upstream LICENSE notice with redistributed fonts.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile, BadZipFile
from io import BytesIO
from hashlib import sha256
import sys

VERSION = "2.37"
URL = ("https://downloads.sourceforge.net/project/dejavu/dejavu/"
       f"{VERSION}/dejavu-fonts-ttf-{VERSION}.zip")
SHA256 = "7576310b219e04159d35ff61dd4a4ec4cdba4f35c00e002a136f00e96a908b0a"
FONTS = {
    "DejaVuSansCondensed.ttf": "DejaVuSansCondensed.ttf",
    "DejaVuSansCondensed-Bold.ttf": "DejaVuSansCondensed-Bold.ttf",
}


def validate(archive_bytes):
    digest = sha256(archive_bytes).hexdigest()
    if digest != SHA256:
        raise ValueError(f"DejaVu official release hash mismatch: {digest}")
    with ZipFile(BytesIO(archive_bytes)) as archive:
        names = archive.namelist()
        files = {}
        for input_name, output_name in FONTS.items():
            matches = [n for n in names if n.endswith("/ttf/" + input_name)]
            if len(matches) != 1:
                raise ValueError("Required DejaVu font not unique: " + input_name)
            data = archive.read(matches[0])
            if len(data) < 10000 or data[:4] not in (b"\x00\x01\x00\x00", b"OTTO"):
                raise ValueError("Invalid DejaVu TTF: " + input_name)
            files[output_name] = data
        licenses = [n for n in names if n.endswith("/LICENSE")]
        if len(licenses) != 1:
            raise ValueError("Official DejaVu license missing")
        notice = archive.read(licenses[0])
        if b"Bitstream Vera" not in notice or b"Permission is hereby granted" not in notice:
            raise ValueError("Unexpected DejaVu redistribution license")
        files["DejaVu-LICENSE.txt"] = notice
    return files


def self_test():
    assert set(FONTS) == {
        "DejaVuSansCondensed.ttf", "DejaVuSansCondensed-Bold.ttf"
    }
    try:
        validate(b"Not a signed official DejaVu font archive")
    except ValueError as ex:
        assert "hash mismatch" in str(ex)
    else:
        raise AssertionError("Rejected corrupted font archive")
    print("PASS: pinned official archive hash, full-font and license validation")


def main(output):
    target = Path(output) / "TMessagesProj/src/main/assets/fonts"
    target.mkdir(parents=True, exist_ok=True)
    request = Request(URL, headers={"User-Agent": "NabdhGram-FontVerifier/1.0"})
    with urlopen(request, timeout=90) as response:
        if response.status != 200:
            raise ValueError("Official font download failed")
        blob = response.read()
    for filename, content in validate(blob).items():
        dest = target / filename
        if dest.exists():
            raise ValueError("Refusing to overwrite existing font asset: " + filename)
        dest.write_bytes(content)
    print("PASS: pinned DejaVu Sans Condensed Regular/Bold and original license installed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        raise SystemExit("Usage: install-dejavu-condensed.py --self-test | TELEGRAM_SOURCE")
