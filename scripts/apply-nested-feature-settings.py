#!/usr/bin/env python3
"""Convert NabdhGram roadmap cards to navigable category pages."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nested-feature-settings.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
page = root / "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramSettingsActivity.java"
s = page.read_text(encoding="utf-8")
start = s.index("        android.widget.CheckBox privacyToggle = ")
end_marker = "        content.addView(privacyNote);"
end = s.index(end_marker, start) + len(end_marker)
privacy = s[start:end]
s = s[:start] + s[end:]
old = "        card.addView(description, textLp);"
if s.count(old) != 1:
    raise SystemExit("Category card rendering anchor changed")
s = s.replace(old, old + '''
        card.setClickable(true);
        card.setFocusable(true);
        card.setOnClickListener(v -> presentFragment(
                new NabdhGramFeatureCategoryActivity(titleRes, descriptionRes)));
''', 1)
page.write_text(s, encoding="utf-8")
# Keep the working Privacy Screen control only in the Privacy category.
# Other categories intentionally show their planned functionality, not fake switches.
privacy = privacy.replace("        ", "        ")
source = r'''package org.telegram.ui;

import android.content.Context;
import android.graphics.Typeface;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;

public class NabdhGramFeatureCategoryActivity extends BaseFragment {
    private final int titleRes;
    private final int descriptionRes;

    public NabdhGramFeatureCategoryActivity(int titleRes, int descriptionRes) {
        this.titleRes = titleRes;
        this.descriptionRes = descriptionRes;
    }

    @Override
    public View createView(Context context) {
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setTitle(context.getString(titleRes));
        actionBar.setAllowOverlayTitle(true);
        actionBar.setActionBarMenuOnItemClick(new org.telegram.ui.ActionBar.ActionBar.ActionBarMenuOnItemClick() {
            @Override
            public void onItemClick(int id) {
                if (id == -1) finishFragment();
            }
        });
        ScrollView scroll = new ScrollView(context);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));
        LinearLayout content = new LinearLayout(context);
        content.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (20 * context.getResources().getDisplayMetrics().density);
        content.setPadding(pad, pad, pad, pad);
        scroll.addView(content);
        TextView explanation = new TextView(context);
        explanation.setText(context.getString(descriptionRes));
        explanation.setTextSize(15);
        explanation.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        content.addView(explanation);
        if (titleRes == R.string.NabdhPrivacyTitle) {
            addPrivacyControls(context, content);
        }
        fragmentView = scroll;
        return fragmentView;
    }

    private void addPrivacyControls(Context context, LinearLayout content) {
__PRIVACY__
    }
}
'''
# Correct fully qualified nested class reference: the class is in ActionBar.
source = source.replace("org.telegram.ui.ActionBar.ActionBar.ActionBarMenuOnItemClick", "org.telegram.ui.ActionBar.ActionBar.ActionBarMenuOnItemClick")
source = source.replace("__PRIVACY__", privacy)
target = root / "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramFeatureCategoryActivity.java"
target.write_text(source, encoding="utf-8")
print("Created six navigable NabdhGram category pages; Privacy Screen moved into Privacy category.")
