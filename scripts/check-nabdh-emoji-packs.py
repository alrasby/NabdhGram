#!/usr/bin/env python3
"""Fail-fast source contracts for fully local Twemoji 17, preserving Telegram."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-emoji-packs.py TELEGRAM_SOURCE")
source = Path(sys.argv[1]).resolve()
ui = source / "TMessagesProj/src/main/java/org/telegram"
emoji = (ui / "messenger/Emoji.java").read_text(encoding="utf-8")
pack = (ui / "messenger/NabdhEmojiPacks.java").read_text(encoding="utf-8")
picker = (ui / "ui/NabdhAppearancePickerActivity.java").read_text(encoding="utf-8")
emoji_view = (ui / "ui/Components/EmojiView.java").read_text(encoding="utf-8")
scheduler = (ui / "ui/NabdhMessageSchedulerActivity.java").read_text(encoding="utf-8")
bundler = (Path(__file__).parent / "bundle-twemoji17.py").read_text(encoding="utf-8")


def require(ok: bool, desc: str) -> None:
    if not ok:
        raise SystemExit("FAIL: Twemoji 17 integration: " + desc)


require(emoji.count("NabdhEmojiPacks.wrap(code, ed)") == 1
        and "new SimpleEmojiDrawable(info, endsWithRightArrow(code))" in emoji,
        "Telegram native emoji drawable must remain an accurate fallback")
require('public static final String TWEMOJI = "twemoji";' in pack
        and 'public static final String SYSTEM = "system";' in pack
        and 'public static final String TELEGRAM = "telegram";' in pack
        and 'public static final String NOTO' not in pack
        and 'public static final String OPENMOJI' not in pack
        and 'NabdhEmojiPacks.NOTO' not in picker
        and 'NabdhEmojiPacks.OPENMOJI' not in picker
        and "Twemoji 17" in picker,
        "only Telegram/system/Twemoji17 choices must remain")
require("class BundledEmoji extends Emoji.EmojiDrawable" in pack
        and "nativeDrawable.draw(canvas);" in pack
        and "canvas.drawBitmap(bitmap, null, bounds, PAINT);" in pack
        and "getAssets().open(ASSET_ROOT + file)" in pack
        and 'private static final String ASSET_ROOT = "nabdh_twemoji/72x72/";' in pack
        and "LruCache<String, Bitmap>" in pack,
        "twemoji must render bundled actual PNGs with bounded memory and native fallback")
require("TWEMOJI.equals(selected())" in pack
        and "SharedConfig.useSystemEmoji = SYSTEM.equals(pack);" in pack
        and 'getSharedPreferences(PREFS, Context.MODE_PRIVATE)' in pack
        and 'if (!isSupported(pack) || !isReady(pack)) pack = TELEGRAM;' in pack
        and "Emoji.invalidateUiRunnable.run();" in pack,
        "selection must migrate legacy preferences and redraw locally")
require(not any(name in pack for name in (
            "HttpURLConnection", "new URL(", "getInputStream()", "getCacheDir()",
            "installAndChoose", "ThreadPoolExecutor", "downloadBitmap", "requestBitmap",
            "cdn.jsdelivr", "NOTO_BASE", "OPENMOJI_BASE")),
        "no on-device CDN, per-icon lazy fetch or obsolete remote engines")
require("installAndChoose(" not in picker
        and "NabdhEmojiPacks.choose(this, pack)" in picker
        and "NabdhEmojiPacks.isReady(pack)" in picker
        and "Emoji.replaceEmoji(" in picker,
        "picker must switch bundled assets instantly without an install screen")
require("b6b55fef1e8636b540a6d016a4729ca8cdf2e60b" in bundler
        and 'VERSION = "17.0.3"' in bundler
        and "LICENSE-GRAPHICS" in bundler
        and "MIN_IMAGES = 3000" in bundler
        and "SHA256SUMS.txt" in bundler
        and "MAX_ASSETS" in bundler
        and "PNG_SIGNATURE" in bundler
        and "1f600.png" in bundler,
        "pinned upstream artwork bundler and attribution validation missing")
require("keep emoji/GIF/sticker tabs stable during scroll" in emoji_view
        and "checkBottomTabScroll(dy);" not in emoji_view,
        "working emoji panel stability fix must not regress")
require("ArrayList<TLRPC.TL_contact> telegramContacts" in scheduler
        and "new ArrayList<>(telegramContacts)" in scheduler
        and "TextView countLabel = section(" in scheduler,
        "scheduled-message type-safety regression")
print("PASS: Telegram / Android / bundled Twemoji 17.0.3 source contracts, "
      "no runtime network, original bot/emoji stability retained")
