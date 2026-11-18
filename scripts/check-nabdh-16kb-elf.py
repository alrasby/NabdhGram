#!/usr/bin/env python3
"""Check actual packaged ARM64/x86-64 ELF PT_LOAD alignments for Play 16KB devices.

NDK r27 and native prebuilt libraries may silently retain 4KB segment alignment.
Fail in owner-signed Release mode; report but do not block Debug experiment.
"""
import struct
import sys
from pathlib import Path
from zipfile import ZipFile

REQUIRED = 16384


def load_alignment(blob):
    if blob[:4] != b"\x7fELF":
        raise ValueError("Not an ELF shared library")
    kind, order = blob[4], blob[5]
    if kind not in (1, 2) or order not in (1, 2):
        raise ValueError("Unsupported ELF encoding")
    endian = "<" if order == 1 else ">"
    if kind == 2:
        offset = struct.unpack_from(endian + "Q", blob, 32)[0]
        size, count = struct.unpack_from(endian + "HH", blob, 54)
        alignment_offset, alignment_size, min_size = 48, 8, 56
    else:
        offset = struct.unpack_from(endian + "I", blob, 28)[0]
        size, count = struct.unpack_from(endian + "HH", blob, 42)
        alignment_offset, alignment_size, min_size = 28, 4, 32
    if count <= 0 or count > 1000 or size < min_size or offset + size * count > len(blob):
        raise ValueError("Invalid ELF program header table")
    result = []
    for index in range(count):
        header = offset + index * size
        if struct.unpack_from(endian + "I", blob, header)[0] == 1:  # PT_LOAD
            if alignment_size == 8:
                align = struct.unpack_from(endian + "Q", blob,
                                           header + alignment_offset)[0]
            else:
                align = struct.unpack_from(endian + "I", blob,
                                           header + alignment_offset)[0]
            result.append(align)
    if not result:
        raise ValueError("ELF has no loadable segments")
    return min(result)


def check(archive):
    bad = []
    count = 0
    with ZipFile(archive) as z:
        names = [n for n in z.namelist()
                 if n.endswith(".so") and (n.startswith("lib/") or n.startswith("base/lib/"))
                 and ("/arm64-v8a/" in n or "/x86_64/" in n)]
        for name in names:
            try:
                alignment = load_alignment(z.read(name))
                if alignment < REQUIRED:
                    bad.append((name, alignment))
            except (ValueError, IndexError, struct.error) as error:
                bad.append((name, str(error)))
            count += 1
    if not count:
        raise ValueError("No 64-bit native libraries found")
    return count, bad


def main():
    if sys.argv[1:] == ["--self-test"]:
        blank = bytearray(128)
        blank[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<Q", blank, 32, 64)
        struct.pack_into("<HH", blank, 54, 56, 1)
        struct.pack_into("<I", blank, 64, 1)
        struct.pack_into("<Q", blank, 64 + 48, 0x4000)
        assert load_alignment(blank) == 16384
        struct.pack_into("<Q", blank, 64 + 48, 0x1000)
        assert load_alignment(blank) == 4096
        print("PASS: synthetic ELF 16KB/4KB alignment validation")
        return
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != "--enforce"):
        raise SystemExit("Usage: check-nabdh-16kb-elf.py APK_OR_AAB [--enforce]")
    count, bad = check(Path(sys.argv[1]))
    if bad:
        for name, align in bad[:25]:
            print(f"16KB alignment issue: {name}: {align}", flush=True)
        print(f"WARNING: {len(bad)}/{count} 64-bit libraries do not advertise 16KB alignment")
        if len(sys.argv) == 3:
            raise SystemExit("FAIL: Google Play 16KB native-page requirement unmet")
    else:
        print(f"PASS: all {count} 64-bit native libraries use at least 16KB ELF alignment")


if __name__ == "__main__":
    main()
