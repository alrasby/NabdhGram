#!/usr/bin/env python3
"""Install a theme-aware, non-interactive visual layer for native settings pages.

Draws only thin inset boundaries ABOVE existing cells: no adapter mutations,
layout changes, touch interceptors, altered click targets or static brand colors.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-settings-surfaces.py TELEGRAM_SOURCE")

ui = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"
component = ui / "Components/NabdhGlassRowDecoration.java"
if component.exists():
    raise SystemExit("NabdhGlassRowDecoration already exists: double overlay?")
component.write_text("""package org.telegram.ui.Components;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;

/**
 * Shared decoration for legacy Telegram settings adapters.
 * Uses native theme colors on EVERY draw, including imported themes.
 * Decorative only: does not modify backgrounds, adapters or hit targets.
 */
public final class NabdhGlassRowDecoration extends RecyclerView.ItemDecoration {
    private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF bounds = new RectF();

    private static boolean isSettingRow(View view) {
        // Use instanceof rather than class simple names: Telegram creates
        // anonymous subclasses of TextCell/TextDetailCell in profiles, whose
        // getSimpleName() is empty. Those were previously left unstyled.
        return view instanceof org.telegram.ui.SettingsActivity.SettingCell
                || view instanceof org.telegram.ui.Cells.TextCell
                || view instanceof org.telegram.ui.Cells.TextSettingsCell
                || view instanceof org.telegram.ui.Cells.TextCheckCell
                || view instanceof org.telegram.ui.Cells.TextCheckCell2
                || view instanceof org.telegram.ui.Cells.TextRightIconCell
                || view instanceof org.telegram.ui.Cells.NotificationsCheckCell
                || view instanceof org.telegram.ui.Cells.RadioButtonCell
                || view instanceof org.telegram.ui.Cells.DialogRadioCell
                || view instanceof org.telegram.ui.Cells.TextDetailCell
                || view instanceof org.telegram.ui.Cells.AboutLinkCell
                || view instanceof org.telegram.ui.Cells.UserCell
                || view instanceof org.telegram.ui.Cells.ProfileChannelCell
                || view instanceof org.telegram.ui.Cells.LanguageCell
                || view instanceof org.telegram.ui.Cells.TextRadioCell
                || view instanceof org.telegram.ui.Cells.SessionCell
                || view instanceof org.telegram.ui.Cells.RadioCell
                || view instanceof org.telegram.ui.Cells.TextColorCell
                || view instanceof org.telegram.ui.Cells.CheckBoxCell
                || view instanceof org.telegram.ui.Cells.TextCheckBoxCell;
    }

    public static boolean isGlassCard(View child) {
        return child != null && child.getBackground() instanceof GlassCardLayers;
    }

    // Shared by Telegram lists and by NabdhGram-owned cards/sections.
    // Do not allocate a separate, static GradientDrawable with stale colors.
    public static android.graphics.drawable.Drawable newCardBackground() {
        return new GlassCardLayers();
    }

    public static android.graphics.drawable.Drawable newHeroBackground() {
        // Same radius and theme as rows, but remove the nearly white
        // appearance of the account hero over the opaque Settings root.
        GlassCardLayers hero = new GlassCardLayers();
        hero.setAlpha(190);
        return hero;
    }

    // The removed Telegram section-group fills no longer mask old fragments.
    // Keep the page canvas OPAQUE while each independent Glass card stays tinted.
    // Resolve the active light/dark/imported-theme color on every draw.
    public static android.graphics.drawable.Drawable newOpaquePageBackground() {
        return new android.graphics.drawable.Drawable() {
            private final Paint paint = new Paint();
            @Override public void draw(@NonNull Canvas canvas) {
                int current = Theme.getColor(Theme.key_windowBackgroundGray);
                paint.setColor(Color.rgb(Color.red(current),
                        Color.green(current), Color.blue(current)));
                canvas.drawRect(getBounds(), paint);
            }
            @Override public void setAlpha(int alpha) {
                // Never turn the navigation canvas translucent.
            }
            @Override public void setColorFilter(android.graphics.ColorFilter filter) {}
            @Override public int getOpacity() {
                return android.graphics.PixelFormat.OPAQUE;
            }
        };
    }


