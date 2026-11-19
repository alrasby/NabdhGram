#!/usr/bin/env python3
"""Offline validation of the actual bundled Noto Latin/Arabic font cmap tables.

No external Python packages; no message content is sent anywhere. This checks
font-file glyph availability and does NOT claim emulator/device rendering QA.
"""
from pathlib import Path
import struct
import sys

LATIN_SAMPLE = "Hello NabdhGram"
GREEK_SAMPLE = "Ελληνικά"
CYRILLIC_SAMPLE = "Привет"
ARABIC_SAMPLE = "مرحبا بالعالم"

def u16(buf, off):
    return struct.unpack_from(">H", buf, off)[0]

def u32(buf, off):
    return struct.unpack_from(">I", buf, off)[0]

def table(data, tag):
    if data[:4] not in (b"\0\1\0\0", b"OTTO"):
        raise ValueError("Invalid font sfnt signature")
    count = u16(data, 4)
    for i in range(count):
        pos = 12 + i * 16
        if data[pos:pos + 4] == tag:
            start = u32(data, pos + 8)
            length = u32(data, pos + 12)
            if length < 16 or start + length > len(data):
                raise ValueError("Invalid font table bounds")
            return data[start:start + length]
    raise ValueError("Missing font cmap table")

def glyphs(data):
    cmap = table(data, b"cmap")
    if u16(cmap, 0) != 0:
        raise ValueError("Unexpected cmap version")
    subtables = []
    for i in range(u16(cmap, 2)):
        rec = 4 + i * 8
        platform, encoding = u16(cmap, rec), u16(cmap, rec + 2)
        offset = u32(cmap, rec + 4)
        if platform == 0 or platform == 3 and encoding in (1, 10):
            fmt = u16(cmap, offset)
            if fmt in (4, 12):
                subtables.append((fmt, offset))
    if not subtables:
        raise ValueError("No Unicode cmap table")
    def has(cp):
        for fmt, off in subtables:
            if fmt == 12:
                for i in range(u32(cmap, off + 12)):
                    pos = off + 16 + i * 12
                    start, end = u32(cmap, pos), u32(cmap, pos + 4)
                    if start <= cp <= end:
                        if u32(cmap, pos + 8) + cp - start:
                            return True
            elif cp <= 0xffff:
                seg = u16(cmap, off + 6) // 2
                for i in range(seg):
                    end = u16(cmap, off + 14 + i * 2)
                    start = u16(cmap, off + 16 + seg * 2 + i * 2)
                    if start <= cp <= end:
                        delta = u16(cmap, off + 16 + seg * 4 + i * 2)
                        ro_pos = off + 16 + seg * 6 + i * 2
                        ro = u16(cmap, ro_pos)
                        if ro == 0:
                            if ((cp + delta) & 0xffff):
                                return True
                        else:
                            glyph = u16(cmap, ro_pos + ro + (cp - start) * 2)
                            if glyph and ((glyph + delta) & 0xffff):
                                return True
        return False
    return has

def check(directory):
    directory = Path(directory)
    latin = directory / "NotoSans.ttf"
    arabic = directory / "NotoSansArabic.ttf"
    for path in (latin, arabic, directory / "NotoSans-OFL.txt",
                 directory / "NotoSansArabic-OFL.txt"):
        if not path.is_file() or path.stat().st_size < 200:
            raise ValueError("Missing bundled Noto font/license: " + path.name)
    can_latin = glyphs(latin.read_bytes())
    can_arabic = glyphs(arabic.read_bytes())
    for title, sample, test in (
        ("Latin", LATIN_SAMPLE, can_latin),
        ("Greek", GREEK_SAMPLE, can_latin),
        ("Cyrillic", CYRILLIC_SAMPLE, can_latin),
        ("Arabic", ARABIC_SAMPLE, can_arabic),
    ):
        missing = sorted({ord(ch) for ch in sample if not ch.isspace() and not test(ord(ch))})
        if missing:
            raise ValueError(f"{title} font missing sample codepoints: {missing}")
        print("PASS:", title, "glyph sample present in the intended font")
    print("PASS: Noto Sans Latin / Noto Sans Arabic OFL assets and mixed-script cmap")

def self_test():
    try:
        table(b"not-a-ttf", b"cmap")
    except ValueError:
        pass
    else:
        raise AssertionError("Corrupt font unexpectedly accepted")
    for sample in (LATIN_SAMPLE, GREEK_SAMPLE, CYRILLIC_SAMPLE, ARABIC_SAMPLE):
        assert sample and len(sample) > 5
    print("PASS: Unicode sample and corrupt font self-tests")

if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    elif len(sys.argv) == 2:
        check(sys.argv[1])
    else:
        raise SystemExit("Usage: check-nabdh-noto-fonts.py --self-test | ASSET_FONT_DIRECTORY")
