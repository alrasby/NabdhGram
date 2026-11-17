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
emoji_view = (ui / "ui/Components/EmojiView.java").read_text(encoding="utf-8")

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
             "HttpURLConnection", "ThreadPoolExecutor(", "ArrayBlockingQueue<>(256)",
             "getNoBackupFilesDir()", "getCacheDir()", "Character.codePointAt",
             "setConnectTimeout", "setReadTimeout",
             "SharedConfig.useSystemEmoji = SYSTEM.equals(pack)",
             'putString("pack", pack)', "if (bitmap == null)",
             "return false; // Keep Telegram's native emoji visible while fetching."):
    require(attr in pack, "real safe pack loading missing: " + attr)
for licence in ("Apache-2.0", "CC-BY-4.0", "CC-BY-SA-4.0"):
    require(licence in pack, "third-party attribution missing: " + licence)
require('private static final String READY_MARKER = ".nabdh_pack_complete_v2"' in pack
        and "public static boolean isReady(String pack)" in pack
        and "if (!isSupported(pack) || !isReady(pack)) pack = TELEGRAM;" in pack
        and "if (!isReady(pack)) throw new IllegalStateException" in pack
        and "public static void installAndChoose(Context context, String pack, InstallListener listener)" in pack
        and "for (String[] section : EmojiData.data)" in pack
        and "for (String[] section : EmojiData.dataColored)" in pack
        and "final CountDownLatch workers = new CountDownLatch(6);" in pack
        and "done.get() == total" in pack
        and "errors.get() == 0" in pack
        and "output.getFD().sync();" in pack
        and "if (complete && version == selectionVersion)" in pack
        and "NabdhEmojiPacks.installAndChoose(getApplicationContext(), pack, installListener)" in picker,
        "external pack must install the full picker inventory before atomic activation")
require("6, 6, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(256)" in pack
        and 'new File(context.getNoBackupFilesDir(), "nabdh_emoji_" + pack)' in pack
        and "legacy.renameTo(file);" in pack
        and "File file = new File(packFolder(context, pack)" in pack
        and "Bitmap bitmap = decode(file);" in pack,
        "installed images must render from private durable files without late CDN requests")
require("requestBitmap(code);" not in pack
        and "nativeDrawable.preload();" in pack
        and "if (downloaded == null) errors.incrementAndGet();" in pack
        and "errors.get() < 10" in pack,
        "no per-glyph lazy reload or activation after a failed/offline install")
require("NotificationCenter.didSetNewTheme" in pack
        and "Emoji.invalidateUiRunnable.run()" in pack
        and "Emoji.replaceEmoji(" in picker,
        "switch must repaint old spans and render actual sample")
require('if (TELEGRAM.equals(pack) || SYSTEM.equals(pack)) return;' in pack
        and "NabdhEmojiPacks.choose(this, pack)" in picker
        and "NabdhEmojiPacks.installAndChoose(getApplicationContext(), pack, installListener)" in picker,
        "only user-selected art may download, with ready native fallback")
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
require("keep emoji/GIF/sticker tabs stable during scroll" in emoji_view
        and "checkBottomTabScroll(dy);" not in emoji_view
        and "showBottomTab(true, true);" in emoji_view,
        "emoji tabs must stay pinned during scrolling without disabling explicit actions")
require("Math.abs(bottomTabContainer.getTranslationY() -" in emoji_view
        and "nextBottomTabTranslation) >= 0.5f" in emoji_view
        and "bottomTabContainer.setTranslationY(nextBottomTabTranslation);" in emoji_view,
        "bottom-tab translation must skip subpixel redundant redraws")
print("PASS: live opt-in Noto/Twemoji/OpenMoji PNG draw, bounded cache, "
      "Telegram fallback, licenses, and #686 Java type shadows")