    public static android.graphics.drawable.Drawable newProfileScrim() {
        // The copy menu must not share a Drawable callback with the row.
        return new GlassCardLayers();
    }

    // Draw exactly one inset card. Stacking the old ColorDrawable (usually
    // opaque white) underneath an inset card leaves a white rectangular strip
    // around every row, particularly obvious in RTL settings and profiles.
    // A native RippleDrawable preserves pressed feedback and touch behavior.
    public static void applyCardStyle(View child) {
        applyCardStyle(child, false);
    }

    // UniversalAdapter uses several proprietary row subclasses which do not
    // appear in the legacy class whitelist. Only its explicitly opted-in
    // SettingsActivity and approved row types may use this override.
    public static void applyCardStyle(View child, boolean settingsRow) {
        if (!settingsRow && !isSettingRow(child)) return;
        android.graphics.drawable.Drawable existing = child.getBackground();
        if (existing instanceof GlassCardLayers) {
            ((GlassCardLayers) existing).refreshThemeTint();
            return;
        }
        // setBackground can reset padding on Android. Keep Telegram's text
        // geometry, including its RTL insets, unmodified.
        int left = child.getPaddingLeft();
        int top = child.getPaddingTop();
        int right = child.getPaddingRight();
        int bottom = child.getPaddingBottom();
        child.setBackground(new GlassCardLayers());
        child.setPadding(left, top, right, bottom);
    }

    private static final class GlassCardLayers extends android.graphics.drawable.RippleDrawable {
        private int lastTint;
        GlassCardLayers() {
            super(android.content.res.ColorStateList.valueOf(
                    Theme.getColor(Theme.key_listSelector)),
                    new LiveGlassSurface(), makeRippleMask());
            lastTint = Theme.getColor(Theme.key_listSelector);
        }
        private static android.graphics.drawable.Drawable makeRippleMask() {
            android.graphics.drawable.GradientDrawable mask =
                    new android.graphics.drawable.GradientDrawable();
            mask.setColor(Color.WHITE);
            mask.setCornerRadius(AndroidUtilities.dp(20));
            return new android.graphics.drawable.InsetDrawable(mask,
                    AndroidUtilities.dp(10), AndroidUtilities.dp(2),
                    AndroidUtilities.dp(10), AndroidUtilities.dp(2));
        }
        void refreshThemeTint() {
            // Called during RecyclerView decoration. Updating the RippleDrawable
            // unconditionally here would schedule an endless draw/invalidate loop.
            int tint = Theme.getColor(Theme.key_listSelector);
            if (tint != lastTint) {
                lastTint = tint;
                setColor(android.content.res.ColorStateList.valueOf(tint));
                invalidateSelf();
            }
        }
    }

    // Resolve palette in draw(), not at construction: imported and system
    // themes immediately update without a hard-coded turquoise background.
    private static final class LiveGlassSurface extends android.graphics.drawable.Drawable {
        private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint edge = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint sheen = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final RectF rect = new RectF();
        private int opacity = 255;

        @Override public void draw(@NonNull Canvas canvas) {
            android.graphics.Rect bounds = getBounds();
            if (bounds.width() <= 0 || bounds.height() <= AndroidUtilities.dp(28)) return;
            final int base = Theme.getColor(Theme.key_windowBackgroundWhite);
            final int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
            final int red = (Color.red(base) * 82 + Color.red(accent) * 18) / 100;
            final int green = (Color.green(base) * 82 + Color.green(accent) * 18) / 100;
            final int blue = (Color.blue(base) * 82 + Color.blue(accent) * 18) / 100;
            float inset = AndroidUtilities.dp(10);
            float vertical = AndroidUtilities.dp(2);
            float round = AndroidUtilities.dp(20);
            rect.set(bounds.left + inset, bounds.top + vertical,
                    bounds.right - inset, bounds.bottom - vertical);
            if (rect.width() <= 0 || rect.height() <= 0) return;
            fill.setStyle(Paint.Style.FILL);
            // A partially translucent surface lets the active theme canvas
            // show through instead of painting another opaque pale-blue row.
            fill.setColor(Color.argb(218 * opacity / 255, red, green, blue));
            canvas.drawRoundRect(rect, round, round, fill);
            edge.setStyle(Paint.Style.STROKE);
            edge.setStrokeWidth(AndroidUtilities.dpf2(.8f));
            edge.setColor(Color.argb(73 * opacity / 255,
                    Color.red(accent), Color.green(accent), Color.blue(accent)));
            canvas.drawRoundRect(rect, round, round, edge);
            // Specular highlight along the card's top edge differentiates
            // real glass material from an ordinary flat pastel row.
            final boolean dark = Theme.isCurrentThemeDark();
            sheen.setColor(Color.argb((dark ? 49 : 130) * opacity / 255,
                    dark ? 198 : 255, dark ? 225 : 255, dark ? 232 : 255));
            sheen.setStyle(Paint.Style.STROKE);
            sheen.setStrokeWidth(AndroidUtilities.dpf2(.85f));
            canvas.drawLine(rect.left + round, rect.top + AndroidUtilities.dpf2(.7f),
                    rect.right - round, rect.top + AndroidUtilities.dpf2(.7f), sheen);
        }

