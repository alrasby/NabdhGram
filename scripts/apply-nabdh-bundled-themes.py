#!/usr/bin/env python3
"""Register four user-approved NabdhGram .attheme assets as bundled Telegram themes.

Never decode/re-encode theme bytes: embedded WPS JPEG wallpapers must survive.
Optional until the binary assets are added to branding/themes in the GitHub repo.
"""
from pathlib import Path
import hashlib
import sys
import zipfile

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-bundled-themes.py TELEGRAM_SOURCE")

root = Path(sys.argv[1])
themes = [
    ("nabdh_siri_refined.attheme", "NabdhGram • Siri Glass Refined", 0xFFEDEFF0, 0xFFDFE0E4, 0xFFDBDCD8,
     "75f9d70c9714d3a87c2531cf664627d60994caf2f3366663a3351c3edfac6497"),
    ("nabdh_soft_mint.attheme", "NabdhGram • Soft Mint", 0xFFE5F3F2, 0xFFD8EDEA, 0xFFB6E9D5,
     "2e1d755c59c640b1dd191ac4eda18e8232dc75347b6bef66dc1f80f094dfd011"),
    ("nabdh_dark.attheme", "NabdhGram • Dark Glass", 0xFF101B24, 0xFF203740, 0xFF24454A,
     "fc06d71577698ae0cf6b8879e5175274d5d0def85de1a1369dbaa0ca0627a617"),
    ("nabdh_sand.attheme", "NabdhGram • Gray Avalanche Sand", 0xFFD4C4AE, 0xFFE4D7C6, 0xFFD7C8B7,
     "b32ed42b89ac7375e7fddbe6833a506e89fe25436651696af5ff4346a5c46f7f"),
]
# Accept the validated existing archive until the new binary ZIP is staged.
# Select each preview palette only after verifying the matching asset digest.
UPDATED_THEME_SPECS = {
    "nabdh_siri_refined.attheme": (
        "ec27974ab1930be4a6015d5d907d11acd3fcf08ac79f834d539958abb8a5b2a6",
        0xFFF0F7F5, 0xFFF8FCFB, 0xFFDFF2F0),
    "nabdh_soft_mint.attheme": (
        "2e1d755c59c640b1dd191ac4eda18e8232dc75347b6bef66dc1f80f094dfd011",
        0xFFECF5F3, 0xFFFFFFFF, 0xFFE5F3F2),
    "nabdh_dark.attheme": (
        "fc06d71577698ae0cf6b8879e5175274d5d0def85de1a1369dbaa0ca0627a617",
        0xFF101B24, 0xFF223942, 0xFF275157),
    "nabdh_sand.attheme": (
        "9d81f3276c1db4f0f6edc88aa6d82fbf3338c961407948fe5084a4f5e15f255b",
        0xFFF3ECE0, 0xFFF3E8D7, 0xFFD7C0A8),
}


def resolve_verified_theme(spec, data):
    filename, name, background, incoming, outgoing, old_digest = spec
    digest = hashlib.sha256(data).hexdigest()
    updated_digest, updated_bg, updated_in, updated_out = UPDATED_THEME_SPECS[filename]
    if digest == updated_digest:
        # The updated assets use embedded WPS JPEGs, including Sand which
        # previously referenced a WLS remote wallpaper. Verify the bytes
        # before replacing anything in the Telegram build checkout.
        from PIL import Image
        from io import BytesIO
        marker = data.find(b"WPS\n")
        if marker < 0 or data[marker + 4:marker + 7] != b"\xff\xd8\xff":
            raise SystemExit("Missing embedded JPEG wallpaper: " + filename)
        try:
            with Image.open(BytesIO(data[marker + 4:])) as wallpaper:
                wallpaper.verify()
        except Exception as error:
            raise SystemExit("Invalid bundled wallpaper " + filename + ": " + str(error))
        return filename, name, updated_bg, updated_in, updated_out, updated_digest
    if digest == old_digest:
        return spec
    raise SystemExit("Unrecognized SHA-256 for " + filename + ": " + digest)


