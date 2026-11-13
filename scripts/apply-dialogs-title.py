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
    print("NabdhGram main dialogs title overlay applied.")

if __name__ == "__main__":
    main()