        @Override public void setAlpha(int alpha) {
            opacity = Math.max(0, Math.min(255, alpha));
            invalidateSelf();
        }

        @Override public void setColorFilter(android.graphics.ColorFilter filter) {
            invalidateSelf();
        }

        @Override public int getOpacity() {
            return android.graphics.PixelFormat.TRANSLUCENT;
        }
    }

    // Draw a fallback behind cells whose native adapters reassign their
    // background after bind. Never mutate child View hierarchy during a
    // RecyclerView drawing/layout pass (setBackground may requestLayout).
    private final LiveGlassSurface fallback = new LiveGlassSurface();

    @Override
    public void onDraw(@NonNull Canvas canvas, @NonNull RecyclerView parent,
            @NonNull RecyclerView.State state) {
        for (int index = 0; index < parent.getChildCount(); index++) {
            final View child = parent.getChildAt(index);
            if (!isSettingRow(child) || isGlassCard(child)
                    || child.getVisibility() != View.VISIBLE) continue;
            fallback.setBounds(child.getLeft(), child.getTop(),
                    child.getRight(), child.getBottom());
            fallback.draw(canvas);
        }
    }

    @Override
    public void onDrawOver(@NonNull Canvas canvas, @NonNull RecyclerView parent,
            @NonNull RecyclerView.State state) {
        for (int index = 0; index < parent.getChildCount(); index++) {
            final View child = parent.getChildAt(index);
            if (child.getVisibility() == View.VISIBLE && isGlassCard(child)) {
                ((GlassCardLayers) child.getBackground()).refreshThemeTint();
            }
        }
    }
}
""", encoding="utf-8")

# One owner for the native section background suppression used by Contacts,
# Settings, Folders and Lite Mode. Preserve section offsets, selector geometry
# and accessibility; only skip Telegram's broad grouped fill callback.
list_path = ui / "Components/RecyclerListView.java"
list_src = list_path.read_text(encoding="utf-8")
section_anchor = "    public void disableSections() {"
if list_src.count(section_anchor) != 1:
    raise SystemExit("RecyclerListView section API changed")
# setSectionsDrawBackground(true) may occur AFTER the Glass helper call:
# do not let Telegram 13.2 re-enable the cached bitmap group fill.
native_draw_mode = "    public void setSectionsDrawBackground(boolean drawBackground) {"
if list_src.count(native_draw_mode) != 1:
    raise SystemExit("RecyclerListView section draw-mode API changed")
list_src = list_src.replace(native_draw_mode, native_draw_mode + """
        if (nabdhSuppressLegacySectionFill) {
            drawBackground = false;
        }""", 1)
section_helper = """    private boolean nabdhSuppressLegacySectionFill;

    public void nabdhHideSectionBackgroundOnly() {
        // Telegram 13.2.x can paint group fills using bitmap decoration,
        // independent of the legacy drawSectionBackground callback.
        // Disable BOTH fill paths without removing section row geometry.
        nabdhSuppressLegacySectionFill = true;
        drawSectionBackground = null;
        bitmapSectionsDrawBackground = false;
        if (bitmapSectionsItemDecoration != null) {
            bitmapSectionsItemDecoration.setDrawBackground(false);
        }
        invalidate();
    }