asset_dir = Path(__file__).resolve().parents[1] / "branding" / "themes"
archive = asset_dir / "NabdhGram_Bundled_Themes.zip"
available = [asset_dir / spec[0] for spec in themes]
verified_themes = []
verified_assets = []
if archive.is_file():
    # The approved ZIP keeps the four original binary files under branding/themes/.
    # Read only expected members: never extract arbitrary paths from a ZIP.
    with zipfile.ZipFile(archive) as bundled:
        expected = {"branding/themes/" + spec[0] for spec in themes}
        actual = {name for name in bundled.namelist() if name.endswith(".attheme")}
        if actual != expected:
            raise SystemExit("Theme archive has unexpected or missing .attheme members")
        for filename, name, background, incoming, outgoing, checksum in themes:
            entry = bundled.getinfo("branding/themes/" + filename)
            if entry.file_size > 5 * 1024 * 1024:
                raise SystemExit(f"Theme asset is unexpectedly large: {filename}")
            data = bundled.read(entry)
            verified_themes.append(resolve_verified_theme((filename, name, background, incoming, outgoing, checksum), data))
            verified_assets.append((filename, data))
elif all(p.is_file() for p in available):
    for spec, original in zip(themes, available):
        verified_themes.append(resolve_verified_theme(spec, original.read_bytes()))
        verified_assets.append((original.name, original.read_bytes()))
elif any(p.is_file() for p in available):
    raise SystemExit("Incomplete theme bundle: all four .attheme assets are required")
else:
    raise SystemExit("Missing NabdhGram theme ZIP or individual approved .attheme assets")

# Do not register anything until all four resources pass integrity checks.
if len(verified_themes) != 4 or len({spec[0] for spec in verified_themes}) != 4:
    raise SystemExit("Invalid bundled theme inventory")
themes = verified_themes
for filename, data in verified_assets:
    destination = root / "TMessagesProj/src/main/assets" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)

target = root / "TMessagesProj/src/main/java/org/telegram/ui/ActionBar/Theme.java"
source = target.read_text(encoding="utf-8")
anchor = """        sortThemes();

        ThemeInfo applyingTheme = null;"""
if source.count(anchor) != 1:
    raise SystemExit("Built-in Theme registration anchor changed; inspect upstream before patching")

lines = [
    "        // NabdhGram: bundled original .attheme files with wallpaper bytes intact.",
]
for filename, name, background, incoming, outgoing, sha in themes:
    lines.extend([
        "        themeInfo = new ThemeInfo();",
        f'        themeInfo.name = "{name}";',
        f'        themeInfo.assetName = "{filename}";',
        f"        themeInfo.previewBackgroundColor = 0x{background:08X};",
        f"        themeInfo.previewInColor = 0x{incoming:08X};",
        f"        themeInfo.previewOutColor = 0x{outgoing:08X};",
        # Critical: ThemeInfo.isDark() otherwise constructs new File(pathToFile)
        # when isDark is UNKNOWN. Bundled assets have assetName but no pathToFile,
        # so that constructor receives null during palette changes and crashes.
        # The approved four assets' windowBackgroundWhite values were inspected:
        # only nabdh_dark.attheme uses a dark base (#101B24).
        "        themeInfo.isDark = ThemeInfo."
        + ("DARK;" if filename == "nabdh_dark.attheme" else "LIGHT;"),
        "        themes.add(themeInfo);",
        "        themesDict.put(themeInfo.getKey(), themeInfo);",
    ])
source = source.replace(anchor, "\n".join(lines) + "\n\n" + anchor, 1)
# Defensive support for asset themes: if a future bundled theme doesn't have a
# cached isDark value, it must read its asset rather than constructing File(null).
is_dark_old = """            if (isDark == UNKNOWN) {
                String[] wallpaperLink = new String[1];
                SparseIntArray colors = getThemeFileValues(new File(pathToFile), null, wallpaperLink);
                checkIsDark(colors, this);
            }"""
is_dark_new = """            if (isDark == UNKNOWN) {
                String[] wallpaperLink = new String[1];
                if (assetName != null) {
                    checkIsDark(getThemeFileValues(null, assetName, wallpaperLink), this);
                } else if (pathToFile != null) {
                    checkIsDark(getThemeFileValues(new File(pathToFile), null, wallpaperLink), this);
                } else {
                    // Native/default theme: no backing file to open.
                    // Unknown palettes should never crash on File(null).
                    isDark = previewBackgroundColor != 0
                            && ColorUtils.calculateLuminance(previewBackgroundColor) < .5f
                            ? DARK : LIGHT;
                }
            }"""
if source.count(is_dark_old) != 1:
    raise SystemExit("ThemeInfo.isDark fallback anchor changed")
