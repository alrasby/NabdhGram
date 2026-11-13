#!/usr/bin/env python3
"""Brand the main dialogs title without touching Telegram networking or chat UI."""
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-dialogs-title.py TELEGRAM_SOURCE")
    p = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java"
    s = p.read_text(encoding="utf-8")
    old = """                SpannableStringBuilder ssb = new SpannableStringBuilder(getString(R.string.AppName));
                ssb.setSpan(new ImageSpan(logoDrawable), 0, ssb.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                actionBar.setTitle(ssb, statusDrawable);"""
    new = """                // NabdhGram: keep upstream status drawable but show the approved app name
                // instead of the Telegram glyph embedded in the AppName text span.
                actionBar.setTitle("NabdhGram", statusDrawable);"""
    if s.count(old) != 1:
        raise SystemExit(f"Expected one pinned dialogs title anchor; found {s.count(old)}")
    s = s.replace(old, new, 1)
    # The main list resumes after navigation, language and theme changes.
    # Restrict the title guard to main chats (never archive/search/share).
    resume = "    public void onResume() {\n        super.onResume();"
    guard = """    public void onResume() {
        super.onResume();
        if (initialDialogsType == DIALOGS_TYPE_DEFAULT && !onlySelect
                && folderId == 0 && communityId == 0
                && TextUtils.isEmpty(searchString) && actionBar != null
                && statusDrawable != null) {
            actionBar.setTitle("NabdhGram", statusDrawable);
        }"""
    if s.count(resume) != 1:
        raise SystemExit("DialogsActivity resume title anchor changed")
    s = s.replace(resume, guard, 1)
    p.write_text(s, encoding="utf-8")
    # Telegram 13.2 runs DialogsActivity inside a recycled MainTabsActivity
    # pager. Changing only DialogsActivity.createView/onResume did not fix
    # the visible chats title in the real #566 video. Guard the host tab
    # selection and host resume too, without touching search, archive,
    # share-picker or other Telegram application names.
    tabs = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram/ui/MainTabsActivity.java"
    main_tabs = tabs.read_text(encoding="utf-8")
    select_anchor = """    public void selectTab(int position, boolean animated) {
        for (int a = 0; a < tabs.length; a++) {
            GlassTabView tab = tabs[a];
            tab.setSelected(indexToPosition(a) == position, animated);
        }
    }"""
    select_replacement = """    public void selectTab(int position, boolean animated) {
        for (int a = 0; a < tabs.length; a++) {
            GlassTabView tab = tabs[a];
            tab.setSelected(indexToPosition(a) == position, animated);
        }
        if (position == POSITION_CHATS) nabdhRestoreChatTitle();
    }

    private void nabdhRestoreChatTitle() {
        if (dialogsActivity != null && dialogsActivity.getActionBar() != null) {
            org.telegram.ui.ActionBar.ActionBar bar = dialogsActivity.getActionBar();
            org.telegram.ui.ActionBar.SimpleTextView currentTitle = bar.getTitleTextView();
            // setTitle(value) clears Telegram's emoji-status right drawable.
            // Preserve it to avoid regressing Premium/status controls.
            bar.setTitle("NabdhGram", currentTitle == null
                    ? null : currentTitle.getRightDrawable());
        }
    }"""
    if main_tabs.count(select_anchor) != 1:
        raise SystemExit("Telegram main-tabs title ownership anchor changed")
    main_tabs = main_tabs.replace(select_anchor, select_replacement, 1)
    resume_anchor = """    public void onResume() {
        super.onResume();
        blur3_updateColors();"""
    if main_tabs.count(resume_anchor) != 1:
        raise SystemExit("MainTabsActivity resume title anchor changed")
    main_tabs = main_tabs.replace(resume_anchor, """    public void onResume() {
        super.onResume();
        // The host can reuse an older chat ActionBar on process resume.
        if (viewPager != null && viewPager.getCurrentPosition() == POSITION_CHATS) {
            nabdhRestoreChatTitle();
        }
        blur3_updateColors();""", 1)
    tabs.write_text(main_tabs, encoding="utf-8")
    print("NabdhGram main dialogs and main-tabs host title overlays applied.")

if __name__ == "__main__":
    main()