"""
list_path.write_text(list_src.replace(section_anchor,
        section_helper + section_anchor, 1), encoding="utf-8")

# Telegram cells still draw flat native divider lines ON TOP of the inset
# rounded card. Hide only those separators when this exact Glass background is
# installed; retain separators unchanged in all other application screens.
for cell_name in ("TextCell", "TextSettingsCell", "TextCheckCell", "TextCheckCell2",
                  "NotificationsCheckCell", "TextDetailCell", "TextRadioCell"):
    cell_path = ui / "Cells" / (cell_name + ".java")
    cell_src = cell_path.read_text(encoding="utf-8")
    before_divider = "        if (needDivider) {"
    if cell_src.count(before_divider) != 1:
        raise SystemExit(f"{cell_name}: divider draw anchor changed")
    cell_src = cell_src.replace(before_divider,
        "        if (needDivider && !org.telegram.ui.Components.NabdhGlassRowDecoration.isGlassCard(this)) {",
        1)
    cell_path.write_text(cell_src, encoding="utf-8")

# Covers real nested Settings pages using the same upstream list model;
# complex charts/editors are intentionally excluded from decorative hooks.
GLASS_SETTINGS_SCREENS = (
    "NotificationsSettingsActivity.java", "PrivacySettingsActivity.java",
    "DataSettingsActivity.java", "ThemeActivity.java",
    "ProfileActivity.java", "LanguageSelectActivity.java",
    "SessionsActivity.java", "PrivacyControlActivity.java",
    "NotificationsCustomSettingsActivity.java", "CacheControlActivity.java",
    "ArchiveSettingsActivity.java", "DataAutoDownloadActivity.java",
    "PasscodeActivity.java", "PrivacyUsersActivity.java",
    "ProxyListActivity.java",
    "RestrictedLanguagesSelectActivity.java", "ProfileNotificationsActivity.java",
)
for name in GLASS_SETTINGS_SCREENS:
    path = ui / name
    if not path.is_file():
        if name == "QuickRepliesSettingsActivity.java":
            # Telegram 13.2.2 removed the standalone legacy Quick Replies
            # settings page. Its remaining controls are owned by upstream;
            # never generate a phantom Activity or alter message behavior.
            print("NOTE: native QuickRepliesSettingsActivity absent; skipping obsolete Glass hook")
            continue
        raise SystemExit(f"Required native settings page missing: {name}")
    source = path.read_text(encoding="utf-8")
    # Telegram's QuickReplies settings use tabs for indentation, unlike the
    # other settings fragments. Match their exact pinned source layout.
    anchor = "\t\tlistView.setSections();" if name == "QuickRepliesSettingsActivity.java" \
            else "        listView.setSections();"
    if source.count(anchor) != 1:
        raise SystemExit(f"{name}: settings list anchor changed ({source.count(anchor)} occurrences)")
    radius = "" if name == "ProfileActivity.java" else "        listView.setSelectorRadius(17);\n"
    # The collapsing Profile hero uses custom visuals; other settings lists
    # require an opaque page canvas to avoid displaying previous fragments.
    page_canvas = "" if name == "ProfileActivity.java" else (
        "        listView.setBackground("
        "org.telegram.ui.Components.NabdhGlassRowDecoration.newOpaquePageBackground());\n"
    )
    source = source.replace(anchor, anchor + """
        // Keep native Telegram section offsets/geometry and accessibility.
        // Hide only its large group paint; independent cells own Glass fill.
        listView.nabdhHideSectionBackgroundOnly();
