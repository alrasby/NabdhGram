#!/usr/bin/env python3
"""Synchronize visible custom-drawn Telegram text after a font preference change.

Runs after apply-glass-global-textviews.py and before the finishing overlays.
No Activity restart or changes to accounts, navigation, media or networking.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-live-typography.py TELEGRAM_SOURCE")
ui = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"
launch = ui / "LaunchActivity.java"
s = launch.read_text(encoding="utf-8")

def replace_once(s, old, new, label):
    if s.count(old) != 1:
        raise SystemExit(f"{label}: expected one anchor, got {s.count(old)}")
    return s.replace(old, new, 1)

s = replace_once(s, "    private boolean nabdhFontApplying;", """    private final java.util.WeakHashMap<org.telegram.ui.ActionBar.SimpleTextView, String>
            nabdhCustomFontKeys = new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<org.telegram.ui.ActionBar.SimpleTextView, Float>
            nabdhCustomOriginalSizes = new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<org.telegram.ui.ActionBar.SimpleTextView, android.graphics.Typeface>
            nabdhCustomOriginalFaces = new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<org.telegram.ui.Cells.DialogCell, String>
            nabdhDialogFontKeys = new java.util.WeakHashMap<>();
    private boolean nabdhFontApplying;""", "LaunchActivity typography fields")

anchor = """            if (view instanceof android.view.ViewGroup) {
                android.view.ViewGroup group = (android.view.ViewGroup) view;"""
injection = """            // Names and action-bar labels are custom Canvas widgets, not TextViews.
            if (view instanceof org.telegram.ui.ActionBar.SimpleTextView) {
                org.telegram.ui.ActionBar.SimpleTextView custom =
                        (org.telegram.ui.ActionBar.SimpleTextView) view;
                android.graphics.Typeface existing = custom.getPaint().getTypeface();
                String previous = nabdhCustomFontKeys.get(custom);
                boolean nativeText = existing == null
                        || existing.equals(android.graphics.Typeface.DEFAULT)
                        || existing.equals(android.graphics.Typeface.DEFAULT_BOLD)
                        || existing.equals(android.graphics.Typeface.SANS_SERIF)
                        || existing.equals(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rregular.ttf"))
                        || existing.equals(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rmedium.ttf"));
                if ((previous != null || nativeText) && !renderKey.equals(previous)) {
                    if (!nabdhCustomOriginalSizes.containsKey(custom)) {
                        nabdhCustomOriginalSizes.put(custom, custom.getPaint().getTextSize());
                        nabdhCustomOriginalFaces.put(custom,
                                existing == null || existing.equals(
                                        org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rregular.ttf"))
                                        || existing.equals(
                                        org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rmedium.ttf"))
                                        ? android.graphics.Typeface.DEFAULT : existing);
                    }
                    android.graphics.Typeface selected = null;
                    if ("system-default".equals(family)) {
                        selected = nabdhCustomOriginalFaces.get(custom);
                    } else if ("sans-serif".equals(family) || "serif".equals(family)) {
                        selected = android.graphics.Typeface.create(family,
                                android.graphics.Typeface.NORMAL);
                    } else {
                        String asset = "vazirmatn".equals(family) ? "Vazirmatn.ttf"
                                : "noto-sans-arabic".equals(family) ? "NotoSansArabic.ttf"
                                : "tajawal".equals(family) ? "Tajawal.ttf"
                                : "rubik".equals(family) ? "Rubik.ttf" : "ReadexPro.ttf";
                        selected = org.telegram.messenger.AndroidUtilities.getTypeface("fonts/" + asset);
                    }
                    if (selected != null) {
                        custom.setTypeface(android.graphics.Typeface.create(selected,
                                forceBold ? android.graphics.Typeface.BOLD
                                        : android.graphics.Typeface.NORMAL));
                        Float originalSize = nabdhCustomOriginalSizes.get(custom);
                        if (originalSize != null) {
                            custom.setTextSizePx(Math.round(originalSize * uiPercent / 100f));
                        }
                        nabdhCustomFontKeys.put(custom, renderKey);
                        custom.requestLayout();
                        custom.invalidate();
                    }
                }
            }
            // DialogCell caches StaticLayouts separately from global paint.
            // Font switches must remeasure their name, badge and preview bounds.
            if (view instanceof org.telegram.ui.Cells.DialogCell) {
                org.telegram.ui.Cells.DialogCell dialog = (org.telegram.ui.Cells.DialogCell) view;
                if (!renderKey.equals(nabdhDialogFontKeys.get(dialog))) {
                    nabdhDialogFontKeys.put(dialog, renderKey);
                    dialog.nabdhRemeasureTypography();
                }
            }
"""
s = replace_once(s, anchor, injection + anchor, "LaunchActivity custom view traversal")
launch.write_text(s, encoding="utf-8")

p = ui / "ActionBar/SimpleTextView.java"
s = p.read_text(encoding="utf-8")
s = replace_once(s, """    public void setTypeface(Typeface typeface) {
        textPaint.setTypeface(typeface);
    }""", """    public void setTypeface(Typeface typeface) {
        if (textPaint.getTypeface() != typeface) {
            textPaint.setTypeface(typeface);
            // Text changes dimensions with Arabic and Latin variable fonts.
            // Never reuse the previous text layout after a family switch.
            recreateLayoutMaybe();
            requestLayout();
            invalidate();
        }
    }""", "SimpleTextView text-layout refresh")
p.write_text(s, encoding="utf-8")

p = ui / "Cells/DialogCell.java"
s = p.read_text(encoding="utf-8")
s = replace_once(s, "    public void buildLayout() {", """    private boolean nabdhTypographyChanged;

    public void nabdhRemeasureTypography() {
        nabdhTypographyChanged = true;
        requestLayout();
        invalidate();
    }

    public void buildLayout() {""", "DialogCell invalidation hook")
s = replace_once(s,
    """            if (!needUpdate && currentDialogFolderId == 0 && currentDialogCommunityId == 0 && encryptedChat == null) {
                return;
            }
        }

        if (useForceThreeLines""",
    """            if (!needUpdate && !nabdhTypographyChanged
                    && currentDialogFolderId == 0 && currentDialogCommunityId == 0
                    && encryptedChat == null) {
                return;
            }
        }
        nabdhTypographyChanged = false;

        if (useForceThreeLines""", "DialogCell forced remeasure")
p.write_text(s, encoding="utf-8")
print("Applied immediate font re-layout for visible native/custom Canvas labels and dialogs.")
