#!/usr/bin/env python3
"""Export all four approved launchers and their adaptive layers as a reproducible ZIP.

Run after apply-nabdh-approved-icon-variants.py. Every actual mipmap resource
is copied from the generated Telegram source: no image redesign, no badges.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

from PIL import Image

SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
SOURCES = {"silver": "nabdh-icon-silver-circle.webp",
           "dark": "nabdh-icon-dark-circle.webp",
           "glass": "nabdh-icon-glass-circle.webp",
           "iphone": "nabdh-icon-iphone.webp"}


def export(root: Path, target: Path) -> None:
    res = root / "TMessagesProj/src/main/res"
    sources = Path(__file__).resolve().parents[1] / "branding/approved"
    payload = {}
    manifest = {"format": "NabdhGram Android launcher icons v1",
                "variants": {}, "densities": SIZES}
    for slug, filename in SOURCES.items():
        original = sources / filename
        if not original.is_file():
            raise ValueError("Missing approved artwork: " + filename)
        with Image.open(original) as image:
            if image.size != (192, 192) or image.mode != "RGBA":
                raise ValueError("Unexpected approved artwork: " + filename)
            pixels = image.copy()
        payload["approved/" + filename] = original.read_bytes()
        hashes = {}
        for density, pixels_wide in SIZES.items():
            filename_png = "nabdh_icon_" + slug + ".png"
            path = res / ("mipmap-" + density) / filename_png
            if not path.is_file():
                raise ValueError("Missing generated Android resource: " + str(path))
            raw = path.read_bytes()
            with Image.open(io.BytesIO(raw)) as icon:
                if icon.size != (pixels_wide, pixels_wide) or icon.mode != "RGBA":
                    raise ValueError("Incorrect density/color mode: " + str(path))
                expected = pixels.resize((pixels_wide, pixels_wide),
                                          Image.Resampling.LANCZOS)
                if icon.tobytes() != expected.tobytes():
                    raise ValueError("Resource artwork differs from owner image: " + str(path))
            location = "res/mipmap-" + density + "/" + filename_png
            payload[location] = raw
            hashes[location] = hashlib.sha256(raw).hexdigest()
        # Include the actual API 26+ files. Previously this export contained
        # legacy PNGs only, which could not reproduce what Samsung renders.
        adaptive = res / "mipmap-anydpi-v26" / ("nabdh_icon_" + slug + ".xml")
        foreground = res / "drawable-nodpi" / ("nabdh_icon_" + slug + "_foreground.png")
        for path in (adaptive, foreground):
            if not path.is_file():
                raise ValueError("Missing adaptive launcher resource: " + str(path))
            location = "res/" + path.relative_to(res).as_posix()
            payload[location] = path.read_bytes()
            hashes[location] = hashlib.sha256(payload[location]).hexdigest()
        manifest["variants"][slug] = hashes
    payload["manifest.json"] = (json.dumps(manifest, ensure_ascii=False,
                           indent=2, sort_keys=True) + "\n").encode("utf-8")
    payload["README.txt"] = (
        "NabdhGram approved icon package\\n"
        "silver: owner image 44; dark: 55; glass: 33; iPhone Glass: approved.\\n"
        "Copy the res/mipmap-* resource directories into an Android project.\\n"
        "The archive includes both legacy PNG and Android 26+ adaptive XML/artwork.\\n"
        "The source image is also provided under approved/.\\n"
        "All five density tiers and adaptive resources included.\\n"
    ).replace("\\n", "\n").encode("utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(payload):
            info = ZipInfo(path, (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, payload[path], compress_type=ZIP_DEFLATED,
                             compresslevel=9)
    with ZipFile(target) as archive:
        if archive.testzip():
            raise ValueError("Export archive checksum invalid")
        assert set(archive.namelist()) == set(payload)
    print("PASS: icon archive includes all 20 density assets, four adaptive layers and SHA-256 hashes")
    print("ZIP:", target)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: package-nabdh-android-icons.py TELEGRAM_SOURCE OUTPUT_ZIP")
    export(Path(sys.argv[1]), Path(sys.argv[2]))