""" + radius + page_canvas + """        listView.addItemDecoration(
                new org.telegram.ui.Components.NabdhGlassRowDecoration());""", 1)
    # Add the themed filled card AFTER each native row has been bound.
    # No adapters, row data, click handlers or selection logic are changed.
    adapter = source.find("class ListAdapter extends")
    if adapter < 0:
        raise SystemExit(f"{name}: native ListAdapter class not found")
    method = source.find("public void onBindViewHolder(", adapter)
    if method < 0:
        raise SystemExit(f"{name}: native ListAdapter bind method not found")
    opened = source.find("{", method)
    if opened < 0:
        raise SystemExit(f"{name}: ListAdapter method body not found")
    depth = 0
    index = opened
    # Skip Java comments/string literals when measuring nested braces.
    while index < len(source):
        if source.startswith("//", index):
            newline = source.find("\n", index)
            index = len(source) if newline == -1 else newline
            continue
        if source.startswith("/*", index):
            stop = source.find("*/", index + 2)
            if stop < 0:
                raise SystemExit(f"{name}: unclosed Java comment")
            index = stop + 2
            continue
        if source[index] in ('"', "'"):
            delim = source[index]
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                elif source[index] == delim:
                    index += 1
                    break
                else:
                    index += 1
            continue
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                break
        index += 1
    if depth != 0 or index >= len(source):
        raise SystemExit(f"{name}: could not locate ListAdapter bind end")
    # Insert at the BEGINNING of the original closing-brace line. Inserting
    # just before '}' leaves its leading spaces as a newly added blank line
    # (one per settings screen) and makes git diff --check fail. Preserve
    # the original brace/indentation intact instead.
    line_start = source.rfind("\n", 0, index) + 1
    if source[line_start:index].strip():
        raise SystemExit(f"{name}: unexpected non-whitespace before method close")
    source = (source[:line_start]
        + "            org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(holder.itemView);\n"
        + source[line_start:])
    path.write_text(source, encoding="utf-8")
# The real main Settings menu uses SettingCell.Factory, whose text has its
# own layout separate from all native TextCell adjustments.
settings_rtl = ui / "SettingsActivity.java"
settings_rtl_src = settings_rtl.read_text(encoding="utf-8")
rtl_from = """        public void updateColors() {
            titleView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, resourcesProvider));"""
rtl_to = """        public void updateColors() {
            int nabdhDirection = LocaleController.isRTL
                    ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR;
            setLayoutDirection(nabdhDirection);
            textLayout.setLayoutDirection(nabdhDirection);
            // Align the view start with Telegram's selected locale but retain
            // native bidi ordering for mixed Arabic and Latin names.
            titleView.setTextAlignment(View.TEXT_ALIGNMENT_VIEW_START);
            subtitleView.setTextAlignment(View.TEXT_ALIGNMENT_VIEW_START);
            valueView.setTextAlignment(View.TEXT_ALIGNMENT_VIEW_START);
            // The paragraph begins at the locale's start edge but its
            // internal Arabic/Latin runs keep their own strong direction.
            titleView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG);
            subtitleView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG);
            valueView.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG);
            titleView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, resourcesProvider));"""
# SettingsActivity also contains SuggestionCell.updateColors with the
# identical titleView color anchor. Restrict this edit to SettingCell only.
cell_start = settings_rtl_src.find("    public static class SettingCell extends")
cell_end = settings_rtl_src.find("    public static class SuggestionCell extends", cell_start)
if cell_start < 0 or cell_end < 0:
    raise SystemExit("SettingsActivity.SettingCell class boundaries changed")
cell_source = settings_rtl_src[cell_start:cell_end]
if cell_source.count(rtl_from) != 1:
    raise SystemExit("SettingsActivity.SettingCell.updateColors changed")
settings_rtl_src = (settings_rtl_src[:cell_start]
        + cell_source.replace(rtl_from, rtl_to, 1)
        + settings_rtl_src[cell_end:])
settings_rtl.write_text(settings_rtl_src, encoding="utf-8")

# Style the actual SettingsActivity account hero as its own (larger)
# theme-aware surface. Leave child avatar/name/camera touch handlers intact.
settings_hero = ui / "SettingsActivity.java"
hero_source = settings_hero.read_text(encoding="utf-8")
hero_old = "        topView = new FrameLayout(context);"
hero_new = """        topView = new FrameLayout(context);
        // GlassCardLayers already insets 10dp on both sides. The extra
        // InsetDrawable doubled this margin and misaligned the hero.
        topView.setBackground(
                org.telegram.ui.Components.NabdhGlassRowDecoration.newHeroBackground());"""
if hero_source.count(hero_old) != 1:
    raise SystemExit("SettingsActivity account hero constructor changed")
settings_hero.write_text(hero_source.replace(hero_old, hero_new, 1), encoding="utf-8")

# The Account details screen is UserInfoActivity, not ProfileActivity. The
# latter is a different Telegram profile viewer. Its actual phone, handle,
# birthday and channel items use SettingsActivity.SettingCell.Factory and
# require an explicit opt-in to the same shared native Glass decoration.
user_info = ui / "UserInfoActivity.java"
user_info_src = user_info.read_text(encoding="utf-8")
# Account name/bio edit views are UItem.asCustom(EditTextCell), not
# SettingsActivity.SettingCell. Paint their existing containers, never the
# inner EditText: selection, focus, validation and keyboard remain native.
for old, new in (
    ("        firstNameEdit.setDivider(true);",
     """        firstNameEdit.setDivider(false);
        org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(firstNameEdit, true);"""),
    ("        lastNameEdit.hideKeyboardOnEnter();",
     """        lastNameEdit.hideKeyboardOnEnter();
        org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(lastNameEdit, true);"""),
    ("        bioEdit.setShowLimitWhenEmpty(true);",
     """        bioEdit.setShowLimitWhenEmpty(true);
        org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(bioEdit, true);"""),
    ("                ((InfoCell) view).set(item.iconResId, item.text, item.subtext, item.accent, item.red, item.intValue);",
     """                ((InfoCell) view).set(item.iconResId, item.text, item.subtext, item.accent, item.red, item.intValue);
                // Account actions (add-account/logout) have a distinct
                // factory. They must also match the same settings surfaces.
                org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(view, true);"""),
):
    if user_info_src.count(old) != 1:
        raise SystemExit("UserInfoActivity custom editor/account action anchor changed")
    user_info_src = user_info_src.replace(old, new, 1)
account_anchor_legacy = "        listView.setSections();\n        listView.setClipToPadding(false);"
account_anchor_modern = ("        listView.setSections();\n"
        "        listView.setSectionsDrawBackground(true);\n"
        "        listView.setClipToPadding(false);")
if user_info_src.count(account_anchor_legacy) == 1:
    account_anchor = account_anchor_legacy
    native_sections = "        listView.setSections();"
elif user_info_src.count(account_anchor_modern) == 1:
    # Telegram 13.2.x explicitly re-enables section fill. Preserve its
    # setup and opt out of the opaque paint AFTER that call.
    account_anchor = account_anchor_modern
    native_sections = ("        listView.setSections();\n"
                       "        listView.setSectionsDrawBackground(true);")
else:
    raise SystemExit("UserInfoActivity Account rows anchor changed")
account_card = ("""        // Preserve native section geometry and account input behavior.
""" + native_sections + """
        listView.nabdhHideSectionBackgroundOnly();
        // The SimpleActionBar UniversalFragment leaves its root transparent:
        // own the page backdrop behind the account list and header.
        contentView.setBackground(
                org.telegram.ui.Components.NabdhGlassRowDecoration.newOpaquePageBackground());
        listView.adapter.setApplyBackground(false);
        listView.adapter.setNabdhGlassSettings(true);
        // Avoid a second Glass drawing pass under the adapter's card rows.
        listView.setClipToPadding(false);""")
user_info.write_text(user_info_src.replace(account_anchor, account_card, 1), encoding="utf-8")

# Main Telegram Settings uses UniversalAdapter rather than the legacy
# ListAdapter screens above. Re-apply the shared card after updateColors()
# runs (including onViewAttachedToWindow), so custom rows aren't flat.
universal_path = ui / "Components/UniversalAdapter.java"
universal_source = universal_path.read_text(encoding="utf-8")
method_anchor = "    private void updateColors(RecyclerView.ViewHolder holder) {"
if universal_source.count(method_anchor) != 1:
    raise SystemExit("UniversalAdapter.updateColors anchor changed")
begin = universal_source.index(method_anchor)
end = universal_source.find("\n    }", begin)
if end < 0 or "nabdhGlassSettings" not in universal_source[begin:end]:
    raise SystemExit("UniversalAdapter native settings styling was not applied")
universal_source = universal_source[:end] + """
        if (nabdhGlassSettings) {
            int glassType = holder.getItemViewType();
            // Do not turn section headers, profile hero, media, or spacer
            // rows into cards; force only these Settings-specific row types.
            if (holder.itemView instanceof org.telegram.ui.Cells.HeaderCell
                    && (glassType == VIEW_TYPE_HEADER
                            || glassType == VIEW_TYPE_BLACK_HEADER
                            || glassType == VIEW_TYPE_LARGE_HEADER
                            || glassType == VIEW_TYPE_ANIMATED_HEADER)) {
                // Account section headers must blend into the settings canvas,
                // not produce white square panels above rounded input cards.
                holder.itemView.setBackgroundColor(
                        getThemedColor(Theme.key_windowBackgroundGray));
            } else if (holder.itemView instanceof org.telegram.ui.SettingsActivity.SettingCell
                    || glassType == VIEW_TYPE_TEXT_SETTINGS
                    || glassType == VIEW_TYPE_TEXT || glassType == VIEW_TYPE_TEXT_CHECK
                    || glassType == VIEW_TYPE_SWITCH || glassType == VIEW_TYPE_ICON_TEXT_CHECK) {
                NabdhGlassRowDecoration.applyCardStyle(holder.itemView, true);
            }
        }
