#!/usr/bin/env python3
"""NabdhGram Glass: draw chat row cards and brand the native phone-login page.

A narrow overlay on pinned Telegram v13.1.1 Android Java sources. No
navigation, dialog ordering, account, auth, network or message semantics change.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-core-ui.py TELEGRAM_SOURCE")

root = Path(sys.argv[1])
cell = root / "TMessagesProj/src/main/java/org/telegram/ui/Cells/DialogCell.java"
login = root / "TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java"

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected one anchor, found {n}")
    return text.replace(old, new, 1)

s = cell.read_text(encoding="utf-8")
# Keep cached Paint/RectF objects: do not allocate on every scrolling frame.
anchor = "    private boolean isSelected;\n"
s = replace_once(s, anchor, anchor + """
    // NabdhGram Glass: cached row decoration to avoid per-frame allocations.
    private final Paint nabdhGlassFill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint nabdhGlassStroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF nabdhGlassBounds = new RectF();
""", "DialogCell paint fields")
anchor = """        if (!visibleOnScreen) {
            return;
        }

        boolean needInvalidate = false;"""
patch = """        if (!visibleOnScreen) {
            return;
        }

        // One native row per chat: pinned chats have their own cyan-tinted
        // card treatment, standard chats a subtler card, selection a bright
        // accent. Do not consume touches or replace Telegram's row actions.
        if (currentDialogFolderId == 0 && translationX == 0 && rightFragmentOpenedProgress == 0) {
            final int surface = Theme.getColor(Theme.key_windowBackgroundWhite, resourcesProvider);
            final boolean darkSurface = Color.red(surface) + Color.green(surface) + Color.blue(surface) < 360;
            final boolean pinnedGlass = getIsPinned() || drawPinBackground;
            final int fill = isSelected ? (darkSurface ? 0xFF086A70 : 0xFFD2F3F0)
                    : pinnedGlass ? (darkSurface ? 0xFF103D45 : 0xFFE5F6F4)
                    : (darkSurface ? 0xFF162B36 : 0xFFF9FDFD);
            final int stroke = isSelected ? 0xFF20C8C1
                    : pinnedGlass ? (darkSurface ? 0xFF208F95 : 0xFF9CDDD9)
                    : (darkSurface ? 0xFF27515B : 0xFFDDECEB);
            final float insetX = dp(7);
            final float insetY = dp(3);
            final float round = dp(19);
            nabdhGlassBounds.set(insetX, insetY, getMeasuredWidth() - insetX,
                    getMeasuredHeight() - insetY);
            nabdhGlassFill.setColor(fill);
            nabdhGlassFill.setStyle(Paint.Style.FILL);
            canvas.drawRoundRect(nabdhGlassBounds, round, round, nabdhGlassFill);
            nabdhGlassStroke.setColor(stroke);
            nabdhGlassStroke.setStyle(Paint.Style.STROKE);
            nabdhGlassStroke.setStrokeWidth(dp(1));
            canvas.drawRoundRect(nabdhGlassBounds, round, round, nabdhGlassStroke);
        }

        boolean needInvalidate = false;"""
s = replace_once(s, anchor, patch, "DialogCell draw entry")
cell.write_text(s, encoding="utf-8")

s = login.read_text(encoding="utf-8")
anchor = """            setOrientation(VERTICAL);
            setGravity(Gravity.CENTER);

            titleView = new TextView(context);"""
replacement = """            setOrientation(VERTICAL);
            setGravity(Gravity.CENTER);

            // NabdhGram identity on the official phone-auth step. Keep all
            // Telegram verification fields and supported code flows unchanged.
            TextView nabdhBrand = new TextView(context);
            nabdhBrand.setText("NabdhGram");
            nabdhBrand.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 30);
            nabdhBrand.setTypeface(AndroidUtilities.bold());
            nabdhBrand.setTextColor(0xFF11AAA9);
            nabdhBrand.setGravity(Gravity.CENTER);
            addView(nabdhBrand, LayoutHelper.createLinear(
                    LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT,
                    Gravity.CENTER_HORIZONTAL, 24, 0, 24, 20));

            titleView = new TextView(context);"""
s = replace_once(s, anchor, replacement, "Login phone-page brand")
login.write_text(s, encoding="utf-8")
# A real contiguous group behind pinned rows, without changing the adapter's
# data order, list item type, click targets, swipe actions or scroll recycling.
dialogs = root / "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java"
s = dialogs.read_text(encoding="utf-8")
anchor = "            viewPage.listView.setClipToPadding(false);"
group = """            viewPage.listView.setClipToPadding(false);
            // NabdhGram Glass: visually separate the currently visible pinned
            // block. Draw behind rows; no overlay intercepts user gestures.
            viewPage.listView.addItemDecoration(new RecyclerView.ItemDecoration() {
                private final Paint glassGroupFill = new Paint(Paint.ANTI_ALIAS_FLAG);
                private final Paint glassGroupStroke = new Paint(Paint.ANTI_ALIAS_FLAG);
                private final RectF glassGroupBounds = new RectF();

                @Override
                public void onDraw(Canvas canvas, RecyclerView parent, RecyclerView.State state) {
                    float first = Float.MAX_VALUE;
                    float last = -Float.MAX_VALUE;
                    boolean started = false;
                    for (int i = 0; i < parent.getChildCount(); i++) {
                        View child = parent.getChildAt(i);
                        if (!(child instanceof DialogCell) || !((DialogCell) child).getIsPinned()) {
                            if (started) break;
                            continue;
                        }
                        started = true;
                        float y = child.getTranslationY();
                        first = Math.min(first, child.getTop() + y);
                        last = Math.max(last, child.getBottom() + y);
                    }
                    if (!started || last <= first) return;
                    int base = Theme.getColor(Theme.key_windowBackgroundWhite);
                    boolean dark = Color.red(base) + Color.green(base) + Color.blue(base) < 360;
                    glassGroupBounds.set(dp(2), first, parent.getWidth() - dp(2), last);
                    glassGroupFill.setColor(dark ? 0xFF082D35 : 0xFFDDF3F2);
                    glassGroupFill.setStyle(Paint.Style.FILL);
                    canvas.drawRoundRect(glassGroupBounds, dp(24), dp(24), glassGroupFill);
                    glassGroupStroke.setColor(dark ? 0xFF1D8589 : 0xFF9AD7D4);
                    glassGroupStroke.setStyle(Paint.Style.STROKE);
                    glassGroupStroke.setStrokeWidth(dp(1));
                    canvas.drawRoundRect(glassGroupBounds, dp(24), dp(24), glassGroupStroke);
                }
            });"""
s = replace_once(s, anchor, group, "DialogsActivity pinned group")
dialogs.write_text(s, encoding="utf-8")
print("Installed NabdhGram Glass grouped pinned chats, chat cards and official login branding.")
