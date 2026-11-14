#!/usr/bin/env python3
"""Inspect the FINAL compiled APK's Android 12 splash in day AND night mode.

Unlike checking source XML, this reads resources.arsc, where Android's
values-night qualifier can outrank values-v31. Standard library only.
"""
import re
import struct
import sys
import zipfile
from pathlib import Path

SPLASH_ICON_ATTR = 0x0101062D
SPLASH_BG_ATTR = 0x0101062C
BRAND_BG = 0xFF04252A

def require(ok, reason):
    if not ok:
        raise AssertionError(reason)

def compiled_id(aapt, resource):
    ids = re.findall(r"(?m)^\s*spec resource (0x[0-9a-fA-F]+) \S+:"
                     + re.escape(resource) + r":", aapt)
    require(len(ids) == 1, "Missing/ambiguous packaged resource: " + resource)
    return int(ids[0], 16)

def style_configs(table, style_id):
    def u16(p): return struct.unpack_from("<H", table, p)[0]
    def u32(p): return struct.unpack_from("<I", table, p)[0]
    wanted_type = (style_id >> 16) & 255
    wanted_entry = style_id & 65535
    found = []
    def chunks(start, end):
        cursor = start
        while cursor + 8 <= end:
            kind, header, size = struct.unpack_from("<HHI", table, cursor)
            require(size >= header >= 8 and cursor + size <= end,
                    "Invalid Android resources.arsc chunk")
            if kind in (0x0002, 0x0200):
                chunks(cursor + header, cursor + size)
            elif kind == 0x0201 and table[cursor + 8] == wanted_type:
                count, entry_start = u32(cursor + 12), u32(cursor + 16)
                if wanted_entry < count:
                    offset = u32(cursor + header + wanted_entry * 4)
                    if offset != 0xffffffff:
                        entry = cursor + entry_start + offset
                        require(u16(entry) == 16 and u16(entry + 2) & 1,
                                "Startup style changed from complex map")
                        config_len = u32(cursor + 20)
                        require(config_len >= 32, "Unsupported compiled Android config")
                        config = table[cursor + 20:cursor + 20 + config_len]
                        sdk = struct.unpack_from("<H", config, 24)[0]
                        night = config[29] & 0x30 == 0x20
                        values = {}
                        for i in range(u32(entry + 12)):
                            p = entry + 16 + i * 12
                            values[u32(p)] = (table[p + 7], u32(p + 8))
                        found.append((sdk, night, values))
            cursor += size
    chunks(0, len(table))
    require(found, "Theme.TMessages.Start missing from compiled APK")
    return found

def verify(apk, dumped_resources, dumped_manifest):
    aapt = Path(dumped_resources).read_text(encoding="utf-8")
    style = compiled_id(aapt, "style/Theme.TMessages.Start")
    brand = compiled_id(aapt, "drawable/nabdhgram_launcher_foreground")
    telegram = compiled_id(aapt, "drawable/tg_splash_320")
    manifest = Path(dumped_manifest).read_text(encoding="utf-8")
    require(manifest.count(f"android:theme(0x01010000)=@0x{style:08x}") >= 2,
            "APK application and LaunchActivity must use audited launch style")
    with zipfile.ZipFile(apk) as archive:
        data = archive.read("resources.arsc")
    checked = []
    for sdk, night, values in style_configs(data, style):
        if SPLASH_ICON_ATTR not in values:
            continue
        where = ("night" if night else "day") + "-v" + str(sdk)
        icon_type, icon = values[SPLASH_ICON_ATTR]
        require(icon_type == 1 and icon != telegram and icon == brand,
                f"Unbranded compiled {where} startup icon: {icon:#010x}; expected {brand:#010x}")
        bg_type, bg = values.get(SPLASH_BG_ATTR, (-1, -1))
        require(bg_type == 0x1d and bg == BRAND_BG,
                f"Wrong compiled {where} startup background: {bg:#010x}")
        checked.append(where)
    require(any(c.startswith("day-") for c in checked), "Day startup not verified")
    require(any(c.startswith("night-") for c in checked), "Night startup not verified")
    print("PASS: packaged NabdhGram startup logo in: " + ", ".join(checked))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: check-packaged-splash.py APK apk-resources.txt apk-manifest-tree.txt")
    verify(*sys.argv[1:])