""" + universal_source[end:]
universal_path.write_text(universal_source, encoding="utf-8")

# The modern Settings screen has a SizeNotifierFrameLayout root with its
# OWN floating avatar, camera, and glass action bar. A backdrop on the
# RecyclerView alone cannot cover those layers or its negative overscroll.
# Removing Telegram's section paint then exposes underlying tabs and causes
# the ghost text/black rails recorded on device. The outer root MUST own the
# opaque theme canvas while inner Glass row surfaces stay translucent.
# UniversalAdapter already reapplies Glass after binding and theme changes;
# a second main-list ItemDecoration duplicates draw work and can disturb the
# original glass capture pipeline. Other legacy lists keep their decorator.
settings_main = ui / "SettingsActivity.java"
settings_source = settings_main.read_text(encoding="utf-8")
enable_anchor = "        listView.adapter.setNabdhGlassSettings(true);"
if settings_source.count(enable_anchor) != 1:
    raise SystemExit("Main Settings unified card opt-in anchor changed")
native_list_anchor = (
    "        listView = new UniversalRecyclerView("
    "this, this::fillItems, this::onClick, this::onLongClick);"
)
if settings_source.count(native_list_anchor) != 1:
    raise SystemExit("Main Settings root/list initialization anchor changed")
settings_source = settings_source.replace(native_list_anchor,
    """        // This root covers the avatar, glass action bar and over-scrolled
        // list; only individual cards are semi-transparent.
        contentView.setBackground(
                org.telegram.ui.Components.NabdhGlassRowDecoration.newOpaquePageBackground());
