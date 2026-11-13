#!/usr/bin/env python3
"""Verify cross-screen Glass design contracts before an expensive Android build."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/nabdhgram-identity-build.yml").read_text(encoding="utf-8")
bubble = (ROOT / "scripts/apply-glass-bubble-outline.py").read_text(encoding="utf-8")
profile = (ROOT / "scripts/apply-glass-native-settings-profile.py").read_text(encoding="utf-8")
finishing = (ROOT / "scripts/apply-glass-v1-finishing.py").read_text(encoding="utf-8")
settings = (ROOT / "scripts/apply-glass-settings.py").read_text(encoding="utf-8")
login_overlay = (ROOT / "scripts/apply-glass-login-finish.py").read_text(encoding="utf-8")
login_layout = (ROOT / "scripts/apply-glass-login.py").read_text(encoding="utf-8")
finishing_ui = finishing

ordered = [
    "apply-glass-global-font.py",
    "apply-glass-chat-typefaces.py",
    "apply-glass-global-textviews.py",
    "apply-glass-settings.py",
    "apply-glass-bubble-radius.py",
    "apply-glass-bubble-outline.py",
    "apply-glass-final-screens.py",
    "apply-glass-v1-finishing.py",
    "apply-glass-settings-surfaces.py",
    "apply-nabdh-empty-state.py",
    "check-glass-overlay.py",
]
positions = [workflow.find("python3 nabdhgram/scripts/" + name) for name in ordered]
assert all(pos >= 0 for pos in positions), "Missing Glass integration step"
assert positions == sorted(positions), "Glass overlays applied out of order"
identity_overlay = (ROOT / "scripts/apply-identity.py").read_text(encoding="utf-8")
assert 'appVersion = nabdhVersionName + " (" + pInfo.versionCode + ")";' in identity_overlay
assert "Cells/SessionCell.java" in identity_overlay and '"NandhGram".equalsIgnoreCase(nabdhDisplayApp)' in identity_overlay, "SessionCell must correct only this client app_name"
assert "SessionBottomSheet.java" in identity_overlay and "nabdhDisplayVersion.startsWith" in identity_overlay, "Session detail must normalize historic versions"
assert "while (nabdhVersionName.startsWith(" in identity_overlay, "Repeated NandhGram / NabdhGram prefixes must be stripped"
assert workflow.index("      - name: Verify NabdhGram Glass overlays before Gradle") < workflow.index("      - name: Install Android SDK and NDK") < workflow.index("      - name: Build branded debug APK"), "Expensive SDK/NDK setup must run only after source overlays pass"
assert bubble.count("(currentType == TYPE_TEXT || currentType == TYPE_MEDIA)") == 2, "Text/media design is inconsistent"
assert "!themePreview && !isSelected" in bubble, "Selection or preview protection was removed"
assert finishing.count("if ((currentType == TYPE_TEXT || currentType == TYPE_MEDIA) && !themePreview && !isSelected)") == 2, "Final overlay no longer matches text/media anchor"
assert "0x330098A3" not in profile, "Hard-coded profile press color returned"
assert "Theme.key_windowBackgroundWhiteBlueText" in profile, "Theme-aware profile tint missing"
for family in ("Readex Pro", "Vazirmatn", "Noto Sans Arabic", "Tajawal", "Rubik", "Sans-serif", "Serif"):
    assert family in settings, f"Missing English font label: {family}"
assert '"values-ar": ("خط التطبيق", "Readex Pro", "Sans-serif", "Serif"' in settings, "Arabic locale changes font names"
assert "+ 'Device default font'" in settings, "Default font label changes with locale"
assert (chr(92) * 2 + "n            settings.allow_firebase") not in login_overlay, "Double-escaped Java newline in auth overlay"
assert "if (nabdhGlassSettings) {" in finishing_ui and "updateColors(holder);" in finishing_ui, "Settings rows must refresh Glass after native bind"
assert "float visibleTextStart = offsetX" in finishing_ui, "RTL badge not anchored to glyph start"
assert "textOffsetX += drawablePadding + leftDrawable.getIntrinsicWidth();" in finishing_ui, "RTL badge drawable width not reserved in text translation"
assert "(nabdhRtlBadgeBeforeText" in finishing_ui, "RTL badge position is not restricted to verified names"
assert "offsetX = Math.round(width + rightStatusSpace - layout.getLineRight(0));" in finishing_ui, "RTL mixed-script status glyph edge not aligned"
assert "Premium stars/emoji statuses are rightDrawable in Telegram" in finishing_ui and "- dw - drawablePadding - dp(3)" in finishing_ui, "Premium star still overlaps Arabic contact names"
assert "R.drawable.nabdh_keypad_delete" in login_overlay and "nabdh_keypad_delete.xml" in login_overlay, "Native delete vector not bundled"
assert "SIDE_PADDING = 10, BUTTON_PADDING = 6" in login_overlay, "Original keypad geometry not restored"
assert "class NabdhCircleKey" in login_overlay and "canvas.drawCircle(" in login_overlay, "Circular keypad renderer is missing"
assert "key_text_before" in login_overlay and "key_text_after" in login_overlay, "Circular keys must center native keypad labels"
assert "SIDE_PADDING = 4, BUTTON_PADDING = 3" in login_overlay, "Keypad touch-cell geometry has not been enlarged"
assert "Gravity.TOP | Gravity.CENTER_HORIZONTAL" in (ROOT / "scripts/apply-glass-login.py").read_text(encoding="utf-8"), "Login still vertically centers ghost logo height"
assert "LayoutHelper.createLinear(136, 84," in (ROOT / "scripts/apply-glass-login.py").read_text(encoding="utf-8"), "Login logo still reserves a tall blank box"
assert "int bottomMargin = activityMode == MODE_LOGIN ? 12 : 72;" in login_layout, "Login form still reserves oversized fixed blank area"
assert "getGravity() != desired" in login_layout and "getChildCount()" in login_layout, "Login form must center measured content adaptively"
assert "MeasureSpec.getSize(widthMeasureSpec)" in login_overlay and "MeasureSpec.getSize(heightMeasureSpec)" in login_overlay, "Keypad still measures its keys from stale view bounds"
assert "keyRadius * .18f" in login_overlay and "keyRadius * .48f" in login_overlay, "Key labels must track actual circle size"
assert "numberTextPaint.setTextAlign(Paint.Align.CENTER)" in login_overlay, "Number labels are not centered"
assert "symbolsTextPaint.setTextAlign(Paint.Align.CENTER)" in login_overlay, "Letter labels are not centered"
assert "getWidth() * 0.25f - numberWidth / 2f" in login_overlay, "Original upstream text-layout anchor changed; update keypad patch"

assert "Math.min(box.width(), box.height()) * .5f - dp(1)" in login_overlay, "Key circles were not enlarged"
assert "Gravity.LEFT | Gravity.TOP, 16, 16, 0, 16" in login_overlay and "Gravity.LEFT | Gravity.TOP, 68, 16, 0, 16" in login_overlay, "Language/proxy actions are not left-aligned"
assert "state_pressed" in login_overlay and "46) / 100" in login_overlay, "Pressed keys are not visibly tinted"
assert 'backButton.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));' in login_overlay, "Delete glyph is not theme accent"
empty_script = (ROOT / "scripts/apply-nabdh-empty-state.py").read_text(encoding="utf-8")
assert "branding/approved/nabdhgram-welcome-transparent.png" in empty_script and "R.drawable.nabdh_empty_logo" in empty_script, "Approved empty-chat branding is missing"
assert "Theme.key_windowBackgroundWhite" in login_overlay, "Keypad surface must follow theme"
native_surfaces = (ROOT / "scripts/apply-glass-settings-surfaces.py").read_text(encoding="utf-8")
assert all(name in native_surfaces for name in ("NotificationsSettingsActivity.java",
    "PrivacySettingsActivity.java", "DataSettingsActivity.java",
    "ThemeActivity.java", "ProfileActivity.java", "LanguageSelectActivity.java",
    "SessionsActivity.java", "PrivacyControlActivity.java",
    "NotificationsCustomSettingsActivity.java", "CacheControlActivity.java")), "Missing native settings target"
assert "getColor(Theme.key_windowBackgroundWhiteBlueText)" in native_surfaces, "Theme-independent settings border"
assert "onDrawOver" in native_surfaces and "isSettingRow" in native_surfaces, "Settings decoration must exclude non-row views"
assert "newCardBackground()" in native_surfaces and "makeRippleMask()" in native_surfaces, "Theme-aware card background and clipped ripple must be shared"
for obsolete in ("GradientDrawable glassCard =", "GradientDrawable infoCard =", "GradientDrawable fontGlass =", "RippleDrawable touchSurface ="):
    assert obsolete not in settings, f"Second per-card surface allocation survived: {obsolete}"
assert "scroll.setBackground(new GradientDrawable(" not in settings, "NabdhGram scroll snapshots old theme colors"
assert "topView.setBackground(new android.graphics.drawable.InsetDrawable(" in native_surfaces and "AndroidUtilities.dp(10), 0, AndroidUtilities.dp(10), 0" in native_surfaces, "Main Settings hero needs the same inset as its cards"
remaining = (ROOT / "scripts/apply-glass-remaining-settings.py").read_text(encoding="utf-8")
for screen in ("FiltersSetupActivity.java", "FilterCreateActivity.java", "FilterChatlistActivity.java", "LiteModeSettingsActivity.java", "ThemeActivity.java"):
    assert screen in remaining, f"Missing dedicated folder / lite mode coverage for {screen}"
assert "VIEW_TYPE_FILTER_SUGGESTION" in remaining and "TYPE_BUBBLE_RADIUS" in remaining, "Suggested folders and chat custom widgets remain flat"
assert "insert_at_method_end" in remaining and "holder.itemView, true" in remaining, "Folder and Lite adapters must be decorated AFTER bind"
assert "glassPreviewParams.leftMargin = AndroidUtilities.dp(20)" in remaining and "messagesCell.setClipToOutline(true)" in remaining, "Chat Settings wallpaper preview not inset/clipped at Glass edges"
assert "TYPE_APP_ICON" in remaining, "Launcher icon strip missing Glass backing"
assert "ThemeActivity must retain live Glass on theme change" in remaining and "FLAG_CELLBACKGROUNDCOLOR" in remaining, "Theme callbacks still erase native Glass cards"
assert "TYPE_TEXT_PREFERENCE" in remaining and "TYPE_TEXT_SETTING" in remaining, "Chat Settings missing native text-row Glass"
assert "apply-glass-remaining-settings.py" in workflow, "Final native screens not included in Android build"
icon_variants = (ROOT / "scripts/apply-nabdh-approved-icon-variants.py").read_text(encoding="utf-8")
icon_source = ROOT / "branding/approved/NabdhGram_approved_launcher_variants.webp"
assert icon_source.exists() and icon_source.read_bytes()[:4] == b"RIFF", "Approved six-icon artwork missing"
assert '"NabdhHexIcon"' in icon_variants and '"NabdhOriginalIcon"' in icon_variants, "Six launcher aliases missing"
assert 'apply-nabdh-approved-icon-variants.py Telegram-upstream' in workflow, "Variant artwork not applied to APK"
assert 'check-nabdh-approved-icons.py Telegram-upstream' in workflow, "No APK resource validation for selectable icons"
assert "class LiveGlassSurface" in native_surfaces and "class GlassCardLayers" in native_surfaces, "Missing real theme-aware filled cards"
assert "user_info = ui / \"UserInfoActivity.java\"" in native_surfaces and "listView.adapter.setNabdhGlassSettings(true);" in native_surfaces, "Actual Account info rows missing Glass styling"
assert 'GLASS_SETTINGS_SCREENS = (' in native_surfaces and all(
    ('"' + name + '.java"') in native_surfaces
    for name in ("ArchiveSettingsActivity", "DataAutoDownloadActivity",
                 "PasscodeActivity", "PrivacyUsersActivity", "ProxyListActivity",
                 "RestrictedLanguagesSelectActivity",
                 "ProfileNotificationsActivity")), "Nested settings screens still missing"
assert "titleView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG)" in native_surfaces, "Mixed Arabic/Latin text direction lost"
assert "canvas.drawLine(rect.left + round" in native_surfaces, "Card specular layer missing"
assert "firstNameEdit.setDivider(false);" in native_surfaces and "applyCardStyle(bioEdit, true)" in native_surfaces, "Account name/bio editors remain outside Glass"
assert "applyCardStyle(view, true)" in native_surfaces, "Account add/logout action rows remain flat"
assert "SettingsActivity.SettingCell.updateColors changed" in native_surfaces and "titleView.setTextAlignment(View.TEXT_ALIGNMENT_VIEW_START)" in native_surfaces, "Actual SettingsActivity RTL title alignment missing"
assert "Theme.createChatResources(context, true)" in settings, "Changing chat font size leaves native text paints stale"
assert "applyCardStyle(View child, boolean settingsRow)" in native_surfaces, "UniversalAdapter Settings cells must bypass legacy class-only filter"
assert "NabdhGlassRowDecoration.applyCardStyle(holder.itemView, true)" in native_surfaces, "Main Settings cells must receive actual Glass cards after binding"
assert "glassType == VIEW_TYPE_TEXT_SETTINGS" in native_surfaces and "glassType == VIEW_TYPE_ICON_TEXT_CHECK" in native_surfaces, "Main Settings card eligibility missing"
assert "if (!settingsRow && !isSettingRow(child)) return;" in native_surfaces, "Legacy non-settings views must remain protected"

assert "applyCardStyle(holder.itemView)" in native_surfaces, "Legacy adapters still draw original flat rows"
assert 'for activity in ("SettingsActivity.java",):' in native_surfaces, "Main settings grouped wrapper removal missing"
assert 'source = source.replace(anchor, anchor + """' in native_surfaces, "Nested settings must preserve native sections while hiding only group paint"
assert 'extends android.graphics.drawable.RippleDrawable' in native_surfaces, "Native per-row pressed state/ripple missing"
assert 'new GlassCardLayers(previous)' not in native_surfaces, "Opaque parent row background still retained"
assert "view instanceof org.telegram.ui.Cells.LanguageCell" in native_surfaces, "Language selection row is unstyled"
# Main settings uses a custom UItem factory, not any legacy TextCell.
assert "view instanceof org.telegram.ui.SettingsActivity.SettingCell" in native_surfaces, "Actual SettingsActivity factory rows are excluded from Glass styling"
assert "holder.itemView instanceof org.telegram.ui.SettingsActivity.SettingCell" in native_surfaces, "UniversalAdapter factory rows are excluded from Glass after binding"
assert "nabdhOriginalAlpha * 136 / 255" in bubble, "Cached normal bubbles remain opaque"
assert "nabdhOriginalPaintAlpha * 136 / 255" in bubble, "Canvas-drawn normal bubbles remain opaque"
assert "crossfadeFromDrawable == null" in bubble, "Bubble translucency must preserve transition rendering"
assert "nabdhDrawFrostedWallpaper(canvas, path)" in bubble and "nabdhDrawFrostedWallpaper(canvas, makePath())" in bubble, "Both cached and path text bubbles need blurred wallpaper"
assert "Utilities.stackBlurBitmap(bitmap, 7)" in bubble and "nabdhLastWallpaper" in bubble, "Bubble blur must cache source wallpaper and avoid per-message reblur"
assert 'if (!"system-default".equals(family) || userBold)' in (ROOT / "scripts/apply-glass-global-font.py").read_text(encoding="utf-8"), "Device font resets must preserve native Telegram typography"
assert "boolean nativeHeading = assetPath.equals" in (ROOT / "scripts/apply-glass-global-font.py").read_text(encoding="utf-8"), "Native heading emphasis lost in selected fonts"
assert "!view.hasFocus()" in (ROOT / "scripts/apply-glass-global-textviews.py").read_text(encoding="utf-8"), "Unfocused account EditText fields not updated on font changes"
assert "nabdhAppliedFonts.clear();" in (ROOT / "scripts/apply-glass-global-textviews.py").read_text(encoding="utf-8"), "Font cache not invalidated when Telegram rebinds native rows"
assert "new android.view.ViewTreeObserver.OnPreDrawListener()" in (ROOT / "scripts/apply-glass-global-textviews.py").read_text(encoding="utf-8"), "Typography scan still races RecyclerView rebinding"
assert 'listView.setSections(true);' in (ROOT / "scripts/apply-glass-contacts.py").read_text(encoding="utf-8") and 'nabdhHideSectionBackgroundOnly' in (ROOT / "scripts/apply-glass-contacts.py").read_text(encoding="utf-8"), "Contacts sections must survive"
assert "public void nabdhHideSectionBackgroundOnly()" in native_surfaces, "Glass source must own section helper"
assert "source.replace(anchor, anchor +" in native_surfaces, "Nested pages must preserve setSections()"
assert "listView.setSections();" in native_surfaces and "listView.nabdhHideSectionBackgroundOnly();" in native_surfaces, "Account/main sections must survive"
assert 'replacement = list_anchor + "\\n        listView.nabdhHideSectionBackgroundOnly();"' in (ROOT / "scripts/apply-glass-remaining-settings.py").read_text(encoding="utf-8"), "Folder/Lite Mode sections must survive"
assert "linear.findLastVisibleItemPosition()" in (ROOT / "scripts/apply-glass-global-textviews.py").read_text(encoding="utf-8"), "Font changes must only rebind visible rows"
assert "currentType == TYPE_TEXT" in bubble, "Bubble translucency must be limited to text"
assert "getWidth() * 0.25f" in login_overlay and "final float symbolsBaseline = centerY + keyRadius * .48f" in login_overlay, "Keypad text layout patch or compact glyph placement missing"
assert '"numberTextPaint.setTextSize(dp(22));"' in login_overlay and '"symbolsTextPaint.setTextSize(dp(10));"' in login_overlay, "Phone glyphs no longer fit the circular key"
assert "view instanceof org.telegram.ui.Cells.SessionCell" in native_surfaces, "Session details row is unstyled"
assert 'content = content.replace(' in native_surfaces and "group_anchor" in native_surfaces, "Grouped parent backgrounds still drawn"
assert "view instanceof org.telegram.ui.Cells.TextDetailCell" in native_surfaces, "Profile details aren't styled"
assert "view instanceof org.telegram.ui.Cells.AboutLinkCell" in native_surfaces, "Profile about rows aren't styled"
global_fonts = (ROOT / "scripts/apply-glass-global-textviews.py").read_text(encoding="utf-8")
assert "nabdhContainsArabic(label.getText())" in global_fonts and "nabdhExpectedTextFaces" in global_fonts, "Arabic settings must follow font changes despite native custom faces"
assert "nabdhExpectedAnimatedFaces" in global_fonts, "Animated native labels need rebinding drift detection"
assert "final boolean telegramTextFace" in global_fonts, "Telegram-native typefaces excluded from UI scale"
assert "(telegramTextFace || arabicLabel)" in global_fonts, "Reset may restore saved custom font"
assert "nabdhLastFontScanMs >= 48L" in global_fonts, "Font scan throttle missing"
assert "view instanceof org.telegram.ui.Components.AnimatedTextView" in global_fonts, "Animated native labels excluded from app-wide typography"
assert "animated.setText(animated.getText(), false)" in global_fonts, "AnimatedTextView cached layout not refreshed"
assert "nabdhAnimatedAppliedFonts.put(animated, renderKey)" in global_fonts, "Animated labels may reflow every frame"
bundled_themes = (ROOT / "scripts/apply-nabdh-bundled-themes.py").read_text(encoding="utf-8")
assert "else if (pathToFile != null)" in bundled_themes, "Theme file null guard missing"
assert "isDark = previewBackgroundColor != 0" in bundled_themes, "Native theme fallback missing"
assert "nabdhLanguageButtonView.setImageResource(R.drawable.nabdh_login_language)" in login_overlay, "Login language shortcut missing"
assert "presentFragment(new LanguageSelectActivity())" in login_overlay, "Login must use native language selector"
assert "proxyDrawable.setConnected(false, connected, animated);" in login_overlay, "Existing preauth proxy control still hidden"
assert "loginNetwork.resumeNetworkMaybe();" in login_overlay, "Native MTProto preflight is missing"
assert "nabdhSendCodeStartedMs" in login_overlay and "nabdhSignInStartedMs" in login_overlay, "Privacy-safe auth performance timings missing"
assert "codeFieldContainer.codeField.length * 45L + 180L" in login_overlay, "Correct-code animation delay still long"
print("PASS: Glass pipeline order, shared text/media styling, theme colors, and stable font names")
