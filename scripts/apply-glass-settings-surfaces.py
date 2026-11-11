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
                    new LiveGlassSurface(), null);
            lastTint = Theme.getColor(Theme.key_listSelector);
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
            float round = AndroidUtilities.dp(16);
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

    @Override
    public void onDrawOver(@NonNull Canvas canvas, @NonNull RecyclerView parent,
            @NonNull RecyclerView.State state) {
        final int color = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        stroke.setColor(Color.argb(82, Color.red(color), Color.green(color), Color.blue(color)));
        stroke.setStyle(Paint.Style.STROKE);
        stroke.setStrokeWidth(AndroidUtilities.dpf2(1f));
        final float inset = AndroidUtilities.dp(11);
        final float topInset = AndroidUtilities.dp(2);
        final float radius = AndroidUtilities.dp(17);
        for (int index = 0; index < parent.getChildCount(); index++) {
            final View child = parent.getChildAt(index);
            if (!isSettingRow(child) || child.getVisibility() != View.VISIBLE) {
                continue;
            }
            // A number of Telegram adapters replace the row background
            // after binding (and on theme changes). Restore an actual filled
            // Glass drawable, not merely a border, on the next draw frame.
            if (!(child.getBackground() instanceof GlassCardLayers)) {
                applyCardStyle(child);
            } else {
                ((GlassCardLayers) child.getBackground()).refreshThemeTint();
            }
        }
    }
}
""", encoding="utf-8")

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

for name in ("NotificationsSettingsActivity.java", "PrivacySettingsActivity.java",
             "DataSettingsActivity.java", "ThemeActivity.java",
             "ProfileActivity.java", "LanguageSelectActivity.java",
             "SessionsActivity.java", "PrivacyControlActivity.java",
             "NotificationsCustomSettingsActivity.java", "CacheControlActivity.java"):
    path = ui / name
    source = path.read_text(encoding="utf-8")
    anchor = "        listView.setSections();"
    if source.count(anchor) != 1:
        raise SystemExit(f"{name}: settings list anchor changed")
    radius = "" if name == "ProfileActivity.java" else "        listView.setSelectorRadius(17);\n"
    source = source.replace(anchor, """
        // NabdhGram: remove the large white parent section. Draw each native
        // cell as its own theme-aware Glass card, without touching its data.
""" + radius + """        listView.addItemDecoration(
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
    source = source[:index] + """
            org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(holder.itemView);
""" + source[index:]
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
            if (holder.itemView instanceof org.telegram.ui.SettingsActivity.SettingCell
                    || glassType == VIEW_TYPE_TEXT_SETTINGS
                    || glassType == VIEW_TYPE_TEXT || glassType == VIEW_TYPE_TEXT_CHECK
                    || glassType == VIEW_TYPE_SWITCH || glassType == VIEW_TYPE_ICON_TEXT_CHECK) {
                NabdhGlassRowDecoration.applyCardStyle(holder.itemView, true);
            }
        }
""" + universal_source[end:]
universal_path.write_text(universal_source, encoding="utf-8")

# The main SettingsActivity uses UniversalRecyclerView; profile and other
# native screens are covered by the loop above. Remove its parent section
# once, leaving child cards, row order and adapters untouched.
# Main Settings uses a UniversalRecyclerView adapter, which can recreate
# native row backgrounds after updateColors(). Install the same fallback
# decorator there, just as on the ten legacy settings screens.
settings_main = ui / "SettingsActivity.java"
settings_source = settings_main.read_text(encoding="utf-8")
enable_anchor = "        listView.adapter.setNabdhGlassSettings(true);"
if settings_source.count(enable_anchor) != 1:
    raise SystemExit("Main Settings unified card opt-in anchor changed")
settings_source = settings_source.replace(enable_anchor, enable_anchor + """
        listView.addItemDecoration(new org.telegram.ui.Components.NabdhGlassRowDecoration());""", 1)
settings_main.write_text(settings_source, encoding="utf-8")

for activity in ("SettingsActivity.java",):
    page = ui / activity
    content = page.read_text(encoding="utf-8")
    group_anchor = "        listView.setSections();"
    if content.count(group_anchor) != 1:
        raise SystemExit(f"{activity}: native grouped background anchor changed")
    content = content.replace(
        group_anchor,
        "        // NabdhGram: no large grouped background behind individual Glass cards.",
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