""" + native_list_anchor, 1)
settings_main.write_text(settings_source, encoding="utf-8")

for activity in ("SettingsActivity.java",):
    page = ui / activity
    content = page.read_text(encoding="utf-8")
    group_anchor = "        listView.setSections();"
    if content.count(group_anchor) != 1:
        raise SystemExit(f"{activity}: native grouped background anchor changed")
    content = content.replace(
        group_anchor,
        group_anchor + "\n        listView.nabdhHideSectionBackgroundOnly();",
        1)
    page.write_text(content, encoding="utf-8")

# Text selection/copy menus on ProfileActivity temporarily draw a scrim
# clone of the selected row. Telegram's getClipBackground returns the original
# broad white section, which appears as a white strip under the bio card.
# Give the menu the actual rounded row drawable when Glass is active.
profile_path = ui / "ProfileActivity.java"
profile_src = profile_path.read_text(encoding="utf-8")
old_scrim = ".setScrimViewBackground(listView.getClipBackground(view))"
new_scrim = """.setScrimViewBackground(
                        org.telegram.ui.Components.NabdhGlassRowDecoration.isGlassCard(view)
                                ? org.telegram.ui.Components.NabdhGlassRowDecoration.newProfileScrim()
                                : listView.getClipBackground(view))"""
if profile_src.count(old_scrim) != 3:
    raise SystemExit("Profile selection scrim anchors changed")
profile_src = profile_src.replace(old_scrim, new_scrim)
profile_path.write_text(profile_src, encoding="utf-8")

print("NabdhGram Glass backgrounds installed on native settings and profile rows.")
