#!/usr/bin/env python3
"""Fast no-Gradle smoke checks for NabdhGram Glass source overlays."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: check-glass-overlay.py TELEGRAM_SOURCE")

root = Path(sys.argv[1])
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
dialogs = (ui / "DialogsActivity.java").read_text(encoding="utf-8")
cell = (ui / "Cells/DialogCell.java").read_text(encoding="utf-8")
settings = (ui / "NabdhGramSettingsActivity.java").read_text(encoding="utf-8")
selector = (ui / "Components/RecyclerListView.java").read_text(encoding="utf-8")
typefaces = (root / "TMessagesProj/src/main/java/org/telegram/messenger/AndroidUtilities.java").read_text(encoding="utf-8")
composer = (ui / "Components/ChatActivityEnterView.java").read_text(encoding="utf-8")
contacts = (ui / "ContactsActivity.java").read_text(encoding="utf-8")
native_settings = (ui / "SettingsActivity.java").read_text(encoding="utf-8")
profile = (ui / "ProfileActivity.java").read_text(encoding="utf-8")
shared_config = (root / "TMessagesProj/src/main/java/org/telegram/messenger/SharedConfig.java").read_text(encoding="utf-8")
universal = (ui / "Components/UniversalAdapter.java").read_text(encoding="utf-8")
launch = (ui / "LaunchActivity.java").read_text(encoding="utf-8")
document_cell = (ui / "Cells/ChatMessageCell.java").read_text(encoding="utf-8")
font_assets = root / "TMessagesProj/src/main/assets/fonts"
font_files = ("ReadexPro.ttf", "Vazirmatn.ttf", "NotoSansArabic.ttf", "Tajawal.ttf", "Rubik.ttf")
localized = (ui / "NabdhStrings.java").read_text(encoding="utf-8")
feature = (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
appearance_en = (root / "TMessagesProj/src/main/res/values/nabdhgram_settings.xml").read_text(encoding="utf-8")
appearance_ar = (root / "TMessagesProj/src/main/res/values-ar/nabdhgram_settings.xml").read_text(encoding="utf-8")
# The launcher label and MTProto session name are two different paths.
connections = (root / "TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java").read_text(encoding="utf-8")
checks = {
    "blurred chat wallpaper rendered inside actual message shape":
        "nabdhDrawFrostedWallpaper(canvas, makePath())" in
            (ui / "ActionBar/MessageDrawable.java").read_text(encoding="utf-8")
        and "nabdhDrawFrostedWallpaper(canvas, path)" in
            (ui / "ActionBar/MessageDrawable.java").read_text(encoding="utf-8"),
    "Devices sessions report the NabdhGram application name":
        'appVersion = "NabdhGram " + nabdhVersionName' in connections
        and 'appVersion += " pbeta";' in connections,
    "Glass cards suppress native separator strokes without touching other pages":
        all("if (needDivider && !org.telegram.ui.Components.NabdhGlassRowDecoration.isGlassCard(this))" in
            (ui / "Cells" / (name + ".java")).read_text(encoding="utf-8")
            for name in ("TextCell", "TextSettingsCell", "TextCheckCell", "TextCheckCell2",
                         "NotificationsCheckCell", "TextDetailCell", "TextRadioCell"))
        and "public static boolean isGlassCard(View child)" in
            (ui / "Components/NabdhGlassRowDecoration.java").read_text(encoding="utf-8"),
    "all settings parent group backgrounds absent, child cards retained":
        all("listView.setSections();" not in (ui / page).read_text(encoding="utf-8")
            for page in ("SettingsActivity.java", "ProfileActivity.java",
                "NotificationsSettingsActivity.java", "PrivacySettingsActivity.java",
                "DataSettingsActivity.java", "ThemeActivity.java",
                "LanguageSelectActivity.java", "SessionsActivity.java",
                "PrivacyControlActivity.java", "NotificationsCustomSettingsActivity.java",
                "CacheControlActivity.java", "ArchiveSettingsActivity.java",
                "DataAutoDownloadActivity.java", "PasscodeActivity.java",
                "PrivacyUsersActivity.java", "ProxyListActivity.java",
                "QuickRepliesSettingsActivity.java",
                "RestrictedLanguagesSelectActivity.java",
                "ProfileNotificationsActivity.java"))
        and "NabdhGlassRowDecoration.applyCardStyle(holder.itemView)" in
            (ui / "ProfileActivity.java").read_text(encoding="utf-8")
        and "NabdhGlassRowDecoration.applyCardStyle(holder.itemView, true)" in
            (ui / "Components/UniversalAdapter.java").read_text(encoding="utf-8")
        and "if (!settingsRow && !isSettingRow(child)) return;" in
            (ui / "Components/NabdhGlassRowDecoration.java").read_text(encoding="utf-8")
        and "extends android.graphics.drawable.RippleDrawable" in
            (ui / "Components/NabdhGlassRowDecoration.java").read_text(encoding="utf-8"),
    "native mixed Arabic/Latin alignment uses first strong direction":
        "titleView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG)" in native_settings
        and "subtitleView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG)" in native_settings,
    "native Glass rows include specular highlight":
        "canvas.drawLine(rect.left + round" in
            (ui / "Components/NabdhGlassRowDecoration.java").read_text(encoding="utf-8"),
    "account info uses same Glass for actual SettingCell factory rows":
        "listView.adapter.setNabdhGlassSettings(true)" in
            (ui / "UserInfoActivity.java").read_text(encoding="utf-8")
        and "new org.telegram.ui.Components.NabdhGlassRowDecoration()" in
            (ui / "UserInfoActivity.java").read_text(encoding="utf-8"),
    "native settings and profile use filled theme-aware backgrounds": all(
        "NabdhGlassRowDecoration.applyCardStyle(holder.itemView)" in
        (ui / name).read_text(encoding="utf-8")
        for name in ("NotificationsSettingsActivity.java", "PrivacySettingsActivity.java",
                     "DataSettingsActivity.java", "ThemeActivity.java", "ProfileActivity.java",
                     "LanguageSelectActivity.java", "SessionsActivity.java",
                     "PrivacyControlActivity.java", "NotificationsCustomSettingsActivity.java",
                     "CacheControlActivity.java")
    ) and all(
        phrase in (ui / "Components/NabdhGlassRowDecoration.java").read_text(encoding="utf-8")
        for phrase in ("class LiveGlassSurface", "class GlassCardLayers",
                       "Theme.getColor(Theme.key_windowBackgroundWhite)",
                       "Theme.getColor(Theme.key_windowBackgroundWhiteBlueText)",
                       "TextDetailCell", "AboutLinkCell")
    ),
    "unified theme-aware legacy settings pages": all(
        "new org.telegram.ui.Components.NabdhGlassRowDecoration()" in
        (ui / name).read_text(encoding="utf-8")
        for name in ("NotificationsSettingsActivity.java",
                     "PrivacySettingsActivity.java", "DataSettingsActivity.java",
                     "ThemeActivity.java", "ProfileActivity.java", "LanguageSelectActivity.java",
                     "SessionsActivity.java", "PrivacyControlActivity.java",
                     "NotificationsCustomSettingsActivity.java", "CacheControlActivity.java")
    ) and all(token in
        (ui / "Components/NabdhGlassRowDecoration.java").read_text(encoding="utf-8")
        for token in ("onDrawOver", "Theme.key_windowBackgroundWhiteBlueText",
                      "isSettingRow", "Paint.Style.STROKE")),
    "native Telegram text labels eligible for font remeasure": all(
        token in launch for token in
        ("final boolean telegramTextFace", "telegramTextFace ? android.graphics.Typeface.DEFAULT",
         "originalPx * uiPercent / 100f")
    ),
    "third-party login cannot advertise official-only Firebase SMS":
        'settings.allow_firebase = false; // Third-party app' in
        (ui / "LoginActivity.java").read_text(encoding="utf-8"),
    "login keypad circular keys, visible press and tinted delete icon":
        all(part in (ui / "Components/CustomPhoneKeyboardView.java").read_text(encoding="utf-8")
            for part in ("class NabdhCircleKey", "canvas.drawCircle(",
                         "Math.min(box.width(), box.height())", "state_pressed",
                         "54 + android.graphics.Color.red(accent) * 46",
                         "R.drawable.nabdh_keypad_delete",
                         "backButton.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));")),
    "Telegram empty-chat egg replaced by approved NabdhGram logo":
        (root / "TMessagesProj/src/main/res/drawable-nodpi/nabdh_empty_logo.png").is_file()
        and all(t in (ui / "Cells/DialogsEmptyCell.java").read_text(encoding="utf-8")
            for t in ("R.drawable.nabdh_empty_logo", "ImageView.ScaleType.FIT_CENTER",
                      "currentType == TYPE_WELCOME_WITH_CONTACTS")),
    "verification boxes are rounded without touching validation":
        "nabdhLoginGlass" in (ui / "CodeFieldContainer.java").read_text(encoding="utf-8")
        and "setNabdhLoginGlass(true);" in (ui / "LoginActivity.java").read_text(encoding="utf-8"),
    "auth verification route diagnostics contain no personal identifiers":
        'FileLog.d("NabdhGram auth delivery type="' in
        (ui / "LoginActivity.java").read_text(encoding="utf-8")
        and 'FileLog.d("NabdhGram auth sendCode: "' in
        (ui / "LoginActivity.java").read_text(encoding="utf-8"),
    "login logo lifted while preserving native input geometry":
        "nabdhLoginLogo.setTranslationY(-dp(14));" in
        (ui / "LoginActivity.java").read_text(encoding="utf-8"),
    "RTL verified contact icon follows name instead of overlapping":
        "setNabdhRtlBadgeBeforeText(LocaleController.isRTL)" in
        (ui / "Cells/UserCell.java").read_text(encoding="utf-8")
        and "float visibleTextStart = offsetX" in
        (ui / "ActionBar/SimpleTextView.java").read_text(encoding="utf-8")
        and "textOffsetX += drawablePadding + leftDrawable.getIntrinsicWidth();" in
        (ui / "ActionBar/SimpleTextView.java").read_text(encoding="utf-8")
        and "(nabdhRtlBadgeBeforeText" in
        (ui / "ActionBar/SimpleTextView.java").read_text(encoding="utf-8"),
    "actual Telegram Settings rows have theme-based rounded Glass":
        "listView.adapter.setNabdhGlassSettings(true)" in native_settings
        and "NabdhGlassRowDecoration.applyCardStyle(holder.itemView, true)" in universal
        and "view instanceof org.telegram.ui.SettingsActivity.SettingCell" in
            (ui / "Components/NabdhGlassRowDecoration.java").read_text(encoding="utf-8"),
    "country and phone inputs keep native validation plus soft Glass":
        "setNabdhSoftGlass(true)" in (ui / "LoginActivity.java").read_text(encoding="utf-8")
        and "canvas.drawRoundRect(" in
        (ui / "Components/OutlineTextContainerView.java").read_text(encoding="utf-8"),
    "solid native chat bubbles draw tinted Glass overlay":
        "canvas.drawPath(makePath(), nabdhBubbleEdge)" in
        (ui / "ActionBar/MessageDrawable.java").read_text(encoding="utf-8"),
    "finished NabdhGram settings use one accessible column":
        'section(context, content, R.string.NabdhShieldTitle' in settings
        and "compactGrid" not in settings
        and 'card.setOnClickListener(v -> presentFragment(' in settings
        and 'description.setMaxLines(2);' in settings,
    "contacts card uses dedicated native rounded row backgrounds":
        "InsetDrawable(" in (ui / "Adapters/ContactsAdapter.java").read_text(encoding="utf-8")
        and "glass.setCornerRadius(AndroidUtilities.dp(15))" in
            (ui / "Adapters/ContactsAdapter.java").read_text(encoding="utf-8"),
    "profile channel media and heading get separate readable space":
        "Math.max(122," in (ui / "Cells/ProfileChannelCell.java").read_text(encoding="utf-8")
        and "headerLayout.setLayoutDirection(LocaleController.isRTL" in
            (ui / "Cells/ProfileChannelCell.java").read_text(encoding="utf-8"),
    "contact names honor regular font and keep verified badges distinct":
        'nameTextView.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));' in
        (ui / "Cells/UserCell.java").read_text(encoding="utf-8")
        and 'nameTextView.setDrawablePadding(dp(8));' in
        (ui / "Cells/UserCell.java").read_text(encoding="utf-8"),
    "MTProxy promotion may be re-hidden after server reconnect":
        "nabdhLastProxyPromoAttemptAt" in dialogs
        and ">= 15000L" in dialogs
        and "nabdhLastProxyPromoId" not in dialogs
        and "viewPages[0].updateList(true);" in dialogs,
    "compact Glass card text and height":
        "card.setMinimumHeight((int) (78 * density + .5f))" in settings
        and "descLp.topMargin = (int) (3 * density + .5f);" in settings,
    "device default font and regular custom typefaces": all(
        part in typefaces for part in (
            'getString("font_family", "system-default")',
            'boolean bold = userBold;',
            '"system-default".equals(family)',
        )
    ) and "NabdhFontSystemDefault" in appearance_ar
      and "NabdhFontSystemDefault" in appearance_en
      and "nabdhOriginalTypefaces" in launch,
    "login mark doubled and diagnostic toggle hidden in production":
        "LayoutHelper.createLinear(152, 152," in
        (ui / "LoginActivity.java").read_text(encoding="utf-8")
        and "&& getConnectionsManager().isTestBackend()) {" in
        (ui / "LoginActivity.java").read_text(encoding="utf-8"),
    "bundled theme darkness initialized safely": all(
        phrase in (ui / "ActionBar/Theme.java").read_text(encoding="utf-8")
        for phrase in (
            "themeInfo.isDark = ThemeInfo.DARK;",
            "themeInfo.isDark = ThemeInfo.LIGHT;",
            "checkIsDark(getThemeFileValues(null, assetName, wallpaperLink), this);",
            "else if (pathToFile != null)",
            "isDark = previewBackgroundColor != 0",
        )
    ),
    "canvas-based chat text adopts selected font": all(
        phrase in (ui / "ActionBar/Theme.java").read_text(encoding="utf-8")
        for phrase in (
            'chat_msgTextPaint.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));',
            'chat_replyTextPaint.setTypeface(AndroidUtilities.getTypeface("fonts/rregular.ttf"));',
        )
    ),
    "verified badges reserve Arabic name glyph inset":
        "nameWidth -= dp(27);" in cell and "nameLeft += dp(27);" in cell,
    "Arabic resources survive upstream Gradle locale filter":
        'localeFilters += ["zz", "ar"]' in
        (root / "TMessagesProj_App/build.gradle").read_text(encoding="utf-8")
        and "<string name=\"NabdhGramSettingsTitle\">إعدادات نبض جرام</string>" in appearance_ar,
    "NabdhGram settings spacing compacted": all(
        token in settings for token in (
            "cardLp.bottomMargin = (int) (8 * density + .5f);",
            "labelsLp.setMarginStart((int) (11 * density + .5f));",
            "int pad = (int) (12 * context.getResources().getDisplayMetrics().density);",
        )
    ),
    "settings and nested page headings localized": all(
        item in settings for item in (
            "actionBar.setTitle(NabdhStrings.get(context, R.string.NabdhGramSettingsTitle));",
            "heading.setText(NabdhStrings.get(context, titleRes));",
            "description.setText(NabdhStrings.get(context, summaryRes));",
        )
    ) and "actionBar.setTitle(NabdhStrings.get(context, titleRes));" in feature
      and "explanation.setText(NabdhStrings.get(context, descriptionRes));" in feature,
    "appearance settings describe working Glass and fonts": "Choose the application font below." in appearance_en
        and "اختر خط التطبيق أدناه." in appearance_ar
        and "Glass appearance and application fonts" in appearance_en
        and "مظهر Glass وخطوط التطبيق" in appearance_ar
        and "Planned: Glass themes, fonts and personalization. Not enabled yet." not in appearance_en
        and "قيد التطوير: ثيمات Glass والخطوط وخيارات التخصيص. لم تُفعّل بعد." not in appearance_ar,
    "custom labels follow Telegram locale": "getCurrentLocale()" in localized
        and "createConfigurationContext(config)" in localized
        and "NabdhStrings.get(context," in settings
        and "NabdhStrings.get(context," in feature,
    "chat section headings localized": "NabdhStrings.get(context, section == 1" in dialogs,
    "appearance RTL layout": "content.setLayoutDirection(" in feature
        and "LocaleController.isRTL" in feature,
    "composer native RTL hint renderer enabled": "messageEditText.setSupportRtlHint(true)" in composer,
    "appearance font options in Glass surface": "fontCard.setBackground(fontGlass)" in feature
        and "fontCard.addView(choices);" in feature,
    "all selected fonts bundled": all((font_assets / name).is_file() and (font_assets / name).stat().st_size > 10000 for name in font_files),
    "font options mapped to native renderer": all(name in launch for name in font_files),
    "font options mapped to Telegram typefaces": all(name in typefaces for name in font_files),
    "native font choice restored on resume": "nabdhApplyVisibleFonts();" in launch and 'getString("font_family", "system-default")' in launch,
    "native font scan skips editors": "!(view instanceof android.widget.EditText)" in launch,
    "native font scan only when layout dirty": "nabdhFontLayoutListener = () -> nabdhFontDirty = true;" in launch,
    "font size and weight persisted with scope": all(
        key in launch for key in ("ui_scale_percent", "font_bold", "nabdhOriginalTextSizes")
    ) and 'getBoolean("font_bold", false)' in typefaces
        and '"fons_size"' in (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8"),
    "settings selected locale respected": "getCurrentLocale()" in settings
        and "getCurrentLocale()" in (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8"),
    "profile buttons show pressed surface": "nabdhPressPaint" in
        (ui / "Components/ProfileActionsView.java").read_text(encoding="utf-8"),
    "document title and metadata do not share fixed spacing": 
        "subtitleY = titleY + Math.max(dp(23), docTitleLayout.getHeight() + dp(7));" in document_cell
        and "photoHeight = Math.max(photoHeight, docTitleLayout.getHeight() + dp(32));" in document_cell,
    "archive gets its own rounded card": "final boolean archived = isFolderCell();" in cell,
    "archive folder remains outside pinned group": all(
        token in dialogs for token in (
            "if (dialog.isFolder) continue;",
            "if (position == firstPinned) return 1;", 
            "!((TLRPC.Dialog) item).isFolder", 
        )
    ),
    "archive/pinned separation retains original adapter indices":
        "viewPage.listView.addItemDecoration(new RecyclerView.ItemDecoration()" in dialogs,

    "unread badges centered for every count animation": all(
        f"nabdhBadgeTextOffset({layout})" in cell
        for layout in ("countLayout", "countOldLayout", "countAnimationStableLayout", "countAnimationInLayout")
    ),
    "unread badge metrics center": "fm.ascent + fm.descent" in cell,
    "native bubble geometry preserved with theme-aware gradient outline":
        "nabdhBubbleEdge" in (ui / "ActionBar/MessageDrawable.java").read_text(encoding="utf-8")
        and "key_chat_outBubbleShadow" in (ui / "ActionBar/MessageDrawable.java").read_text(encoding="utf-8")
        and "canvas.drawPath(path, nabdhBubbleEdge)" in (ui / "ActionBar/MessageDrawable.java").read_text(encoding="utf-8"),
    "settings headers safe inset": "new HeaderCell(context, 32, resourcesProvider)" in universal
        and "Theme.key_windowBackgroundWhiteBlackText, 32, 15" in universal,
    "font applied before drawing": "addOnPreDrawListener(nabdhFontPreDrawListener)" in launch
        and "if (nabdhFontDirty && android.os.SystemClock.uptimeMillis()" in launch
        and "nabdhLastFontScanMs >= 48L" in launch,
    "composer retains native padding and RTL": "messageEditText.setPadding(0, dp(9), 0, dp(10));" in composer
        and "TEXT_DIRECTION_FIRST_STRONG" in composer
        and "LocaleController.isRTL" in composer
        and "android.view.Gravity.RIGHT : android.view.Gravity.LEFT" in composer,
    "rounded bubble default with saved preference": 'public static int bubbleRadius = 19;' in shared_config
        and 'bubbleRadius = preferences.getInt("bubbleRadius", 19);' in shared_config,
    "native settings rounded touch selector": "listView.setSelectorRadius(17);" in native_settings,
    "profile rounded touch selector": "listView.setSelectorRadius(17);" in profile,
    "contacts rounded selector": "listView.setSelectorRadius(17);" in contacts,
    "verified contact names reserve icon gap":
        "nameTextView.setDrawablePadding(dp(8))" in
        (ui / "Cells/UserCell.java").read_text(encoding="utf-8")
        and "setNabdhRtlBadgeBeforeText(LocaleController.isRTL)" in
        (ui / "Cells/UserCell.java").read_text(encoding="utf-8"),
    "approved NabdhGram artwork on phone login":
        "R.drawable.nabdhgram_welcome_logo" in
        (ui / "LoginActivity.java").read_text(encoding="utf-8"),
    "MTProxy promo uses native hide API (not PSA)":
        all(token in dialogs for token in (
            "controller.promoDialogType != MessagesController.PROMO_TYPE_PROXY",
            "controller.hidePromoDialog();",
            "nabdhHideProxySponsorIfPresent();",
        ))
        and "i < visible.size()" in
        (ui / "DialogsActivity.java").read_text(encoding="utf-8"),
    "same-fragment font refresh available":
        "public void nabdhRefreshAllFonts()" in launch
        and "nabdhRefreshAllFonts();" in feature,
    "Glass settings colors follow active theme":
        "Theme.key_windowBackgroundWhiteBlueText" in feature
        and "Theme.key_windowBackgroundGray" in feature,

    "chat composer rounded theme surface": "messageEditText.setBackground(nabdhInputGlass)" in composer
        and "nabdhInputGlass.setCornerRadius(dp(19))" in composer
        and "Theme.key_chat_messagePanelBackground" in composer,
    "dialog selector rounded clipping installed": "selectorView instanceof org.telegram.ui.Cells.DialogCell" in selector
        and "canvas.clipPath(nabdhDialogSelectorPath)" in selector
        and "selectorRect.left + 7f * density" in selector
        and "selectorRect.bottom - 3f * density" in selector,
    "selector canvas state restored": "if (nabdhDialog) {" in selector and "canvas.restore();" in selector,
    "all section labels honor normal-weight selected typography":
        'labelPaint.setTypeface(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rregular.ttf"))' in dialogs,
    "custom bold font avoids stale mediumTypeface": 'if (!"system-default".equals(selectedFamily))' in typefaces
        and "getTypeface(TYPEFACE_ROBOTO_MEDIUM)" in typefaces,
    "composer refreshes text and hint typography": "nabdhRefreshComposerFont();" in composer
        and "messageEditText.setTypeface(chosen, bold" in composer
        and 'getString("font_family", "system-default")' in composer,
    "font preference consumed by Telegram typeface resolver": 'getString("font_family", "system-default")' in typefaces
        and '"ReadexPro.ttf"' in typefaces
        and '"sans-serif".equals(family)' in typefaces
        and '"serif".equals(family)' in typefaces,
    "appearance font preference persisted": 'getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)' in (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8")
        and 'putString("font_family", family).commit()' in (ui / "NabdhGramFeatureCategoryActivity.java").read_text(encoding="utf-8"),
    "settings card native ripple": "new android.graphics.drawable.RippleDrawable(" in settings
        and "card.setBackground(new android.graphics.drawable.RippleDrawable(" in settings,
    "pinned decoration never draws a box across mixed chat rows":
        "hasFirstPinnedRow" not in dialogs and "pinnedGroupPaint" not in dialogs,
    "profile channel preview keeps its own layout": "getParent() instanceof ProfileChannelCell" in cell,
    "mixed-language dialog name alignment preserves native avatar bounds":
        "nabdhNameAlignment" not in cell
        and "nameLayout = new StaticLayout(nameStringFinal" in cell
        and "Layout.Alignment.ALIGN_NORMAL" in cell
        and "if (left == 0)" in cell
        and "nameWidth -= dp(27);" in cell,
    "dialog card paint created once": cell.count("private final android.graphics.Paint nabdhCardPaint") == 1,
    "dialog card canvas drawing present": cell.count("canvas.drawRoundRect(nabdhCardBounds") == 2,
    "dialog card excludes swipe/archive without hiding all rows": "!drawArchive" not in cell
        and "currentRevealProgress == 0.0f" in cell
        and "translationX == 0" in cell
        and "isFolderCell()" in cell,
    "dialog selection feedback": "isPressed() || isSelected || isSelected()" in cell,
    "section headers drawn only at unique boundaries": all(
        part in dialogs for part in (
            "if (position == firstPinned) return 1;",
            "if (position == firstOther) return 2;",
            "if (section != 0) outRect.top = dp(25);",
        )
    ),
    "decoration section headings": "NabdhGlassPinnedChats" in dialogs and "NabdhGlassOtherChats" in dialogs,
    "no oversized pinned-group overlay":
        "pinnedGroupPaint" not in dialogs and "onDrawOver(Canvas" not in dialogs,
    "archive row excluded without extra section":
        "if (dialog.isFolder) continue;" in dialogs
        and "((TLRPC.Dialog) row).isFolder) return 0;" in dialogs,
    "decoration not adapter mutation": "new RecyclerView.ItemDecoration()" in dialogs
        and "itemInternals.add(regularFirst" not in dialogs,
    "main chats only": "viewPage.dialogsType == DIALOGS_TYPE_DEFAULT && folderId == 0 && communityId == 0" in dialogs,
}

for lang in ("values", "values-ar"):
    xml = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    strings = ET.parse(xml).getroot()
    # Android AAPT2 requires apostrophes in string resources to be escaped.
    for entry in strings.findall("string"):
        if entry.attrib.get("name") == "NabdhFontScope":
            value = entry.text or ""
            if "'" in value.replace(chr(92) + "'", ""):
                raise SystemExit(f"Unescaped Android apostrophe in {lang}/NabdhFontScope")
    for name in ("NabdhGlassPinnedChats", "NabdhGlassOtherChats", "NabdhFontTitle", "NabdhFontSans", "NabdhFontSerif", "NabdhFontScope"):
        found = sum(e.attrib.get("name") == name for e in strings.findall("string"))
        print(f"Resource count {lang}/{name}: {found}", flush=True)
        if found != 1:
            print("Nearby resource names: " + repr([e.attrib.get("name") for e in strings.findall("string") if "Glass" in e.attrib.get("name", "")]), flush=True)
        checks[f"{lang}: {name} unique"] = found == 1

for name, okay in checks.items():
    print(("PASS" if okay else "FAIL") + " " + name)
if not all(checks.values()):
    raise SystemExit("NabdhGram Glass source smoke checks failed")
print("NabdhGram Glass source smoke checks passed.")
