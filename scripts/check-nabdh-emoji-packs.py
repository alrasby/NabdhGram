#!/usr/bin/env python3
"""Fail-fast contract for true, opt-in, independently rendered PNG emoji packs."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-nabdh-emoji-packs.py TELEGRAM_SOURCE")
ui = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram"
emoji = (ui / "messenger/Emoji.java").read_text(encoding="utf-8")
pack = (ui / "messenger/NabdhEmojiPacks.java").read_text(encoding="utf-8")
picker = (ui / "ui/NabdhAppearancePickerActivity.java").read_text(encoding="utf-8")
scheduler = (ui / "ui/NabdhMessageSchedulerActivity.java").read_text(encoding="utf-8")

def require(ok, desc):
    if not ok:
        raise SystemExit("FAIL: emoji integration " + desc)

require(emoji.count("NabdhEmojiPacks.wrap(code, ed)") == 1
        and "new SimpleEmojiDrawable(info, endsWithRightArrow(code))" in emoji,
        "must keep native fallback in Telegram Emoji.getEmojiDrawable")
require("extends Emoji.EmojiDrawable" in pack
        and "nativeDrawable.draw(canvas)" in pack
        and "canvas.drawBitmap(bitmap, null, bounds, PAINT)" in pack,
        "independent PNG must actually draw over native spans")
for name in ("NOTO", "TWEMOJI", "OPENMOJI", "TELEGRAM", "SYSTEM"):
    require('public static final String ' + name in pack
            and 'NabdhEmojiPacks.' + name in picker,
            "picker entry missing working renderer " + name)
for attr in ("2D/png/72/", "assets/72x72/", "color/72x72/",
             "MAX_IMAGE_BYTES", "MAX_DISK_BYTES", "LruCache",
             "HttpURLConnection", "ThreadPoolExecutor(", "ArrayBlockingQueue<>(64)",
             "getCacheDir()", "Character.codePointAt",
             "setConnectTimeout", "setReadTimeout",
             "SharedConfig.useSystemEmoji = SYSTEM.equals(pack)",
             'putString("pack", pack)', "if (bitmap == null)",
             "return false; // Keep Telegram's native emoji visible while fetching."):
    require(attr in pack, "real safe pack loading missing: " + attr)
for licence in ("Apache-2.0", "CC-BY-4.0", "CC-BY-SA-4.0"):
    require(licence in pack, "third-party attribution missing: " + licence)
require("NotificationCenter.didSetNewTheme" in pack
        and "Emoji.invalidateUiRunnable.run()" in pack
        and "Emoji.replaceEmoji(" in picker,
        "switch must repaint old spans and render actual sample")
require('if (TELEGRAM.equals(pack) || SYSTEM.equals(pack)) return;' in pack
        and "NabdhEmojiPacks.choose(this, pack)" in picker,
        "no background requests unless user chooses external art")
require(all(k in pack for k in ("TEMPORARY_RETRY_MS", "MISSING_GLYPH_RETRY_MS",
        "RETRY_AFTER", "SystemClock.elapsedRealtime()", "HTTP_NOT_FOUND",
        "FileNotFoundException", "RejectedExecutionException", "pack.equals(selected())",
        "if (PENDING.contains(id)", "return size() > 1024;")),
        "offline CDN failures must retry with bounded backoff; missing PNGs must not loop")
require("private static final Set<String> NOT_FOUND" not in pack,
        "do not permanently suppress an emoji glyph after a transient offline error")
require("Build.MANUFACTURER" not in picker and "AutoCompleteTextView" not in scheduler,
        "no placebo OEM label or native dropdown")
require("ArrayList<TLRPC.TL_contact> telegramContacts" in scheduler
        and "new ArrayList<>(telegramContacts)" in scheduler
        and "TextView countLabel = section(" in scheduler
        and "renderChoices(list, pending, v.toString(), countLabel)" in scheduler,
        "fix both scheduler #686 Java compile type-shadowing errors")
require(not any(x in pack for x in
                ("getDialogMessage(", "READ_CONTACTS", "getChat(", "getMessageText(")),
        "emoji CDN must not receive message/contact content")
print("PASS: live opt-in Noto/Twemoji/OpenMoji PNG draw, bounded cache, "
      "Telegram fallback, licenses, and #686 Java type shadows")
