#!/usr/bin/env python3
"""Final UI geometry pass for NabdhGram v1: real Android views, not mockups.

Applied after the existing Glass overlays and locale resolver. Does not modify
dialog adapters, navigation IDs, messaging, calls, authentication or database.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-final-screens.py TELEGRAM_SOURCE")

ui = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"

def read(name):
    p = ui / name
    return p, p.read_text(encoding="utf-8")

def replace_once(s, before, after, where):
    count = s.count(before)
    if count != 1:
        raise SystemExit(f"{where}: expected one anchor, got {count}")
    return s.replace(before, after, 1)

# 1. The six feature cards are one-column on phone screens: the experimental
# two-column layout created extra parent rows and compressed multi-line Arabic.
p, s = read("NabdhGramSettingsActivity.java")
start = s.find("        boolean compactGrid =")
next_card = s.find("        section(context, compactGrid ?", start)
if start < 0 or next_card < 0:
    raise SystemExit("NabdhGram settings grid creation has changed")
s = s[:start] + s[next_card:]
s, count = re.subn(
    r"section\(context, compactGrid \? nabdhRows\[\d+\] : content,",
    "section(context, content,", s)
if count != 6:
    raise SystemExit(f"Expected six category cards; found {count}")

method_start = s.find("    private void section(Context context, LinearLayout parent, int titleRes, int descriptionRes) {")
method_end = s.rfind("\n    }\n}")
if method_start < 0 or method_end < method_start:
    raise SystemExit("NabdhGram section rendering method changed")
method = """    private void section(Context context, LinearLayout parent, int titleRes, int descriptionRes) {
        final float density = context.getResources().getDisplayMetrics().density;
        final int pad = (int) (12 * density + .5f);
        final int iconSide = (int) (42 * density + .5f);
        final int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        final int surface = Theme.getColor(Theme.key_windowBackgroundWhite);
        final int neutral = Theme.getColor(Theme.key_windowBackgroundGray);
        final boolean rtl = org.telegram.messenger.LocaleController.isRTL;

        // Actual card layout: one horizontal content row with separately
        // measured title and subtitle, rather than three loosely placed lines.
        LinearLayout card = new LinearLayout(context);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setLayoutDirection(rtl ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        card.setGravity(android.view.Gravity.CENTER_VERTICAL);
        card.setPadding(pad, pad, pad, pad);
        card.setMinimumHeight((int) (78 * density + .5f));

        GradientDrawable glass = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR, new int[] {surface, neutral});
        glass.setCornerRadius(20 * density);
        glass.setStroke(Math.max(1, (int) density),
                Color.argb(110, Color.red(accent), Color.green(accent), Color.blue(accent)));
        // One card renderer shared with Telegram Settings, including a
        // clipped Ripple and immediate imported-theme responsiveness.
        card.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());

        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(-1, -2);
        cardLp.bottomMargin = (int) (8 * density + .5f);
        parent.addView(card, cardLp);

        int iconRes = titleRes == R.string.NabdhShieldTitle ? R.drawable.settings_privacy
                : titleRes == R.string.NabdhPrivacyTitle ? R.drawable.settings_devices
                : titleRes == R.string.NabdhProductivityTitle ? R.drawable.settings_folders
                : titleRes == R.string.NabdhLanguageTitle ? R.drawable.settings_language
                : titleRes == R.string.NabdhNetworkTitle ? R.drawable.settings_data
                : R.drawable.settings_chat;
        android.widget.FrameLayout iconFrame = new android.widget.FrameLayout(context);
        GradientDrawable iconBackground = new GradientDrawable();
        iconBackground.setColor(Color.argb(23, Color.red(accent),
                Color.green(accent), Color.blue(accent)));
        iconBackground.setCornerRadius(13 * density);
        iconFrame.setBackground(iconBackground);
        android.widget.ImageView icon = new android.widget.ImageView(context);
        icon.setImageResource(iconRes);
        icon.setColorFilter(accent);
        iconFrame.addView(icon, new android.widget.FrameLayout.LayoutParams(
                (int) (24 * density + .5f), (int) (24 * density + .5f),
                android.view.Gravity.CENTER));
        card.addView(iconFrame, new LinearLayout.LayoutParams(iconSide, iconSide));

        LinearLayout labels = new LinearLayout(context);
        labels.setOrientation(LinearLayout.VERTICAL);
        labels.setGravity(android.view.Gravity.CENTER_VERTICAL);
        labels.setLayoutDirection(rtl ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        LinearLayout.LayoutParams labelsLp = new LinearLayout.LayoutParams(0, -2, 1f);
        labelsLp.setMarginStart((int) (11 * density + .5f));
        labelsLp.setMarginEnd((int) (5 * density + .5f));
        card.addView(labels, labelsLp);

        TextView heading = new TextView(context);
        heading.setText(NabdhStrings.get(context, titleRes));
        heading.setTextSize(16);
        heading.setTypeface(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rregular.ttf"));
        heading.setTextColor(accent);
        heading.setMaxLines(2);
        heading.setEllipsize(android.text.TextUtils.TruncateAt.END);
        heading.setGravity((rtl ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT)
                | android.view.Gravity.CENTER_VERTICAL);
        labels.addView(heading, new LinearLayout.LayoutParams(-1, -2));

        int summaryRes = R.string.NabdhGlassAppearanceSummary;
        if (titleRes == R.string.NabdhShieldTitle) summaryRes = R.string.NabdhGlassShieldSummary;
        else if (titleRes == R.string.NabdhPrivacyTitle) summaryRes = R.string.NabdhGlassPrivacySummary;
        else if (titleRes == R.string.NabdhProductivityTitle) summaryRes = R.string.NabdhGlassProductivitySummary;
        else if (titleRes == R.string.NabdhLanguageTitle) summaryRes = R.string.NabdhGlassLanguageSummary;
        else if (titleRes == R.string.NabdhNetworkTitle) summaryRes = R.string.NabdhGlassNetworkSummary;
        TextView description = new TextView(context);
        description.setText(NabdhStrings.get(context, summaryRes));
        description.setTextSize(12);
        // This final layout replaces the earlier settings category builder.
        // Preserve readable summary weight when the global Bold control is on.
        description.setTag("nabdh:secondary-text");
        description.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        description.setMaxLines(2);
        description.setEllipsize(android.text.TextUtils.TruncateAt.END);
        description.setGravity(rtl ? android.view.Gravity.RIGHT : android.view.Gravity.LEFT);
        LinearLayout.LayoutParams descLp = new LinearLayout.LayoutParams(-1, -2);
        descLp.topMargin = (int) (3 * density + .5f);
        labels.addView(description, descLp);

        TextView arrow = new TextView(context);
        arrow.setText(rtl ? "‹" : "›");
        arrow.setTextSize(21);
        arrow.setTextColor(accent);
        arrow.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        card.addView(arrow, new LinearLayout.LayoutParams(-2, -2));

        card.setContentDescription(heading.getText() + ". " + description.getText());
        card.setClickable(true);
        card.setFocusable(true);
        card.setOnClickListener(v -> presentFragment(
                new NabdhGramFeatureCategoryActivity(titleRes, descriptionRes)));
    }
"""
s = s[:method_start] + method + s[method_end + len("\n    }"):]
s = replace_once(s, "int pad = (int) (12 * context.getResources().getDisplayMetrics().density);",
                 "int pad = (int) (12 * context.getResources().getDisplayMetrics().density);",
                 "Settings outer padding")
p.write_text(s, encoding="utf-8")

# 2. A compact light/dark Glass surface for actual contact rows; only the
# native ContactsAdapter USER_CELL branch is affected. No adapter changes.
p, s = read("Adapters/ContactsAdapter.java")
anchor = """                cell.setCallCellStyle(58);
                view = cell;"""
styling = """                cell.setCallCellStyle(58);
                // Same native Glass card/ripple as Settings and dialogs.
                // No per-row unused GradientDrawable allocation.
                cell.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
                view = cell;"""
s = replace_once(s, anchor, styling, "Contacts adapter USER_CELL")
# The two native Contacts actions (invite friends, recent calls) are TEXT_CELL
# rather than USER_CELL. Style them at construction; keep click and section
# semantics, headers and fast scroll untouched.
s = replace_once(s,
    "                view = new TextCell(mContext);\n                break;",
    """                view = new TextCell(mContext);
                org.telegram.ui.Components.NabdhGlassRowDecoration.applyCardStyle(view);
                break;""",
    "Contacts adapter action row Glass surface")
p.write_text(s, encoding="utf-8")

# 3. Profile channel header and body currently share a hard 102dp measured
# height; scale-aware height avoids cutting Arabic labels and media previews.
p, s = read("Cells/ProfileChannelCell.java")
s = replace_once(
    s, "headerLayout.setOrientation(LinearLayout.HORIZONTAL);",
    """headerLayout.setOrientation(LinearLayout.HORIZONTAL);
        headerLayout.setLayoutDirection(LocaleController.isRTL
                ? LAYOUT_DIRECTION_RTL : LAYOUT_DIRECTION_LTR);""",
    "Profile channel header layout direction"
)
s = replace_once(
    s, "LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 17, Gravity.LEFT | Gravity.TOP, 4, 1, 4, 0)",
    "LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, 20, Gravity.LEFT | Gravity.TOP, 6, 1, 4, 0)",
    "Profile channel subscriber label measure"
)
s = replace_once(
    s, "MeasureSpec.makeMeasureSpec(dp(102), MeasureSpec.EXACTLY)",
    """MeasureSpec.makeMeasureSpec(dp(Math.max(122,
                (int) (106 * getResources().getConfiguration().fontScale))),
                MeasureSpec.EXACTLY)""",
    "Profile channel fixed card height"
)
p.write_text(s, encoding="utf-8")

print("Finalized compact localized Settings, native Contacts rows and scale-aware profile channel.")
