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
# Telegram already provides server-side Scheduled Messages from any chat's
# Send-button long-press menu. Surface this existing feature in Privacy,
# rather than introducing another sending queue or fake enable switch.
schedule_anchor = "            addPrivacyControls(context, content);"
if source.count(schedule_anchor) != 1:
    raise SystemExit("Privacy category body changed")
source = source.replace(schedule_anchor, schedule_anchor + """
            TextView scheduleTitle = new TextView(context);
            scheduleTitle.setText(context.getString(R.string.NabdhScheduleTitle));
            scheduleTitle.setTextSize(18);
            scheduleTitle.setTypeface(null, Typeface.BOLD);
            scheduleTitle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            LinearLayout.LayoutParams scheduleParams = new LinearLayout.LayoutParams(-1, -2);
            scheduleParams.topMargin = (int) (20 * context.getResources().getDisplayMetrics().density);
            content.addView(scheduleTitle, scheduleParams);
            TextView scheduleInfo = new TextView(context);
            scheduleInfo.setText(context.getString(R.string.NabdhScheduleInstructions));
            scheduleInfo.setTextSize(14);
            scheduleInfo.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
            content.addView(scheduleInfo);
""", 1)
for lang, heading, instructions in [
    ("values", "Scheduled messages", "Available now through Telegram: open a chat, write a message, then long-press Send and choose Schedule Message. Telegram handles delivery; this setting does not create a second scheduler."),
    ("values-ar", "الرسائل المجدولة", "متاحة حاليًا عبر Telegram: افتح محادثة، واكتب رسالة، ثم اضغط مطولًا على زر الإرسال واختر جدولة الرسالة. يتولى Telegram الإرسال دون إنشاء نظام جدولة مكرر.")
]:
    f = root / "TMessagesProj/src/main/res" / lang / "nabdhgram_settings.xml"
    from xml.sax.saxutils import escape
    xml = f.read_text(encoding="utf-8")
    if xml.count("</resources>") != 1:
        raise SystemExit("Settings strings resource structure changed")
    xml = xml.replace("</resources>", '    <string name="NabdhScheduleTitle">' + escape(heading) + '</string>\\n' +
                      '    <string name="NabdhScheduleInstructions">' + escape(instructions) + '</string>\\n</resources>')
    f.write_text(xml, encoding="utf-8")

target = root / "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramFeatureCategoryActivity.java"
target.write_text(source, encoding="utf-8")
print("Created six navigable NabdhGram category pages; Privacy Screen moved into Privacy category.")