source = source.replace(is_dark_old, is_dark_new, 1)
# Preserve Telegram's wallpaper-link handling for legacy WLS assets;
# updated bundled WPS JPEG wallpaper bytes remain untouched.
wallpaper_old = "currentColorsNoAccent = getThemeFileValues(null, themeInfo.assetName, null);"
wallpaper_new = "currentColorsNoAccent = getThemeFileValues(null, themeInfo.assetName, wallpaperLink);"
if source.count(wallpaper_old) != 1:
    raise SystemExit("Telegram built-in asset wallpaper parser anchor changed")
source = source.replace(wallpaper_old, wallpaper_new, 1)

target.write_text(source, encoding="utf-8")
print("Registered 4 bundled NabdhGram theme assets in native Telegram selector.")


# Enrich ONLY the four owned NabdhGram theme cards. Telegram's other themes
# retain their upstream preview. The original ThemeInfo.name is untouched,
# so native dialogs/details and accessibility retain the full title.
cell = root / "TMessagesProj/src/main/java/org/telegram/ui/Cells/ThemesHorizontalListCell.java"
cell_src = cell.read_text(encoding="utf-8")
def replace_cell(old, new, label):
    global cell_src
    if cell_src.count(old) != 1:
        raise SystemExit("Pinned theme selector changed (" + label + "); refusing unsafe patch")
    cell_src = cell_src.replace(old, new, 1)

# Reuse a single preview paint per mini-card instead of allocating per frame.
replace_cell(
    "        private Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);",
    """        private Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint nabdhPreviewPaint = new Paint(Paint.ANTI_ALIAS_FLAG);""",
    "cache bundled theme mini-preview paint")

replace_cell(
    """            String text = TextUtils.ellipsize(name, textPaint, maxWidth, TextUtils.TruncateAt.END).toString();
            int width = (int) Math.ceil(textPaint.measureText(text));
            textPaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            canvas.drawText(text, x + (AndroidUtilities.dp(76) - width) / 2, AndroidUtilities.dp(131), textPaint);""",
    """            textPaint.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            if (themeInfo.assetName != null && themeInfo.assetName.startsWith("nabdh_")) {
                // The complete original name remains in ThemeInfo and native details.
                // Use a readable two-line label only in this 76dp mini-card.
                String cardName = name.startsWith("NabdhGram • ")
                        ? name.substring("NabdhGram • ".length()) : name;
                // Split by measured width, not by the last word: long names
                // such as Gray Avalanche Sand should remain balanced.
                int split = -1;
                float best = Float.MAX_VALUE;
                for (int pos = cardName.indexOf(' '); pos >= 0;
                        pos = cardName.indexOf(' ', pos + 1)) {
                    float a = textPaint.measureText(cardName, 0, pos);
                    float b = textPaint.measureText(cardName, pos + 1, cardName.length());
                    float score = Math.max(a, b);
                    if (score < best) {
                        best = score;
                        split = pos;
                    }
                }
                String first = split > 0 ? cardName.substring(0, split) : cardName;
                String second = split > 0 ? cardName.substring(split + 1) : "";
                first = TextUtils.ellipsize(first, textPaint, maxWidth, TextUtils.TruncateAt.END).toString();
                second = TextUtils.ellipsize(second, textPaint, maxWidth, TextUtils.TruncateAt.END).toString();
                canvas.drawText(first, x + (AndroidUtilities.dp(76) - textPaint.measureText(first)) / 2,
                        AndroidUtilities.dp(127), textPaint);
                canvas.drawText(second, x + (AndroidUtilities.dp(76) - textPaint.measureText(second)) / 2,
                        AndroidUtilities.dp(143), textPaint);
            } else {
                String text = TextUtils.ellipsize(name, textPaint, maxWidth, TextUtils.TruncateAt.END).toString();
                int width = (int) Math.ceil(textPaint.measureText(text));
                canvas.drawText(text, x + (AndroidUtilities.dp(76) - width) / 2, AndroidUtilities.dp(131), textPaint);
            }""",
    "two-line brand theme title")

