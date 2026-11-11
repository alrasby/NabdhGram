#!/usr/bin/env python3
"""NabdhGram v1 finishing pass: fix real RTL badges, settings and input/bubble paint.

Run after the localized feature screens, without replacing Telegram's working
navigation, auth logic, media paths, update handlers or message data.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-v1-finishing.py TELEGRAM_SOURCE")
ui = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"

def modify(relative, changes):
    path = ui / relative
    source = path.read_text(encoding="utf-8")
    for original, replacement, count in changes:
        found = source.count(original)
        if found != count:
            raise SystemExit(f"{relative}: anchor changed, expected {count}, found {found}: {original[:64]}")
        source = source.replace(original, replacement, count)
    path.write_text(source, encoding="utf-8")

# Bug report: custom SimpleTextView paints leftDrawable at x=0 even when
# name gravity is RIGHT. For Arabic names this falls *inside* the glyphs.
# Opt-in per contact-name view, not a global change to Telegram widgets.
modify("ActionBar/SimpleTextView.java", [
    (
        """    public void setTypeface(Typeface typeface) {
        textPaint.setTypeface(typeface);
    }""",
        """    public void setTypeface(Typeface typeface) {
        if (textPaint.getTypeface() == typeface) return;
        textPaint.setTypeface(typeface);
        // This view paints a cached StaticLayout. A new typeface changes
        // glyph widths and baselines; just invalidating leaves stale names.
        if (!recreateLayoutMaybe()) {
            requestLayout();
            invalidate();
        }
    }

    // Custom Telegram titles paint a StaticLayout, not an Android TextView.
    // Track their original size once so changing fonts/scales takes effect
    // immediately and does not compound the previous size.
    private float nabdhOriginalTextPx = -1f;
    private int nabdhOriginalTextStyle;
    private boolean nabdhNativeTextApplied;

    public void nabdhRefreshSelectedFont() {
        Typeface current = textPaint.getTypeface();
        if (current == null) return;
        boolean standard = nabdhNativeTextApplied
                || current.equals(Typeface.DEFAULT)
                || current.equals(Typeface.DEFAULT_BOLD)
                || current.equals(Typeface.SANS_SERIF)
                || current.equals(Typeface.create("sans-serif", Typeface.BOLD))
                || current.equals(Typeface.create("sans-serif-medium", Typeface.NORMAL))
                || current.equals(Typeface.create("sans-serif-medium", Typeface.BOLD))
                || current.equals(AndroidUtilities.getTypeface("fonts/rregular.ttf"))
                || current.equals(AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
        if (!standard) {
            for (String filename : new String[]{"ReadexPro.ttf", "Vazirmatn.ttf",
                    "NotoSansArabic.ttf", "Tajawal.ttf", "Rubik.ttf"}) {
                Typeface candidate = AndroidUtilities.getTypeface("fonts/" + filename);
                if (candidate != null && (current.equals(candidate)
                        || current.equals(Typeface.create(candidate, Typeface.NORMAL))
                        || current.equals(Typeface.create(candidate, Typeface.BOLD)))) {
                    standard = true;
                    break;
                }
            }
        }
        // Never replace icon, math, code or specialty fonts.
        if (!standard) return;
        if (nabdhOriginalTextPx < 0f) {
            nabdhOriginalTextPx = textPaint.getTextSize();
            nabdhOriginalTextStyle = current.getStyle();
        }
        android.content.SharedPreferences preferences = getContext()
                .getSharedPreferences("nabdhgram_appearance", android.content.Context.MODE_PRIVATE);
        int scale = Math.max(85, Math.min(115,
                preferences.getInt("ui_scale_percent", 100)));
        boolean useMedium = "system-default".equals(
                preferences.getString("font_family", "system-default"))
                && (nabdhOriginalTextStyle & Typeface.BOLD) != 0;
        Typeface desired = AndroidUtilities.getTypeface(
                useMedium ? "fonts/rmedium.ttf" : "fonts/rregular.ttf");
        if (desired != null && !desired.equals(current)) {
            setTypeface(desired);
        }
        final int desiredPx = Math.max(1,
                Math.round(nabdhOriginalTextPx * scale / 100f));
        if (Math.abs(textPaint.getTextSize() - desiredPx) > 0.5f) {
            setTextSizePx(desiredPx);
        }
        nabdhNativeTextApplied = true;
    }""",
        1
    ),
    (
        "    public void setDrawablePadding(int value) {",
        """    private boolean nabdhRtlBadgeBeforeText;

    public void setNabdhRtlBadgeBeforeText(boolean enabled) {
        nabdhRtlBadgeBeforeText = enabled;
        invalidate();
    }

    public void setDrawablePadding(int value) {""",
        1
    ),
    (
        """            if ((gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.CENTER_HORIZONTAL) {
                x += offsetX;
            }
            int y;
            if ((gravity & Gravity.VERTICAL_GRAVITY_MASK) == Gravity.CENTER_VERTICAL) {
                y = (getMeasuredHeight() - leftDrawable.getIntrinsicHeight()) / 2 + leftDrawableTopPadding;""",
        """            if ((gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.CENTER_HORIZONTAL) {
                x += offsetX;
            } else if (nabdhRtlBadgeBeforeText
                    && (gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.RIGHT) {
                // The layout reserves icon width but onDraw did not advance
                // textOffsetX for RIGHT gravity, so a full-width Arabic name
                // overlapped this icon. With textOffsetX fixed below, anchor
                // the badge to the actual translated glyph start for mixed
                // Arabic, Latin and emoji names.
                float lineLeft = layout != null && layout.getLineCount() > 0
                        ? layout.getLineLeft(0) : 0f;
                float visibleTextStart = offsetX
                        + leftDrawable.getIntrinsicWidth() + drawablePadding + lineLeft;
                x = Math.max(0, Math.round(visibleTextStart
                        - drawablePadding - leftDrawable.getIntrinsicWidth() - dp(4)));
            }
            int y;
            if ((gravity & Gravity.VERTICAL_GRAVITY_MASK) == Gravity.CENTER_VERTICAL) {
                y = (getMeasuredHeight() - leftDrawable.getIntrinsicHeight()) / 2 + leftDrawableTopPadding;""",
        1
    ),
    (
        """            if ((gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.LEFT || (gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.CENTER_HORIZONTAL) {
                textOffsetX += drawablePadding + leftDrawable.getIntrinsicWidth();
            }
            totalWidth += drawablePadding + leftDrawable.getIntrinsicWidth();""",
        """            if ((gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.LEFT
                    || (gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.CENTER_HORIZONTAL
                    || (nabdhRtlBadgeBeforeText
                        && (gravity & Gravity.HORIZONTAL_GRAVITY_MASK) == Gravity.RIGHT)) {
                // RIGHT-gravity verified names also need this reserved space
                // in the actual draw translation, not only in createLayout().
                textOffsetX += drawablePadding + leftDrawable.getIntrinsicWidth();
            }
            totalWidth += drawablePadding + leftDrawable.getIntrinsicWidth();""",
        1
    ),
])
modify("Cells/UserCell.java", [
    (
        "        nameTextView.setDrawablePadding(dp(13));",
        """        nameTextView.setDrawablePadding(dp(8));
        nameTextView.setNabdhRtlBadgeBeforeText(LocaleController.isRTL);""",
        1
    ),
])

# Scope Glass styling to the native SETTINGS page. Other screens using the
# UniversalAdapter retain their own media controls, animation and row grouping.
modify("Components/UniversalAdapter.java", [
    (
        "    private boolean applyBackground = true;",
        """    private boolean applyBackground = true;
    private boolean nabdhGlassSettings;

    public void setNabdhGlassSettings(boolean enabled) {
        nabdhGlassSettings = enabled;
    }""",
        1
    ),
    (
        """    private void updateColors(RecyclerView.ViewHolder holder) {
        if (holder.itemView instanceof Theme.Colorable) {
            ((Theme.Colorable) holder.itemView).updateColors();
            if (shouldApplyBackground(holder.getItemViewType())) {
                final int key_background = dialog ? Theme.key_dialogBackground : Theme.key_windowBackgroundWhite;
                holder.itemView.setBackgroundColor(getThemedColor(key_background));
            }
        }
    }""",
        """    private void updateColors(RecyclerView.ViewHolder holder) {
        if (holder.itemView instanceof Theme.Colorable) {
            ((Theme.Colorable) holder.itemView).updateColors();
            if (shouldApplyBackground(holder.getItemViewType())) {
                final int key_background = dialog ? Theme.key_dialogBackground : Theme.key_windowBackgroundWhite;
                holder.itemView.setBackgroundColor(getThemedColor(key_background));
            }
        }
        int type = holder.getItemViewType();
        if (nabdhGlassSettings && (type == VIEW_TYPE_TEXT_SETTINGS
                || type == VIEW_TYPE_TEXT || type == VIEW_TYPE_TEXT_CHECK
                || type == VIEW_TYPE_SWITCH || type == VIEW_TYPE_ICON_TEXT_CHECK)) {
            final int base = getThemedColor(Theme.key_windowBackgroundWhite);
            final int accent = getThemedColor(Theme.key_windowBackgroundWhiteBlueText);
            final int soft = android.graphics.Color.rgb(
                    (android.graphics.Color.red(base) * 88 + android.graphics.Color.red(accent) * 12) / 100,
                    (android.graphics.Color.green(base) * 88 + android.graphics.Color.green(accent) * 12) / 100,
                    (android.graphics.Color.blue(base) * 88 + android.graphics.Color.blue(accent) * 12) / 100);
            android.graphics.drawable.GradientDrawable surface =
                    new android.graphics.drawable.GradientDrawable();
            surface.setColor(soft);
            surface.setCornerRadius(AndroidUtilities.dp(16));
            surface.setStroke(Math.max(1, AndroidUtilities.dp(.65f)),
                    android.graphics.Color.argb(80, android.graphics.Color.red(accent),
                            android.graphics.Color.green(accent), android.graphics.Color.blue(accent)));
            android.graphics.drawable.Drawable inset =
                    new android.graphics.drawable.InsetDrawable(surface,
                            AndroidUtilities.dp(10), AndroidUtilities.dp(2),
                            AndroidUtilities.dp(10), AndroidUtilities.dp(2));
            holder.itemView.setBackground(new android.graphics.drawable.RippleDrawable(
                    android.content.res.ColorStateList.valueOf(
                            android.graphics.Color.argb(44, android.graphics.Color.red(accent),
                                    android.graphics.Color.green(accent), android.graphics.Color.blue(accent))),
                    inset, null));
        }
    }""",
        1
    ),
])
# onBindViewHolder may reset a native row's background after updateColors.
# Re-apply the scoped Settings surface after the row has finished binding;
# otherwise the screenshot remains Telegram's original flat white list.
modify("Components/UniversalAdapter.java", [
    (
        """        if (item.bind != null) {
            item.bind.run(holder.itemView);
        }
    }

    private View findViewByItemObject(Object object) {""",
        """        if (item.bind != null) {
            item.bind.run(holder.itemView);
        }
        if (nabdhGlassSettings) {
            updateColors(holder);
        }
    }

    private View findViewByItemObject(Object object) {""",
        1
    ),
])
modify("SettingsActivity.java", [
    (
        "        listView.adapter.setApplyBackground(false);",
        """        listView.adapter.setApplyBackground(false);
        // Only the main Telegram Settings uses these additional
        // theme-aware inset Glass rows.
        listView.adapter.setNabdhGlassSettings(true);""",
        1
    ),
])

# Soft filled surfaces for number/country and code containers WITHOUT adding
# a second stroke. The upstream OutlineTextContainerView still paints the
# native focus/validation line and accessibility/keyboard behavior.
modify("Components/OutlineTextContainerView.java", [
    (
        "    private final Paint outlinePaint = new Paint(Paint.ANTI_ALIAS_FLAG);",
        """    private final Paint outlinePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private boolean nabdhSoftGlass;
    private final Paint nabdhSoftFillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    public void setNabdhSoftGlass(boolean enabled) {
        nabdhSoftGlass = enabled;
        invalidate();
    }""",
        1
    ),
    (
        """    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        float textOffset =""",
        """    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (nabdhSoftGlass) {
            int base = Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider);
            int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, resourcesProvider);
            nabdhSoftFillPaint.setColor(android.graphics.Color.rgb(
                    (android.graphics.Color.red(base) * 94 + android.graphics.Color.red(accent) * 6) / 100,
                    (android.graphics.Color.green(base) * 94 + android.graphics.Color.green(accent) * 6) / 100,
                    (android.graphics.Color.blue(base) * 94 + android.graphics.Color.blue(accent) * 6) / 100));
            canvas.drawRoundRect(AndroidUtilities.dp(2), AndroidUtilities.dp(3),
                    getWidth() - AndroidUtilities.dp(2), getHeight() - AndroidUtilities.dp(3),
                    AndroidUtilities.dp(17), AndroidUtilities.dp(17), nabdhSoftFillPaint);
        }

        float textOffset =""",
        1
    ),
])
modify("LoginActivity.java", [
    (
        "countryOutlineView = new OutlineTextContainerView(context);",
        """countryOutlineView = new OutlineTextContainerView(context);
            countryOutlineView.setNabdhSoftGlass(true);""",
        1
    ),
    (
        "phoneOutlineView = new OutlineTextContainerView(context);",
        """phoneOutlineView = new OutlineTextContainerView(context);
            phoneOutlineView.setNabdhSoftGlass(true);""",
        1
    ),
    (
        "outlineCodeField = new OutlineTextContainerView(context);",
        """outlineCodeField = new OutlineTextContainerView(context);
            outlineCodeField.setNabdhSoftGlass(true);""",
        1
    ),
    (
        "codeFieldContainer = new CodeFieldContainer(context) {",
        """codeFieldContainer = new CodeFieldContainer(context) {""",
        4
    ),
])

# All ordinary TEXT bubble colors, not merely the rare gradient branch.
# The original Telegram shape/tail stays intact, and grouped media is left
# to native code. The subtle colored fill is applied BEFORE the text is drawn.
modify("ActionBar/MessageDrawable.java", [
    (
        """                background.draw(canvas);
                if ((currentType == TYPE_TEXT || currentType == TYPE_MEDIA) && !themePreview && !isSelected) {""",
        """                background.draw(canvas);
                if ((currentType == TYPE_TEXT || currentType == TYPE_MEDIA) && !themePreview && !isSelected) {
                    // Semi-transparent theme accent under the message glyphs:
                    // makes Glass visible for cached solid native bubbles too.
                    int tint = getColor(isOut
                            ? Theme.key_chat_outBubbleShadow : Theme.key_chat_inBubbleShadow);
                    if (Color.alpha(tint) < 20) {
                        tint = getColor(Theme.key_chat_messagePanelText);
                    }
                    nabdhBubbleEdge.setStyle(Paint.Style.FILL);
                    nabdhBubbleEdge.setColor(tint);
                    nabdhBubbleEdge.setAlpha((int) (42f * alpha / 255f));
                    canvas.drawPath(makePath(), nabdhBubbleEdge);""",
        1
    ),
    (
        "nabdhBubbleEdge.setAlpha((int) (53f * alpha / 255f));",
        "nabdhBubbleEdge.setAlpha((int) (118f * alpha / 255f));",
        1
    ),
])
print("NabdhGram v1: fixed RTL badge placement, native settings Glass, login input surfaces, solid chat bubbles.")
