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
        return view instanceof org.telegram.ui.Cells.TextCell
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
                || view instanceof org.telegram.ui.Cells.ProfileChannelCell;
    }

    // Draw exactly one inset card. Stacking the old ColorDrawable (usually
    // opaque white) underneath an inset card leaves a white rectangular strip
    // around every row, particularly obvious in RTL settings and profiles.
    // A native RippleDrawable preserves pressed feedback and touch behavior.
    public static void applyCardStyle(View child) {
        if (!isSettingRow(child)) return;
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
        GlassCardLayers() {
            super(android.content.res.ColorStateList.valueOf(
                    Theme.getColor(Theme.key_listSelector)),
                    new LiveGlassSurface(), null);
        }
        void refreshThemeTint() {
            setColor(android.content.res.ColorStateList.valueOf(
                    Theme.getColor(Theme.key_listSelector)));
            invalidateSelf();
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
            final int red = (Color.red(base) * 90 + Color.red(accent) * 10) / 100;
            final int green = (Color.green(base) * 90 + Color.green(accent) * 10) / 100;
            final int blue = (Color.blue(base) * 90 + Color.blue(accent) * 10) / 100;
            float inset = AndroidUtilities.dp(10);
            float vertical = AndroidUtilities.dp(2);
            float round = AndroidUtilities.dp(16);
            rect.set(bounds.left + inset, bounds.top + vertical,
                    bounds.right - inset, bounds.bottom - vertical);
            if (rect.width() <= 0 || rect.height() <= 0) return;
            fill.setStyle(Paint.Style.FILL);
            fill.setColor(Color.argb(opacity, red, green, blue));
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
            if (!isSettingRow(child) || child.getVisibility() != View.VISIBLE
                    || child.getBackground() instanceof GlassCardLayers) {
                continue;
            }
            bounds.set(child.getLeft() + inset, child.getTop() + topInset,
                    child.getRight() - inset, child.getBottom() - topInset);
            if (bounds.width() > 0 && bounds.height() > AndroidUtilities.dp(28)) {
                canvas.drawRoundRect(bounds, radius, radius, stroke);
            }
        }
    }
}
""", encoding="utf-8")

for name in ("NotificationsSettingsActivity.java", "PrivacySettingsActivity.java",
             "DataSettingsActivity.java", "ThemeActivity.java",
             "ProfileActivity.java"):
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
            NabdhGlassRowDecoration.applyCardStyle(holder.itemView);
        }
""" + universal_source[end:]
universal_path.write_text(universal_source, encoding="utf-8")

# The main SettingsActivity uses UniversalRecyclerView; profile and other
# native screens are covered by the loop above. Remove its parent section
# once, leaving child cards, row order and adapters untouched.
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

print("NabdhGram Glass backgrounds installed on native settings and profile rows.")
