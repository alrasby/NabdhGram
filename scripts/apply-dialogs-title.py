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
    # Preserve the full-size, user-centered NabdhGram ActionBar title when
    # stories are fully expanded. Telegram normally scales this native text
    # container down to ~40% opacity/size while hiding its own image wordmark;
    # that is why #759 showed a miniature NabdhGram above the story circles.
    fade_end = """        }
    }

    public static float viewOffset = 0.0f;"""
    if s.count(fade_end) != 1:
        raise SystemExit("Telegram stories/action-bar fade anchor changed")
    s = s.replace(fade_end, """        }
        if (initialDialogsType == DIALOGS_TYPE_DEFAULT && !onlySelect
                && folderId == 0 && communityId == 0 && actionBar != null
                && !actionBar.isActionModeShowed()
                && searchAnimationProgress < 0.01f) {
            // Keep ONE real ActionBar title through every stories animation
            // frame. The previous isFullExpanded() check left an entire
            // transition window with BOTH native titles faded out.
            actionBar.getTitlesContainer().setScaleX(1f);
            actionBar.getTitlesContainer().setScaleY(1f);
            actionBar.getTitlesContainer().setAlpha(1f);
            actionBar.getTitlesContainer().setVisibility(View.VISIBLE);
        }
    }

    public static float viewOffset = 0.0f;""", 1)

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

    # Telegram 13.2.2 has a SECOND independently drawn home logo:
    # DialogStoriesCell renders the native Telegram wordmark when stories
    # collapse. Changing DialogsActivity's ActionBar alone leaves that logo
    # untouched and yields a tiny NabdhGram ActionBar title while stories expand.
    stories = Path(sys.argv[1]).resolve() / (
        "TMessagesProj/src/main/java/org/telegram/ui/Stories/DialogStoriesCell.java"
    )
    story = stories.read_text(encoding="utf-8")

    def story_once(before, after, label):
        if story.count(before) != 1:
            raise SystemExit(f"Telegram stories {label} anchor changed: {story.count(before)}")
        return story.replace(before, after, 1)

    story = story_once(
        "    ImageView telegramLogoView;",
        "    TextView telegramLogoView;",
        "wordmark type"
    )
    story = story_once(
        """        telegramLogoView = new ImageView(context);
        telegramLogoView.setContentDescription(getString(R.string.AppName));
        telegramLogoView.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        telegramLogoView.setImageResource(R.drawable.telegram_logo_2);
        telegramLogoView.setColorFilter(getTextLogoColor(), PorterDuff.Mode.MULTIPLY);
        telegramLogoView.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
        telegramLogoView.setFocusableInTouchMode(true);
        addView(telegramLogoView, LayoutHelper.createFrame(90, 22));""",
        """        // Visible home wordmark is separate from the native ActionBar title.
        // Use the approved name, never Telegram's image-based wordmark.
        telegramLogoView = new TextView(context);
        telegramLogoView.setContentDescription("NabdhGram");
        telegramLogoView.setText("NabdhGram");
        telegramLogoView.setSingleLine(true);
        telegramLogoView.setEllipsize(TextUtils.TruncateAt.END);
        telegramLogoView.setTextSize(20);
        telegramLogoView.setTypeface(AndroidUtilities.bold());
        telegramLogoView.setGravity(Gravity.CENTER_VERTICAL);
        telegramLogoView.setTextColor(getTextLogoColor());
        telegramLogoView.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
        telegramLogoView.setFocusableInTouchMode(true);
        addView(telegramLogoView, LayoutHelper.createFrame(LayoutHelper.WRAP_CONTENT, 28));""",
        "visible brand"
    )
    story = story_once(
        "        telegramLogoView.setColorFilter(getTextLogoColor(), PorterDuff.Mode.MULTIPLY);",
        "        telegramLogoView.setTextColor(getTextLogoColor());",
        "wordmark theme updates"
    )
    # The native stories logo deliberately fades to zero during expansion.
    # On main chats, rendering both this logo and ActionBar title creates
    # either a duplicate name or a missing name in mid-transition.
    # The main screen has exactly one owner: ActionBar. Keep stories labels,
    # story avatars and Premium emoji overlays otherwise untouched.
    story = story_once(
        """        final float logoAlpha = logoVisibility * progress;""",
        """        final float logoAlpha = type == TYPE_DIALOGS ? 0f : logoVisibility * progress;""",
        "suppress duplicate stories wordmark on main chats"
    )
    story = story_once(
        """            telegramLogoView.setTranslationX(titleView.getTranslationX() + dp(1));
            telegramLogoView.setTranslationY(bottomY - barOffset + dp(14 + FAKE_TOP_PADDING + 4.333f) + translationOffset /*titleView.getTranslationY() + dpf2(37.33f)*/);

            emojiStatusView.setTranslationX(titleView.getTranslationX() - dpf2(3.33f) + telegramLogoView.getMeasuredWidth());""",
        """            // The secondary stories wordmark must not inherit titleView's
            // animation translation. That offset oscillates on expand/collapse
            // and leaves a tiny "NabdhGram" at the extreme left after returning
            // from Settings, even when Center title is disabled.
            // Keep the same stable avatar-safe START anchor as the home title.
            float nabdhLogoX = dp(72);
            if (type == TYPE_DIALOGS &&
                    org.telegram.ui.Components.NabdhHomePrefs.enabled(getContext(), "center_title")) {
                // Center ONLY when the user explicitly enabled that option.
                float desired = (getWidth() - telegramLogoView.getMeasuredWidth()) / 2f;
                float minX = dp(72);
                float maxX = getWidth() - actionBar.menu.getVisibleItemsMeasuredWidthWithAlpha()
                        - telegramLogoView.getMeasuredWidth() - dp(36);
                nabdhLogoX = Math.max(minX, Math.min(desired, Math.max(minX, maxX)));
            }
            telegramLogoView.setTranslationX(nabdhLogoX);
            // Never inherit Telegram's shrinking status-wordmark animation:
            // the user-facing NabdhGram name must remain readable while
            // stories expand, collapse or the home tab is restored.
            telegramLogoView.setScaleX(1f);
            telegramLogoView.setScaleY(1f);
            telegramLogoView.setTranslationY(bottomY - barOffset + dp(14 + FAKE_TOP_PADDING + 4.333f) + translationOffset /*titleView.getTranslationY() + dpf2(37.33f)*/);

            emojiStatusView.setTranslationX(nabdhLogoX + telegramLogoView.getMeasuredWidth() + dp(4));""",
        "stories and premium status title geometry"
    )
    stories.write_text(story, encoding="utf-8")
    print("PASS: main home title and independent stories-header brand are NabdhGram.")

if __name__ == "__main__":
    main()