replace_cell(
    """                inDrawable.setBounds(x + AndroidUtilities.dp(6), AndroidUtilities.dp(22), x + AndroidUtilities.dp(6 + 43), AndroidUtilities.dp(22 + 14));
                inDrawable.draw(canvas);

                outDrawable.setBounds(x + AndroidUtilities.dp(27), AndroidUtilities.dp(41), x + AndroidUtilities.dp(27 + 43), AndroidUtilities.dp(41 + 14));
                outDrawable.draw(canvas);""",
    """                if (themeInfo.assetName != null && themeInfo.assetName.startsWith("nabdh_")) {
                    // Small conversation mockup, rendered using each theme's
                    // real background and incoming/outgoing bubble colors.
                    // No personal messages or screenshots are embedded.
                    int saved = canvas.save();
                    canvas.clipRect(rect);
                    Paint miniPaint = nabdhPreviewPaint;
                    // Match selected theme palette in preview; never hard-code
                    // light-only chrome on Emerald/Dark Glass themes.
                    int previewBackground = blend(oldBackColor, backColor);
                    int previewInk = (Color.red(previewBackground) * 299
                            + Color.green(previewBackground) * 587
                            + Color.blue(previewBackground) * 114) > 150000
                            ? 0xFF33464B : 0xFFF1F6F5;
                    float left = rect.left;
                    float top = rect.top;
                    float dp = AndroidUtilities.density;
                    miniPaint.setColor(blend(oldInColor, inColor));
                    canvas.drawRoundRect(left + 3 * dp, top + 3 * dp,
                            left + 73 * dp, top + 24 * dp, 4 * dp, 4 * dp, miniPaint);
                    miniPaint.setColor(blend(oldOutColor, outColor));
                    canvas.drawCircle(left + 13 * dp, top + 13 * dp, 6 * dp, miniPaint);
                    miniPaint.setColor(previewInk);
                    canvas.drawRoundRect(left + 24 * dp, top + 9 * dp,
                            left + 55 * dp, top + 12 * dp, 2 * dp, 2 * dp, miniPaint);
                    miniPaint.setColor(blend(oldInColor, inColor));
                    canvas.drawRoundRect(left + 5 * dp, top + 30 * dp,
                            left + 56 * dp, top + 49 * dp, 6 * dp, 6 * dp, miniPaint);
                    miniPaint.setColor(previewInk);
                    canvas.drawRoundRect(left + 11 * dp, top + 36 * dp,
                            left + 42 * dp, top + 39 * dp, 2 * dp, 2 * dp, miniPaint);
                    miniPaint.setColor(blend(oldOutColor, outColor));
                    canvas.drawRoundRect(left + 21 * dp, top + 53 * dp,
                            left + 70 * dp, top + 72 * dp, 6 * dp, 6 * dp, miniPaint);
                    miniPaint.setColor(previewInk);
                    canvas.drawRoundRect(left + 28 * dp, top + 59 * dp,
                            left + 61 * dp, top + 62 * dp, 2 * dp, 2 * dp, miniPaint);
                    miniPaint.setColor(blend(oldInColor, inColor));
                    canvas.drawRoundRect(left + 4 * dp, top + 80 * dp,
                            left + 72 * dp, top + 93 * dp, 6 * dp, 6 * dp, miniPaint);
                    miniPaint.setColor(previewInk);
                    canvas.drawRoundRect(left + 10 * dp, top + 85 * dp,
                            left + 48 * dp, top + 88 * dp, 2 * dp, 2 * dp, miniPaint);
                    canvas.restoreToCount(saved);
                } else {
                    inDrawable.setBounds(x + AndroidUtilities.dp(6), AndroidUtilities.dp(22), x + AndroidUtilities.dp(6 + 43), AndroidUtilities.dp(22 + 14));
                    inDrawable.draw(canvas);

                    outDrawable.setBounds(x + AndroidUtilities.dp(27), AndroidUtilities.dp(41), x + AndroidUtilities.dp(27 + 43), AndroidUtilities.dp(41 + 14));
                    outDrawable.draw(canvas);
                }""",
    "mini chat preview")

# V2 gallery: ONLY the four owned assets open a non-destructive preview.
# Other Telegram/third-party themes retain the stock one-tap behavior.
replace_cell(
    """        setOnItemClickListener((view1, position) -> {
            selectTheme(((InnerThemeView) view1).themeInfo, view1);""",
    """        setOnItemClickListener((view1, position) -> {
            Theme.ThemeInfo tapped = ((InnerThemeView) view1).themeInfo;
            if (tapped != null && tapped.assetName != null
                    && tapped.assetName.startsWith("nabdh_")) {
                nabdhPreviewBundledTheme(tapped, view1);
                return; // A preview tap must never silently apply the theme.
            }
            selectTheme(tapped, view1);""",
    "preview owned themes without changing Telegram's native selection")

