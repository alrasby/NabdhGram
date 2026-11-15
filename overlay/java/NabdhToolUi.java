package org.telegram.ui.Components;

import android.app.Activity;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;

/**
 * Shared NabdhGram tool-page chrome, aligned to Telegram's in-app language,
 * selected font and Theme color keys. Avoids isolated stock Android screens.
 * All tool activities keep their existing behavior, without native chat hooks.
 */
public final class NabdhToolUi {
    private NabdhToolUi() {}

    private static int dp(Activity activity, float n) {
        return (int) (n * activity.getResources().getDisplayMetrics().density + .5f);
    }

    public static void install(Activity activity, View content, String title) {
        LinearLayout shell = new LinearLayout(activity);
        shell.setOrientation(LinearLayout.VERTICAL);
        shell.setLayoutDirection(LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        shell.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));

        LinearLayout bar = new LinearLayout(activity);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(activity, 12), 0, dp(activity, 16), 0);
        bar.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));

        TextView back = new TextView(activity);
        back.setText(LocaleController.isRTL ? "›" : "‹");
        back.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        back.setTextSize(31);
        back.setGravity(Gravity.CENTER);
        back.setContentDescription(LocaleController.isRTL ? "رجوع" : "Back");
        back.setClickable(true);
        back.setFocusable(true);
        back.setOnClickListener(v -> activity.onBackPressed());
        bar.addView(back, new LinearLayout.LayoutParams(dp(activity, 42), dp(activity, 52)));

        TextView heading = new TextView(activity);
        heading.setText(title);
        heading.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        heading.setTextSize(18);
        heading.setTypeface(AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
        heading.setGravity(LocaleController.isRTL ? Gravity.RIGHT : Gravity.LEFT);
        heading.setSingleLine(true);
        heading.setEllipsize(android.text.TextUtils.TruncateAt.END);
        LinearLayout.LayoutParams titleParams = new LinearLayout.LayoutParams(0, -2, 1f);
        titleParams.leftMargin = dp(activity, 6);
        bar.addView(heading, titleParams);
        shell.addView(bar, new LinearLayout.LayoutParams(-1, dp(activity, 56)));

        View line = new View(activity);
        int accent = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2);
        line.setBackgroundColor(Color.argb(36, Color.red(accent), Color.green(accent),
                Color.blue(accent)));
        shell.addView(line, new LinearLayout.LayoutParams(-1, dp(activity, 1)));
        shell.addView(content, new LinearLayout.LayoutParams(-1, 0, 1f));
        activity.setContentView(shell);
    }
}
