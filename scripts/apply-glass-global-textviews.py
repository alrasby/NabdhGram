#!/usr/bin/env python3
"""Apply persisted font to native text labels in LaunchActivity without changing icons.

Updates visible TextViews after layout changes, tracking already processed views
with weak references. Explicit custom fonts, editable inputs, and icons are
left untouched. Throttled to protect long chat scrolling.
"""
from pathlib import Path
import sys
if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-global-textviews.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java"
s = p.read_text(encoding="utf-8")
anchor = """    @Override
    protected void onResume() {
        super.onResume();
        isResumed = true;"""
if s.count(anchor) != 1:
    raise SystemExit("LaunchActivity onResume anchor changed")
field_anchor = "    View feedbackView;\n"
if s.count(field_anchor) != 1:
    raise SystemExit("LaunchActivity field anchor changed")
fields = """    // NabdhGram: weak tracking avoids retaining recycled chat cells.
    private final java.util.WeakHashMap<android.widget.TextView, String> nabdhAppliedFonts =
            new java.util.WeakHashMap<>();
    private long nabdhFontLastScan;
    private android.view.ViewTreeObserver.OnGlobalLayoutListener nabdhFontLayoutListener;

    private void nabdhApplyVisibleFonts() {
        final android.view.View root = getWindow() == null ? null : getWindow().getDecorView();
        if (root == null) return;
        final String family = getSharedPreferences("nabdhgram_appearance", MODE_PRIVATE)
                .getString("font_family", "readex-pro");
        final java.util.ArrayDeque<android.view.View> pending = new java.util.ArrayDeque<>();
        pending.add(root);
        while (!pending.isEmpty()) {
            android.view.View view = pending.removeFirst();
            if (view instanceof android.widget.TextView && !(view instanceof android.widget.EditText)) {
                android.widget.TextView label = (android.widget.TextView) view;
                android.graphics.Typeface current = label.getTypeface();
                final String applied = nabdhAppliedFonts.get(label);
                final boolean normalFont = current == null
                        || current == android.graphics.Typeface.DEFAULT
                        || current == android.graphics.Typeface.DEFAULT_BOLD
                        || current == android.graphics.Typeface.SANS_SERIF
                        || current == android.graphics.Typeface.SERIF
                        || current == android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL);
                if (applied != null || normalFont) {
                    if (!family.equals(applied)) {
                        int style = current == null ? android.graphics.Typeface.NORMAL : current.getStyle();
                        android.graphics.Typeface base = "readex-pro".equals(family)
                                ? org.telegram.messenger.AndroidUtilities.getTypeface("fonts/ReadexPro.ttf")
                                : android.graphics.Typeface.create(family, android.graphics.Typeface.NORMAL);
                        if (base != null) {
                            label.setTypeface(base, style);
                            nabdhAppliedFonts.put(label, family);
                        }
                    }
                }
            }
            if (view instanceof android.view.ViewGroup) {
                android.view.ViewGroup group = (android.view.ViewGroup) view;
                for (int i = 0; i < group.getChildCount(); i++) {
                    pending.addLast(group.getChildAt(i));
                }
            }
        }
    }

"""
s = s.replace(field_anchor,field_anchor + fields,1)
replacement = """    @Override
    protected void onResume() {
        super.onResume();
        // Refresh after returning from Appearance and after a process restart.
        nabdhApplyVisibleFonts();
        if (nabdhFontLayoutListener == null) {
            nabdhFontLayoutListener = () -> {
                long now = android.os.SystemClock.uptimeMillis();
                if (now - nabdhFontLastScan >= 300) {
                    nabdhFontLastScan = now;
                    nabdhApplyVisibleFonts();
                }
            };
            getWindow().getDecorView().getViewTreeObserver()
                    .addOnGlobalLayoutListener(nabdhFontLayoutListener);
        }
        isResumed = true;"""
s = s.replace(anchor,replacement,1)
p.write_text(s,encoding="utf-8")
print("NabdhGram visible native labels now honor persisted font.")
