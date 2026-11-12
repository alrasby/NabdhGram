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
        super.onResume();"""
if s.count(anchor) != 1:
    raise SystemExit("LaunchActivity onResume anchor changed")
field_anchor = "    View feedbackView;\n"
if s.count(field_anchor) != 1:
    raise SystemExit("LaunchActivity field anchor changed")
fields = """    // NabdhGram: weak tracking avoids retaining recycled chat cells.
    private final java.util.WeakHashMap<android.widget.TextView, String> nabdhAppliedFonts =
            new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<android.widget.TextView, Float> nabdhOriginalTextSizes =
            new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<android.widget.TextView, Integer> nabdhOriginalTextStyles =
            new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<android.widget.TextView, android.graphics.Typeface> nabdhOriginalTypefaces =
            new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<org.telegram.ui.Components.AnimatedTextView, String> nabdhAnimatedAppliedFonts =
            new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<org.telegram.ui.Components.AnimatedTextView, Float> nabdhAnimatedOriginalPx =
            new java.util.WeakHashMap<>();
    private final java.util.WeakHashMap<org.telegram.ui.Components.AnimatedTextView, Integer> nabdhAnimatedOriginalStyles =
            new java.util.WeakHashMap<>();
    private boolean nabdhFontApplying;
    private boolean nabdhFontDirty = true;
    private boolean nabdhRowRefreshPending;
    // Avoid a full view-tree scan on every animated RecyclerView layout frame.
    private long nabdhLastFontScanMs;
    private android.view.ViewTreeObserver.OnGlobalLayoutListener nabdhFontLayoutListener;
    private android.view.ViewTreeObserver.OnPreDrawListener nabdhFontPreDrawListener;

    // Appearance is a Telegram fragment; returning to it does not restart
    // LaunchActivity. Allow explicit refresh within the same Activity.
    public void nabdhRefreshAllFonts() {
        nabdhFontDirty = true;
        nabdhApplyVisibleFonts();
        android.view.View decor = getWindow() == null ? null : getWindow().getDecorView();
        if (decor != null) {
            // A number of Telegram labels (DialogCell, ChatMessageCell and
            // SimpleTextView) use cached StaticLayouts rather than TextViews.
            // Rebind their visible RecyclerView rows once on an explicit font
            // choice, retaining existing adapters and scroll position.
            if (nabdhRowRefreshPending) return;
            nabdhRowRefreshPending = true;
            decor.post(() -> {
                nabdhRowRefreshPending = false;
                java.util.ArrayDeque<android.view.View> pending = new java.util.ArrayDeque<>();
                pending.add(decor);
                while (!pending.isEmpty()) {
                    android.view.View view = pending.removeFirst();
                    if (view instanceof androidx.recyclerview.widget.RecyclerView) {
                        androidx.recyclerview.widget.RecyclerView list =
                                (androidx.recyclerview.widget.RecyclerView) view;
                        androidx.recyclerview.widget.RecyclerView.Adapter adapter =
                                list.getAdapter();
                        if (adapter != null && !list.isComputingLayout()) {
                            int first = 0;
                            int count = adapter.getItemCount();
                            androidx.recyclerview.widget.RecyclerView.LayoutManager manager =
                                    list.getLayoutManager();
                            if (manager instanceof androidx.recyclerview.widget.LinearLayoutManager) {
                                androidx.recyclerview.widget.LinearLayoutManager linear =
                                        (androidx.recyclerview.widget.LinearLayoutManager) manager;
                                int last = linear.findLastVisibleItemPosition();
                                first = Math.max(0, linear.findFirstVisibleItemPosition());
                                if (last >= first && first < count) {
                                    count = Math.min(count - first, last - first + 1);
                                } else {
                                    count = 0;
                                }
                            }
                            if (count > 0) {
                                // Only visible rows need an immediate typography
                                // rebuild; recycled rows rebind naturally later.
                                adapter.notifyItemRangeChanged(first, count);
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
                nabdhFontDirty = true;
                nabdhApplyVisibleFonts();
                // Invalidate the native canvas-backed labels for this visible
                // frame; never call notifyDataSetChanged on the entire chat.
                decor.requestLayout();
                decor.invalidate();
            });
        }
    }

    private void nabdhApplyVisibleFonts() {
        final android.view.View root = getWindow() == null ? null : getWindow().getDecorView();
        if (root == null || nabdhFontApplying) return;
        nabdhFontApplying = true;
        nabdhLastFontScanMs = android.os.SystemClock.uptimeMillis();
        try {
        android.content.SharedPreferences appearance =
                getSharedPreferences("nabdhgram_appearance", MODE_PRIVATE);
        final String family = appearance.getString("font_family", "system-default");
        final int uiPercent = Math.max(85, Math.min(115,
                appearance.getInt("ui_scale_percent", 100)));
        final boolean forceBold = appearance.getBoolean("font_bold", false);
        final String renderKey = family + ":" + uiPercent + ":" + forceBold;
        // Resolve packaged faces once per layout pass, never per row/glyph.
        final java.util.HashSet<android.graphics.Typeface> packagedTextFaces =
                new java.util.HashSet<>();
        for (String filename : new String[]{"ReadexPro.ttf", "Vazirmatn.ttf",
                "NotoSansArabic.ttf", "Tajawal.ttf", "Rubik.ttf"}) {
            android.graphics.Typeface face =
                    org.telegram.messenger.AndroidUtilities.getTypeface("fonts/" + filename);
            if (face != null) {
                packagedTextFaces.add(face);
                packagedTextFaces.add(android.graphics.Typeface.create(face,
                        android.graphics.Typeface.NORMAL));
                packagedTextFaces.add(android.graphics.Typeface.create(face,
                        android.graphics.Typeface.BOLD));
            }
        }
        final java.util.ArrayDeque<android.view.View> pending = new java.util.ArrayDeque<>();
        pending.add(root);
        while (!pending.isEmpty()) {
            android.view.View view = pending.removeFirst();
            if (view instanceof org.telegram.ui.ActionBar.SimpleTextView) {
                ((org.telegram.ui.ActionBar.SimpleTextView) view).nabdhRefreshSelectedFont();
            }
            // Telegram's animated settings/headers use a custom drawable and
            // are invisible to a normal TextView scan. Rebuild their cached
            // text layouts when the selected font/size actually changes.
            if (view instanceof org.telegram.ui.Components.AnimatedTextView) {
                org.telegram.ui.Components.AnimatedTextView animated =
                        (org.telegram.ui.Components.AnimatedTextView) view;
                android.graphics.Typeface current = animated.getPaint().getTypeface();
                String applied = nabdhAnimatedAppliedFonts.get(animated);
                boolean eligible = applied != null || current == null
                        || current.equals(android.graphics.Typeface.DEFAULT)
                        || current.equals(android.graphics.Typeface.DEFAULT_BOLD)
                        || current.equals(android.graphics.Typeface.SANS_SERIF)
                        || current.equals(android.graphics.Typeface.create(
                                "sans-serif-medium", android.graphics.Typeface.NORMAL))
                        || current.equals(org.telegram.messenger.AndroidUtilities.getTypeface(
                                "fonts/rregular.ttf"))
                        || current.equals(org.telegram.messenger.AndroidUtilities.getTypeface(
                                "fonts/rmedium.ttf"))
                        || packagedTextFaces.contains(current);
                if (eligible && !renderKey.equals(applied)) {
                    Float original = nabdhAnimatedOriginalPx.get(animated);
                    if (original == null) {
                        original = animated.getPaint().getTextSize();
                        nabdhAnimatedOriginalPx.put(animated, original);
                        nabdhAnimatedOriginalStyles.put(animated,
                                current == null ? android.graphics.Typeface.NORMAL : current.getStyle());
                    }
                    boolean device = "system-default".equals(family);
                    Integer originalStyle = nabdhAnimatedOriginalStyles.get(animated);
                    android.graphics.Typeface desired = device
                            ? android.graphics.Typeface.create(
                                    android.graphics.Typeface.DEFAULT,
                                    forceBold || originalStyle != null
                                    && originalStyle == android.graphics.Typeface.BOLD
                                    ? android.graphics.Typeface.BOLD
                                    : android.graphics.Typeface.NORMAL)
                            : org.telegram.messenger.AndroidUtilities.getTypeface(
                                    (forceBold || originalStyle != null
                                    && (originalStyle & android.graphics.Typeface.BOLD) != 0)
                                    ? "fonts/rmedium.ttf" : "fonts/rregular.ttf");
                    if (desired != null) animated.setTypeface(desired);
                    animated.setTextSize(original * uiPercent / 100f);
                    animated.setText(animated.getText(), false);
                    animated.requestLayout();
                    animated.invalidate();
                    nabdhAnimatedAppliedFonts.put(animated, renderKey);
                }
            }
            if (view instanceof android.widget.TextView && !(view instanceof android.widget.EditText)) {
                android.widget.TextView label = (android.widget.TextView) view;
                android.graphics.Typeface current = label.getTypeface();
                final String applied = nabdhAppliedFonts.get(label);
                // Telegram labels may use different weights of the system
                // sans family. Match their actual family rather than relying
                // on Typeface object identity, which is not guaranteed.
                // Telegram already assigns the selected bundled typeface to
                // many views before this scanner sees them. Treat those native
                // text faces as eligible so UI scaling and future changes work.
                // Include any previously selected packaged family too.
                // Otherwise switching Readex -> Vazirmatn leaves stale custom
                // label typefaces until the Activity is recreated.
                final boolean previouslyChosen = current != null
                        && packagedTextFaces.contains(current);
                final boolean telegramTextFace = previouslyChosen || current != null && (
                        current.equals(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rregular.ttf"))
                        || current.equals(org.telegram.messenger.AndroidUtilities.getTypeface("fonts/rmedium.ttf")));
                final boolean normalFont = telegramTextFace || current == null
                        || current.equals(android.graphics.Typeface.DEFAULT)
                        || current.equals(android.graphics.Typeface.DEFAULT_BOLD)
                        || current.equals(android.graphics.Typeface.SANS_SERIF)
                        || current.equals(android.graphics.Typeface.SERIF)
                        || current.equals(android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL))
                        || current.equals(android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.BOLD));
                if (applied != null || normalFont) {
                    if (!renderKey.equals(applied)) {
                        Integer originalStyle = nabdhOriginalTextStyles.get(label);
                        if (originalStyle == null) {
                            originalStyle = current == null
                                    ? android.graphics.Typeface.NORMAL : current.getStyle();
                            nabdhOriginalTextStyles.put(label, originalStyle);
                            // A Telegram Roboto alias may already resolve to
                            // the user-selected font. Never save that custom
                            // face as the device default: it would survive a reset.
                            nabdhOriginalTypefaces.put(label,
                                    telegramTextFace ? android.graphics.Typeface.DEFAULT
                                    : current == null ? android.graphics.Typeface.DEFAULT : current);
                        }
                        Float originalPx = nabdhOriginalTextSizes.get(label);
                        if (originalPx == null) {
                            originalPx = label.getTextSize();
                            nabdhOriginalTextSizes.put(label, originalPx);
                        }
                        String fontFile = "readex-pro".equals(family) ? "ReadexPro.ttf"
                                : "vazirmatn".equals(family) ? "Vazirmatn.ttf"
                                : "noto-sans-arabic".equals(family) ? "NotoSansArabic.ttf"
                                : "tajawal".equals(family) ? "Tajawal.ttf"
                                : "rubik".equals(family) ? "Rubik.ttf" : null;
                        boolean deviceDefault = "system-default".equals(family);
                        android.graphics.Typeface base = deviceDefault
                                ? nabdhOriginalTypefaces.get(label)
                                : fontFile == null
                                    ? android.graphics.Typeface.create(family, android.graphics.Typeface.NORMAL)
                                    : org.telegram.messenger.AndroidUtilities.getTypeface("fonts/" + fontFile);
                        if (base != null && (!deviceDefault || applied != null || forceBold || uiPercent != 100)) {
                            // Optional typefaces start Regular; returning to
                            // Device font restores this native TextView style.
                            label.setTypeface(base,
                                    forceBold ? android.graphics.Typeface.BOLD : originalStyle);
                            float sizePx = originalPx * uiPercent / 100f;
                            if (Math.abs(label.getTextSize() - sizePx) > 0.5f) {
                                label.setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX, sizePx);
                            }
                            nabdhAppliedFonts.put(label, renderKey);
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
        } finally {
            nabdhFontApplying = false;
        }
    }

"""
s = s.replace(field_anchor,field_anchor + fields,1)
replacement = """    @Override
    protected void onResume() {
        super.onResume();
        // Refresh after returning from Appearance and after a process restart.
        nabdhFontDirty = true;
        nabdhApplyVisibleFonts();
        // Run before each visible frame: newly created rows and settings labels
        // receive their font before pixels are drawn, avoiding delayed swaps.
        // Already processed labels are skipped by the weak cache.
        if (nabdhFontPreDrawListener == null) {
            nabdhFontPreDrawListener = () -> {
                if (nabdhFontDirty && android.os.SystemClock.uptimeMillis()
                        - nabdhLastFontScanMs >= 48L) {
                    nabdhFontDirty = false;
                    nabdhApplyVisibleFonts();
                }
                return true;
            };
            getWindow().getDecorView().getViewTreeObserver()
                    .addOnPreDrawListener(nabdhFontPreDrawListener);
            nabdhFontLayoutListener = () -> nabdhFontDirty = true;
            getWindow().getDecorView().getViewTreeObserver()
                    .addOnGlobalLayoutListener(nabdhFontLayoutListener);
        }
"""
s = s.replace(anchor,replacement,1)
p.write_text(s,encoding="utf-8")
print("NabdhGram visible native labels now honor persisted font.")
