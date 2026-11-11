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
        final String name = view.getClass().getSimpleName();
        return name.equals("TextCell") || name.equals("TextSettingsCell")
                || name.equals("TextCheckCell") || name.equals("TextCheckCell2")
                || name.equals("TextRightIconCell") || name.equals("NotificationsCheckCell")
                || name.equals("RadioButtonCell") || name.equals("DialogRadioCell");
    }

    @Override
    public void onDrawOver(@NonNull Canvas canvas, @NonNull RecyclerView parent,
            @NonNull RecyclerView.State state) {
        final int color = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        stroke.setColor(Color.argb(50, Color.red(color), Color.green(color), Color.blue(color)));
        stroke.setStyle(Paint.Style.STROKE);
        stroke.setStrokeWidth(AndroidUtilities.dpf2(.8f));
        final float inset = AndroidUtilities.dp(11);
        final float topInset = AndroidUtilities.dp(2);
        final float radius = AndroidUtilities.dp(15);
        for (int index = 0; index < parent.getChildCount(); index++) {
            final View child = parent.getChildAt(index);
            if (!isSettingRow(child) || child.getVisibility() != View.VISIBLE) {
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
             "DataSettingsActivity.java", "ThemeActivity.java"):
    path = ui / name
    source = path.read_text(encoding="utf-8")
    anchor = "        listView.setSections();"
    if source.count(anchor) != 1:
        raise SystemExit(f"{name}: settings list anchor changed")
    source = source.replace(anchor,
        anchor + """
        // NabdhGram unified design: theme-aware border around settings rows.
        // Draw-only decoration preserves original scrolling and row actions.
        listView.setSelectorRadius(17);
        listView.addItemDecoration(
                new org.telegram.ui.Components.NabdhGlassRowDecoration());""", 1)
    path.write_text(source, encoding="utf-8")
print("NabdhGram unified native Settings decoration installed on four legacy screens.")