replace_cell(
    """    public void selectTheme(Theme.ThemeInfo themeInfo) {
        selectTheme(themeInfo, null);
    }""",
    """    // Bundled cards are previewed without changing Telegram theme state.
    // Telegram's stock themeconfig and saveCustomTheme flow remains the only
    // way to apply changes; previous selection is stored as a stable key.
    private void nabdhPreviewBundledTheme(Theme.ThemeInfo selected, View tapped) {
        if (fragment == null || fragment.getParentActivity() == null) {
            return;
        }
        final android.content.Context context = fragment.getParentActivity();
        final boolean arabic = LocaleController.isRTL;
        final int background = selected.getPreviewBackgroundColor();
        final int incoming = selected.getPreviewInColor();
        final int outgoing = selected.getPreviewOutColor();
        final boolean night = currentType == ThemeActivity.THEME_TYPE_NIGHT;
        final SharedPreferences prefs = ApplicationLoader.applicationContext
                .getSharedPreferences("nabdh_theme_gallery", Activity.MODE_PRIVATE);
        final String key = night ? "previousNightTheme" : "previousDayTheme";
        final Theme.ThemeInfo previous = Theme.getTheme(prefs.getString(key, ""));
        // These are Telegram's own stable bundled defaults, not new themes.
        final Theme.ThemeInfo defaultChoice = Theme.getTheme(night ? "Night" : "Blue");
        android.widget.LinearLayout content = new android.widget.LinearLayout(context);
        content.setOrientation(android.widget.LinearLayout.VERTICAL);
        content.setPadding(AndroidUtilities.dp(16), AndroidUtilities.dp(10),
                AndroidUtilities.dp(16), AndroidUtilities.dp(10));
        content.setLayoutDirection(arabic ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        final int foreground = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText);
        final int dim = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2);

        // Colors AND wallpaper both come from the verified bundled .attheme.
        // No temporary theme changes are made when opening a preview.
        android.widget.LinearLayout mock = new android.widget.LinearLayout(context);
        mock.setOrientation(android.widget.LinearLayout.VERTICAL);
        mock.setPadding(AndroidUtilities.dp(12), AndroidUtilities.dp(12),
                AndroidUtilities.dp(12), AndroidUtilities.dp(12));
        android.graphics.drawable.GradientDrawable surface = new android.graphics.drawable.GradientDrawable();
        surface.setColor(background);
        surface.setCornerRadius(AndroidUtilities.dp(16));
        mock.setBackground(surface);
        android.widget.LinearLayout.LayoutParams block =
                new android.widget.LinearLayout.LayoutParams(
                        android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT);
        block.setMargins(0, AndroidUtilities.dp(8), 0, AndroidUtilities.dp(8));
        // Decode a bounded sample of the actual embedded WPS JPEG only when
        // opening details (never while scrolling the four miniature cards).
        android.graphics.Bitmap wallpaper = nabdhBundledWallpaper(context, selected);
        if (wallpaper != null) {
            android.graphics.drawable.BitmapDrawable actual =
                    new android.graphics.drawable.BitmapDrawable(context.getResources(), wallpaper);
            actual.setGravity(android.view.Gravity.FILL);
            mock.setBackground(actual);
            mock.setOutlineProvider(new android.view.ViewOutlineProvider() {
                @Override public void getOutline(View view, android.graphics.Outline outline) {
                    outline.setRoundRect(0, 0, view.getWidth(), view.getHeight(),
                            AndroidUtilities.dp(16));
                }
            });
            mock.setClipToOutline(true);
        }
        content.addView(mock, block);

        android.widget.TextView chatTitle = new android.widget.TextView(context);
        chatTitle.setText(arabic ? "المحادثات  •  معاينة" : "Chats  •  Preview");
        chatTitle.setTextSize(14);
        chatTitle.setTextColor(nabdhThemePreviewInk(background));
        chatTitle.setPadding(AndroidUtilities.dp(9), AndroidUtilities.dp(5),
                AndroidUtilities.dp(9), AndroidUtilities.dp(12));
        mock.addView(chatTitle);

        android.widget.TextView row = new android.widget.TextView(context);
        row.setText(arabic ? "◉  محادثة تجريبية\\n      آخر رسالة" : "◉  Sample conversation\\n      Last message");
        row.setTextSize(13);
        row.setTextColor(nabdhThemePreviewInk(incoming));
        row.setPadding(AndroidUtilities.dp(12), AndroidUtilities.dp(10),
                AndroidUtilities.dp(12), AndroidUtilities.dp(10));
        android.graphics.drawable.GradientDrawable card = new android.graphics.drawable.GradientDrawable();
        card.setColor(incoming);
        card.setCornerRadius(AndroidUtilities.dp(13));
        row.setBackground(card);
        mock.addView(row, new android.widget.LinearLayout.LayoutParams(
                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                android.view.ViewGroup.LayoutParams.WRAP_CONTENT));

        android.widget.TextView received = new android.widget.TextView(context);
        received.setText(arabic ? "رسالة واردة" : "Incoming message");
        received.setTextSize(13);
        received.setTextColor(nabdhThemePreviewInk(incoming));
        received.setPadding(AndroidUtilities.dp(12), AndroidUtilities.dp(10),
                AndroidUtilities.dp(12), AndroidUtilities.dp(10));
        android.graphics.drawable.GradientDrawable receiveBg = new android.graphics.drawable.GradientDrawable();
        receiveBg.setColor(incoming);
        receiveBg.setCornerRadius(AndroidUtilities.dp(13));
        received.setBackground(receiveBg);
        android.widget.LinearLayout.LayoutParams receivedParams =
                new android.widget.LinearLayout.LayoutParams(
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT,
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT);
        receivedParams.setMargins(0, AndroidUtilities.dp(12), 0, AndroidUtilities.dp(4));
        mock.addView(received, receivedParams);

        android.widget.TextView sent = new android.widget.TextView(context);
        sent.setText(arabic ? "رسالة صادرة ✓✓" : "Outgoing message ✓✓");
        sent.setTextSize(13);
        sent.setTextColor(nabdhThemePreviewInk(outgoing));
        sent.setPadding(AndroidUtilities.dp(12), AndroidUtilities.dp(10),
                AndroidUtilities.dp(12), AndroidUtilities.dp(10));
        android.graphics.drawable.GradientDrawable sendBg = new android.graphics.drawable.GradientDrawable();
        sendBg.setColor(outgoing);
        sendBg.setCornerRadius(AndroidUtilities.dp(13));
        sent.setBackground(sendBg);
        android.widget.LinearLayout.LayoutParams sentParams =
                new android.widget.LinearLayout.LayoutParams(
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT,
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT);
        sentParams.gravity = arabic ? android.view.Gravity.LEFT : android.view.Gravity.RIGHT;
        sentParams.setMargins(0, AndroidUtilities.dp(4), 0, AndroidUtilities.dp(12));
        mock.addView(sent, sentParams);

        android.widget.TextView settings = new android.widget.TextView(context);
        settings.setText(arabic ? "⚙  الإعدادات    •    الملف الشخصي" :
                "⚙  Settings    •    Profile");
        settings.setTextColor(nabdhThemePreviewInk(background));
        settings.setTextSize(13);
        settings.setPadding(AndroidUtilities.dp(10), AndroidUtilities.dp(9),
                AndroidUtilities.dp(10), AndroidUtilities.dp(9));
        mock.addView(settings);
        android.widget.TextView hint = new android.widget.TextView(context);
        hint.setText(wallpaper != null
                ? (arabic ? "معاينة ثابتة للخلفية الأصلية وألوان الثيم."
                         : "Fixed preview of the original wallpaper and theme colors.")
                : (arabic ? "معاينة الألوان؛ لم تتوفر خلفية مضمّنة صالحة."
                          : "Color preview; no readable embedded wallpaper found."));
        hint.setTextColor(dim);
        hint.setTextSize(12);
        content.addView(hint);

        // A separate personal copy is imported under a unique filename by
        // Telegram. No writes ever target the bundled theme assets.
        android.widget.TextView copyHint = new android.widget.TextView(context);
        copyHint.setText(arabic
                ? "النسخة الشخصية ملف مستقل قابل للتحرير؛ إنشاؤها يطبّقها."
                : "A personal copy is an independent editable file; creating it applies it.");
        copyHint.setTextColor(dim);
        copyHint.setTextSize(12);
        copyHint.setPadding(0, AndroidUtilities.dp(8), 0, AndroidUtilities.dp(8));
        content.addView(copyHint);
        final org.telegram.ui.ActionBar.AlertDialog[] shown =
                new org.telegram.ui.ActionBar.AlertDialog[1];
        if (previous != null && previous != selected) {
            android.widget.TextView restore = new android.widget.TextView(context);
            restore.setText(arabic ? "↶ الرجوع إلى الثيم السابق" : "↶ Restore previous theme");
            restore.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
            restore.setTextSize(14);
            restore.setPadding(AndroidUtilities.dp(12), AndroidUtilities.dp(12),
                    AndroidUtilities.dp(12), AndroidUtilities.dp(12));
            content.addView(restore);
            restore.setOnClickListener(v -> {
                if (shown[0] != null) shown[0].dismiss();
                selectTheme(previous, null);
            });
        }
        if (defaultChoice != null && defaultChoice != selected) {
            android.widget.TextView reset = new android.widget.TextView(context);
            reset.setText(arabic ? "استعادة ثيم Telegram الافتراضي" :
                    "Restore Telegram default theme");
            reset.setTextSize(14);
            reset.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
            reset.setPadding(AndroidUtilities.dp(12), AndroidUtilities.dp(12),
                    AndroidUtilities.dp(12), AndroidUtilities.dp(12));
            content.addView(reset);
            reset.setOnClickListener(v -> {
                Theme.ThemeInfo before = night
                        ? Theme.getCurrentNightTheme() : Theme.getCurrentTheme();
                if (before != null && before != defaultChoice) {
                    prefs.edit().putString(key, before.getKey()).apply();
                }
                if (shown[0] != null) shown[0].dismiss();
                selectTheme(defaultChoice, null); // Persist with Telegram's native API.
            });
        }
        // Preview remains outside the scrolling controls.
        content.removeView(mock);
        android.widget.LinearLayout fixed = new android.widget.LinearLayout(context);
        fixed.setOrientation(android.widget.LinearLayout.VERTICAL);
        fixed.setPadding(AndroidUtilities.dp(12), 0, AndroidUtilities.dp(12), 0);
        fixed.addView(mock, block);
        android.widget.ScrollView scrolling = new android.widget.ScrollView(context);
        scrolling.setFillViewport(false);
        scrolling.addView(content);
        fixed.addView(scrolling, new android.widget.LinearLayout.LayoutParams(
                android.view.ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        int maxHeight = context.getResources().getDisplayMetrics().heightPixels * 65 / 100;
        fixed.setMinimumHeight(Math.min(maxHeight, AndroidUtilities.dp(460)));
        org.telegram.ui.ActionBar.AlertDialog.Builder dialog =
                new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                        .setTitle(selected.name)
                        .setView(fixed)
                        .setPositiveButton(arabic ? "تطبيق" : "Apply", (d, which) -> {
                            Theme.ThemeInfo before = night ?
                                    Theme.getCurrentNightTheme() : Theme.getCurrentTheme();
                            if (before != null && before != selected) {
                                prefs.edit().putString(key, before.getKey()).apply();
                            }
                            selectTheme(selected, tapped); // Native commit + instant update.
                        }).setNegativeButton(arabic ? "إغلاق" : "Close", null)
                        .setNeutralButton(arabic ? "نسخة شخصية" : "Personal copy",
                                (d, which) -> {
                                    // Prompt before importing; cancellation changes nothing.
                                    android.widget.EditText name = new android.widget.EditText(context);
                                    name.setSingleLine(true);
                                    name.setHint(arabic ? "اسم الثيم" : "Theme name");
                                    name.setFilters(new android.text.InputFilter[]{
                                            new android.text.InputFilter.LengthFilter(60)});
                                    android.widget.LinearLayout nameBox = new android.widget.LinearLayout(context);
                                    nameBox.setPadding(AndroidUtilities.dp(20), AndroidUtilities.dp(8),
                                            AndroidUtilities.dp(20), AndroidUtilities.dp(8));
                                    nameBox.addView(name, new android.widget.LinearLayout.LayoutParams(
                                            android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                                            android.view.ViewGroup.LayoutParams.WRAP_CONTENT));
                                    android.app.AlertDialog naming = new android.app.AlertDialog.Builder(context)
                                            .setTitle(arabic ? "تسمية النسخة الشخصية" : "Name personal copy")
                                            .setView(nameBox)
                                            .setNegativeButton(arabic ? "إلغاء" : "Cancel", null)
                                            .setPositiveButton(arabic ? "إنشاء" : "Create", null)
                                            .create();
                                    naming.setOnShowListener(ignored -> {
                                        naming.getButton(android.app.AlertDialog.BUTTON_POSITIVE)
                                                .setOnClickListener(button -> {
                                            String chosen = name.getText().toString().trim();
                                            if (chosen.isEmpty() || chosen.equals(".") || chosen.equals("..")
                                                    || chosen.indexOf('/') >= 0 || chosen.indexOf((char) 92) >= 0
                                                    || nabdhInvalidThemeName(chosen)) {
                                                name.setError(arabic ? "أدخل اسماً صالحاً" : "Enter a valid name");
                                                return;
                                            }
                                            String copyName = chosen + ".attheme";
                                            if (Theme.getTheme(chosen) != null || Theme.getTheme(copyName) != null
                                                    || new java.io.File(context.getFilesDir(), copyName).exists()) {
                                                name.setError(arabic ? "الاسم مستخدم" : "Name already exists");
                                                return;
                                            }
                                            Theme.ThemeInfo before = night ? Theme.getCurrentNightTheme() : Theme.getCurrentTheme();
                                            Theme.ThemeInfo copy = Theme.applyThemeFile(
                                                    Theme.getAssetFile(selected.assetName), copyName, null, false);
                                            if (copy == null) {
                                                name.setError(arabic ? "تعذر إنشاء النسخة" : "Could not create copy");
                                                return;
                                            }
                                            if (before != null) prefs.edit().putString(key, before.getKey()).apply();
                                            naming.dismiss();
                                            if (fragment.getParentActivity() != null) {
                                                new org.telegram.ui.Components.ThemeEditorView()
                                                        .show(fragment.getParentActivity(), copy);
                                            }
                                        });
                                        name.requestFocus();
                                    });
                                    naming.show();
                                });
        shown[0] = dialog.create();
        fragment.showDialog(shown[0]);
    }

    private static boolean nabdhInvalidThemeName(String name) {
        for (int i = 0; i < name.length(); i++) {
            if (Character.isISOControl(name.charAt(i))) return true;
        }
        return false;
    }

    private static android.graphics.Bitmap nabdhBundledWallpaper(
            android.content.Context context, Theme.ThemeInfo theme) {
        if (theme.assetName == null || !theme.assetName.startsWith("nabdh_")) {
            return null;
        }
        // Bundled files are verified during the overlay step (max 5 MiB).
        // Keep the same limit here to protect memory on lower-end phones.
        try (java.io.InputStream input = context.getAssets().open(theme.assetName);
             java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream()) {
            byte[] chunk = new byte[8192];
            int count, total = 0;
            while ((count = input.read(chunk)) != -1) {
                total += count;
                if (total > 5 * 1024 * 1024) return null;
                output.write(chunk, 0, count);
            }
            byte[] data = output.toByteArray();
            for (int i = 0; i + 7 < data.length; i++) {
                if (data[i] == 'W' && data[i + 1] == 'P'
                        && data[i + 2] == 'S' && data[i + 3] == 10
                        && (data[i + 4] & 255) == 255
                        && (data[i + 5] & 255) == 216) {
                    int start = i + 4, length = data.length - start;
                    android.graphics.BitmapFactory.Options options =
                            new android.graphics.BitmapFactory.Options();
                    options.inJustDecodeBounds = true;
                    android.graphics.BitmapFactory.decodeByteArray(data, start,
                            length, options);
                    if (options.outWidth <= 0 || options.outHeight <= 0) return null;
                    options.inJustDecodeBounds = false;
                    options.inSampleSize = 1;
                    while (options.outWidth / options.inSampleSize > 960
                            || options.outHeight / options.inSampleSize > 1280) {
                        options.inSampleSize *= 2;
                    }
                    return android.graphics.BitmapFactory.decodeByteArray(data,
                            start, length, options);
                }
            }
        } catch (Exception ignored) {
            // A malformed or absent embedded wallpaper must not break selection.
        }
        return null;
    }

    private static int nabdhThemePreviewInk(int color) {
        final int luminance = (Color.red(color) * 299
                + Color.green(color) * 587 + Color.blue(color) * 114);
        return luminance > 150000 ? 0xFF26343C : 0xFFF6FAFA;
    }

    public void selectTheme(Theme.ThemeInfo themeInfo) {
        selectTheme(themeInfo, null);
    }""",
    "bundled four-theme preview with deliberate apply and previous-theme restore")

cell.write_text(cell_src, encoding="utf-8")
print("PASS: NabdhGram theme cards show mini chats and readable two-line labels")
