package org.telegram.ui.Components;

import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.content.res.ColorStateList;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.widget.Button;
import android.widget.CompoundButton;
import android.widget.EditText;
import android.widget.Switch;
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

    private static int dp(Context activity, float n) {
        return (int) (n * activity.getResources().getDisplayMetrics().density + .5f);
    }

    public static int shade(int top, int bottom, int percentTop) {
        int q = 100 - percentTop;
        return Color.rgb((Color.red(top) * percentTop + Color.red(bottom) * q) / 100,
                (Color.green(top) * percentTop + Color.green(bottom) * q) / 100,
                (Color.blue(top) * percentTop + Color.blue(bottom) * q) / 100);
    }

    private static GradientDrawable surface(Context activity, int corner) {
        int canvas = Theme.getColor(Theme.key_windowBackgroundGray);
        int paper = Theme.getColor(Theme.key_windowBackgroundWhite);
        int quiet = Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2);
        GradientDrawable result = new GradientDrawable();
        result.setColor(shade(canvas, paper, 56));
        result.setCornerRadius(dp(activity, corner));
        result.setStroke(Math.max(1, dp(activity, 1)),
                Color.argb(48, Color.red(quiet), Color.green(quiet), Color.blue(quiet)));
        return result;
    }

    public static void styleInput(Context activity, EditText field) {
        int d = dp(activity, 14);
        field.setTextSize(15);
        field.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        field.setHintTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        field.setPadding(d, dp(activity, 10), d, dp(activity, 10));
        field.setMinHeight(dp(activity, 52));
        field.setBackground(surface(activity, 12));
        field.setTextDirection(LocaleController.isRTL
                ? View.TEXT_DIRECTION_RTL : View.TEXT_DIRECTION_FIRST_STRONG);
    }

    public static void styleButton(Context activity, Button button) {
        button.setAllCaps(false);
        button.setTextSize(14);
        button.setMinHeight(dp(activity, 48));
        button.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        GradientDrawable mask = new GradientDrawable();
        mask.setColor(Color.WHITE);
        mask.setCornerRadius(dp(activity, 12));
        button.setBackground(new RippleDrawable(
                ColorStateList.valueOf(Color.argb(36, Color.red(accent),
                        Color.green(accent), Color.blue(accent))),
                surface(activity, 12), mask));
        button.setPadding(dp(activity, 16), dp(activity, 10),
                dp(activity, 16), dp(activity, 10));
    }

    public static void styleToggle(Context activity, CompoundButton toggle) {
        int on = Theme.getColor(Theme.key_switchTrackBlueChecked);
        int off = Theme.getColor(Theme.key_switchTrackBlue);
        ColorStateList states = new ColorStateList(
                new int[][]{new int[]{android.R.attr.state_checked}, new int[]{}},
                new int[]{on, off});
        if (toggle instanceof Switch) {
            ((Switch) toggle).setThumbTintList(new ColorStateList(
                    new int[][]{new int[]{android.R.attr.state_checked}, new int[]{}},
                    new int[]{Theme.getColor(Theme.key_switchTrackBlueThumbChecked),
                            Theme.getColor(Theme.key_switchTrackBlueThumb)}));
            ((Switch) toggle).setTrackTintList(new ColorStateList(
                    new int[][]{new int[]{android.R.attr.state_checked}, new int[]{}},
                    new int[]{on, off}));
        } else {
            toggle.setButtonTintList(states);
        }
    }

    public static void install(Activity activity, View content, String title) {
        LinearLayout shell = new LinearLayout(activity);
        shell.setOrientation(LinearLayout.VERTICAL);
        shell.setLayoutDirection(LocaleController.isRTL
                ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        shell.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));

        LinearLayout bar = new LinearLayout(activity);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(activity, 12), 0, dp(activity, 16), 0);
        bar.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));

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
