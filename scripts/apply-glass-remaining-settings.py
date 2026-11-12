#!/usr/bin/env python3
"""Finish Glass coverage on Telegram folders and Lite Mode without changing data.

Runs after apply-glass-settings-surfaces.py has created the shared Glass
drawable. Opt in only individual interactive rows; never style folder editors,
headers, informational cells or the page background as a single giant card.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-remaining-settings.py TELEGRAM_SOURCE")
ui = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/ui"
glass = "org.telegram.ui.Components.NabdhGlassRowDecoration"

def require_replace(s, old, new, label):
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one source anchor, found {count}")
    return s.replace(old, new, 1)

def insert_at_method_end(s, after, condition, label):
    start = s.find("public void onBindViewHolder(", after)
    if start < 0:
        raise SystemExit(f"{label}: adapter binding method absent")
    begin = s.find("{", start)
    if begin < 0:
        raise SystemExit(f"{label}: method brace absent")
    depth, pos = 0, begin
    while pos < len(s):
        if s.startswith("//", pos):
            line_end = s.find("\n", pos)
            pos = len(s) if line_end < 0 else line_end
            continue
        if s.startswith("/*", pos):
            comment_end = s.find("*/", pos + 2)
            if comment_end < 0:
                raise SystemExit(f"{label}: unclosed comment")
            pos = comment_end + 2
            continue
        if s[pos] in ("'", '"'):
            quote = s[pos]
            pos += 1
            while pos < len(s):
                if s[pos] == "\\":
                    pos += 2
                elif s[pos] == quote:
                    pos += 1
                    break
                else:
                    pos += 1
            continue
        if s[pos] == "{":
            depth += 1
        elif s[pos] == "}":
            depth -= 1
            if depth == 0:
                break
        pos += 1
    if depth != 0 or pos >= len(s):
        raise SystemExit(f"{label}: Java method end not located")
    snippet = f"""
            // The shared Glass fill follows the native bind and does not
            // interfere with item data, navigation, drag/slider or editor state.
            if ({condition}) {{
                {glass}.applyCardStyle(holder.itemView, true);
            }}
"""
    return s[:pos] + snippet + s[pos:]

pages = [
    ("FiltersSetupActivity.java", "class ListAdapter extends",
     "holder.getItemViewType() == VIEW_TYPE_FILTER || holder.getItemViewType() == VIEW_TYPE_BUTTON || holder.getItemViewType() == VIEW_TYPE_CHECK || holder.getItemViewType() == VIEW_TYPE_FILTER_SUGGESTION",
     "        listView.setSections();", "folders list"),
    ("FilterCreateActivity.java", "class ListAdapter extends",
     "holder.getItemViewType() == VIEW_TYPE_CHAT || holder.getItemViewType() == VIEW_TYPE_BUTTON || holder.getItemViewType() == VIEW_TYPE_LINK || holder.getItemViewType() == VIEW_TYPE_CREATE_LINK",
     "        listView.setSections();", "folder edit options"),
    ("FilterChatlistActivity.java", "class ListAdapter extends",
     "holder.getItemViewType() == 3 || holder.getItemViewType() == 4",
     "        listView.setAdapter(adapter = new ListAdapter());", "shared folder chat list"),
    ("LiteModeSettingsActivity.java", "private class Adapter extends",
     "viewType == VIEW_TYPE_SWITCH || viewType == VIEW_TYPE_CHECKBOX || viewType == VIEW_TYPE_SWITCH2",
     "        listView.setSections();", "power saving toggles"),
]
for name, marker, condition, list_anchor, label in pages:
    path = ui / name
    s = path.read_text(encoding="utf-8")
    if s.count(marker) != 1:
        raise SystemExit(f"{label}: adapter type changed")
    if "setSections();" in list_anchor:
        # Preserve Telegram section offsets and grouping for folder drag and
        # accessibility; only the backdrop paint becomes independent Glass.
        replacement = list_anchor + "\n        listView.nabdhHideSectionBackgroundOnly();"
    else:
        replacement = list_anchor
    s = require_replace(s, list_anchor,
        replacement + f"\n        listView.addItemDecoration(new {glass}());",
        f"{label}: RecyclerListView hook")
    adapter_start = s.index(marker)
    s = insert_at_method_end(s, adapter_start, condition, label)
    path.write_text(s, encoding="utf-8")
    print("Glass-covered:", name, "rows:", condition)

# Telegram's Chat Settings page contains custom preview widgets, sliders and
# row selectors that the generic Text*Cell whitelist never reaches. Decorate
# the actual bind results while leaving horizontal theme previews intact.
theme = ui / "ThemeActivity.java"
theme_src = theme.read_text(encoding="utf-8")
theme_marker = "private class ListAdapter extends RecyclerListView.SelectionAdapter"
if theme_src.count(theme_marker) != 1:
    raise SystemExit("ThemeActivity list adapter anchor changed")
theme_cond = ("holder.getItemViewType() == TYPE_TEXT_SIZE"
              " || holder.getItemViewType() == TYPE_CHAT_LIST"
              " || holder.getItemViewType() == TYPE_BUBBLE_RADIUS"
              " || holder.getItemViewType() == TYPE_SWIPE_GESTURE"
              " || holder.getItemViewType() == TYPE_THEME_TYPE"
              " || holder.getItemViewType() == TYPE_NIGHT_THEME"
              " || holder.getItemViewType() == TYPE_TEXT_PREFERENCE"
              " || holder.getItemViewType() == TYPE_TEXT_SETTING"
              " || holder.getItemViewType() == TYPE_TEXT_CHECK")
theme_src = insert_at_method_end(theme_src, theme_src.index(theme_marker),
                                  theme_cond, "chat appearance special controls")
# The Telegram-native chat preview is an independent wallpaper drawing
# (ThemePreviewMessagesCell.onDraw). It is NOT a normal Glass list row.
# Inset its layout to the other card edges and clip its actual canvas and
# descendants to 20dp corners without disturbing message touch gestures.
preview_anchor = """                    view = messagesCell;
                    break;"""
preview_style = """                    android.view.ViewGroup.LayoutParams existingPreviewParams =
                            messagesCell.getLayoutParams();
                    RecyclerView.LayoutParams glassPreviewParams =
                            new RecyclerView.LayoutParams(
                                    ViewGroup.LayoutParams.MATCH_PARENT,
                                    ViewGroup.LayoutParams.WRAP_CONTENT);
                    glassPreviewParams.leftMargin = AndroidUtilities.dp(10);
                    glassPreviewParams.rightMargin = AndroidUtilities.dp(10);
                    messagesCell.setLayoutParams(glassPreviewParams);
                    messagesCell.setOutlineProvider(new android.view.ViewOutlineProvider() {
                        @Override
                        public void getOutline(View view, android.graphics.Outline outline) {
                            outline.setRoundRect(0, 0, view.getWidth(), view.getHeight(),
                                    AndroidUtilities.dp(20));
                        }
                    });
                    messagesCell.setClipToOutline(true);
                    view = messagesCell;
                    break;"""
if theme_src.count(preview_anchor) != 1:
    raise SystemExit("Telegram ThemeActivity preview view constructor changed")
theme_src = theme_src.replace(preview_anchor, preview_style, 1)
theme.write_text(theme_src, encoding="utf-8")
print("Glass-covered: ThemeActivity custom chat settings controls")
