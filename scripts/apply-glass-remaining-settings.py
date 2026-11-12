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
     "holder.getItemViewType() == VIEW_TYPE_FILTER || holder.getItemViewType() == VIEW_TYPE_BUTTON || holder.getItemViewType() == VIEW_TYPE_CHECK",
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
        # setSections() draws an opaque group background behind the child
        # Glass cards; keep sections' adapter data but not those backgrounds.
        replacement = f"        // {label}: independent rounded Glass cards, not an opaque section."
    else:
        replacement = list_anchor
    s = require_replace(s, list_anchor,
        replacement + f"\n        listView.addItemDecoration(new {glass}());",
        f"{label}: RecyclerListView hook")
    adapter_start = s.index(marker)
    s = insert_at_method_end(s, adapter_start, condition, label)
    path.write_text(s, encoding="utf-8")
    print("Glass-covered:", name, "rows:", condition)
