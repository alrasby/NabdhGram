package org.telegram.ui.Components;

import android.content.Context;
import android.graphics.Color;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.ui.ActionBar.Theme;

/**
 * Single visual owner for NabdhGram settings rows, not a Telegram engine patch.
 *
 * Use the same live Glass row drawable as Telegram's main Settings page.
 * The group only preserves logical ordering: each option has its own rounded
 * surface and masked ripple. No opaque white parent or unbounded press circle.
 * Never hides or changes the action bound to a row.
 */
public final class NabdhCompactSettings {
    private static final String GROUP_TAG = "nabdh:compact-setting-group:v1";

    private NabdhCompactSettings() {}

    private static int dp(Context context, float size) {
        return (int) (size * context.getResources().getDisplayMetrics().density + .5f);
    }

    private static int translucent(int source, int opacity) {
        return Color.argb(opacity, Color.red(source),
                Color.green(source), Color.blue(source));
    }

    private static LinearLayout ensureGroup(Context context, LinearLayout parent) {
        int index = parent.getChildCount() - 1;
        if (index >= 0) {
            View previous = parent.getChildAt(index);
            if (previous instanceof LinearLayout && GROUP_TAG.equals(previous.getTag())) {
                return (LinearLayout) previous;
            }
        }

        LinearLayout group = new LinearLayout(context);
        group.setTag(GROUP_TAG);
        group.setOrientation(LinearLayout.VERTICAL);
        group.setLayoutDirection(LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        // No second white/slate parent panel behind Telegram's own Glass cards.
        group.setBackground(null);
        group.setClipChildren(false);
        group.setClipToPadding(false);

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.bottomMargin = dp(context, 16);
        parent.addView(group, params);
        return group;
    }

    /** A header naturally breaks one rounded group from the next. */
    public static void header(Context context, LinearLayout parent, String heading) {
        TextView title = new TextView(context);
        title.setText(heading);
        title.setTextSize(13);
        title.setTypeface(AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
        title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        title.setGravity(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT);
        title.setPadding(dp(context, 10), dp(context, 16),
                dp(context, 10), dp(context, 8));
        parent.addView(title, new LinearLayout.LayoutParams(-1, -2));
    }

    public static void row(Context context, LinearLayout parent, String title,
                           String subtitle, int icon, Runnable action) {
        row(context, parent, title, subtitle, icon,
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueText), action);
    }

    public static void row(Context context, LinearLayout parent, String title,
                           String subtitle, int icon, int accent, Runnable action) {
        LinearLayout group = ensureGroup(context, parent);
        final boolean rtl = LocaleController.isRTL;
        final int primary = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText);
        final int secondary = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2);

        // Individual rows draw their own stroke, spacing and masked press feedback.

        LinearLayout row = new LinearLayout(context);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setLayoutDirection(rtl ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setMinimumHeight(dp(context, TextUtils.isEmpty(subtitle) ? 54 : 66));
        row.setPadding(dp(context, 14), dp(context, 9),
                dp(context, 14), dp(context, 9));
        row.setClickable(true);
        row.setFocusable(true);
        row.setContentDescription(TextUtils.isEmpty(subtitle) ? title : title + ". " + subtitle);
        row.setOnClickListener(v -> action.run());
        row.setBackground(NabdhGlassRowDecoration.newCardBackground());
        row.setClipToOutline(true);

        if (icon != 0) {
            ImageView image = new ImageView(context);
            image.setImageResource(NabdhAppearancePrefs.icon(context, icon));
            image.setColorFilter(accent);
            image.setScaleType(ImageView.ScaleType.FIT_CENTER);
            LinearLayout.LayoutParams imageParams =
                    new LinearLayout.LayoutParams(dp(context, 24), dp(context, 24));
            imageParams.setMarginEnd(dp(context, 17));
            row.addView(image, imageParams);
        }

        LinearLayout text = new LinearLayout(context);
        text.setOrientation(LinearLayout.VERTICAL);
        text.setGravity(Gravity.CENTER_VERTICAL);
        text.setLayoutDirection(rtl ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        LinearLayout.LayoutParams textParams = new LinearLayout.LayoutParams(0, -2, 1f);
        row.addView(text, textParams);

        TextView heading = new TextView(context);
        heading.setText(title);
        heading.setTextColor(primary);
        heading.setTextSize(15);
        heading.setMaxLines(2);
        heading.setEllipsize(TextUtils.TruncateAt.END);
        heading.setGravity(rtl ? Gravity.RIGHT : Gravity.LEFT);
        heading.setTypeface(AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
        text.addView(heading, new LinearLayout.LayoutParams(-1, -2));

        if (!TextUtils.isEmpty(subtitle)) {
            TextView summary = new TextView(context);
            summary.setText(subtitle);
            summary.setTextSize(11);
            summary.setTextColor(secondary);
            summary.setMaxLines(2);
            summary.setEllipsize(TextUtils.TruncateAt.END);
            summary.setGravity(rtl ? Gravity.RIGHT : Gravity.LEFT);
            LinearLayout.LayoutParams summaryParams =
                    new LinearLayout.LayoutParams(-1, -2);
            summaryParams.topMargin = dp(context, 3);
            text.addView(summary, summaryParams);
        }

        TextView arrow = new TextView(context);
        arrow.setText(rtl ? "‹" : "›");
        arrow.setTextSize(21);
        arrow.setGravity(Gravity.CENTER);
        arrow.setTextColor(translucent(secondary, 175));
        arrow.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        LinearLayout.LayoutParams arrowParams =
                new LinearLayout.LayoutParams(dp(context, 22), dp(context, 32));
        arrowParams.setMarginStart(dp(context, 8));
        row.addView(arrow, arrowParams);
        LinearLayout.LayoutParams rowParams = new LinearLayout.LayoutParams(-1, -2);
        rowParams.bottomMargin = dp(context, 3);
        group.addView(row, rowParams);
    }
}
