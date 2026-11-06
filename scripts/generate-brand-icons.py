#!/usr/bin/env python3
"""Generate NabdhGram Android launcher icon sizes from the approved user artwork.

Usage:
  python3 -m pip install Pillow
  python3 scripts/generate-brand-icons.py /path/to/approved-icon.png output/brand-icons
No AI generation, repainting, color changes or alterations to composition.
"""
from pathlib import Path
import sys
from PIL import Image

DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: generate-brand-icons.py INPUT_IMAGE OUTPUT_DIRECTORY")
    source, destination = Path(sys.argv[1]), Path(sys.argv[2])
    with Image.open(source) as raw:
        image = raw.convert("RGBA")
        if image.width != image.height:
            raise SystemExit("The approved source must be square")
        destination.mkdir(parents=True, exist_ok=True)
        image.save(destination / "nabdhgram-master.png")
        image.resize((512, 512), Image.Resampling.LANCZOS).save(destination / "play-store-512.png")
        for density, pixels in DENSITIES.items():
            folder = destination / "res" / ("mipmap-" + density)
            folder.mkdir(parents=True, exist_ok=True)
            scaled = image.resize((pixels, pixels), Image.Resampling.LANCZOS)
            scaled.save(folder / "ic_launcher.png")
            scaled.save(folder / "ic_launcher_round.png")
    print("Generated icon assets in", destination)

if __name__ == "__main__":
    main()
