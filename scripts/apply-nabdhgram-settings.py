#!/usr/bin/env python3
"""Brand pinned Telegram Settings without modifying login or Telegram protocols."""
from pathlib import Path
import sys

def once(s, old, new, label):
    if s.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {s.count(old)}")
    return s.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-nabdhgram-settings.py TELEGRAM_SOURCE")
    root = Path(sys.argv[1]).resolve()
    p = root / "TMessagesProj/src/main/java/org/telegram/ui/SettingsActivity.java"
    s = p.read_text(encoding="utf-8")
    # Keep upstream version reporting available; add a branded, clickable credit.
    s = once(s, "versionView.setText(getVersionName());",
        'versionView.setText(getString(R.string.NabdhGramCredits));', "credits label")
    start = s.index("        versionView.setOnClickListener(v -> {")
    end = s.index("\n\n        navigationBar = new View(context);", start)
    s = s[:start] + '''        versionView.setOnClickListener(v -> Browser.openUrl(getContext(), "https://nabdhserv.net"));
        // Retain Telegram's debug menu through a deliberate long press.
        versionView.setOnLongClickListener(v -> {
            openDebugMenu();
            return true;
        });''' + s[end:]
    s = once(s,
        '        items.add(UItem.asHeader(getString(R.string.SettingsHelp)));',
        '''        // NabdhGram feature hub; currently a transparent status overview.
        // Do not present planned capabilities as already active.
        items.add(SettingCell.Factory.of(80, IconBackgroundColors.CYAN.top,
                IconBackgroundColors.CYAN.bottom, R.drawable.settings_privacy,
                getString(R.string.NabdhGramSettingsTitle), getString(R.string.NabdhGramFeaturesStatus)));
        items.add(UItem.asShadow(null));

        items.add(UItem.asHeader(getString(R.string.SettingsHelp)));''', "settings hub")
    s = once(s, '        switch (item.id) {\n            case 1:',
        '''        switch (item.id) {
            case 80:
                presentSettingFragment(new NabdhGramSettingsActivity());
                break;
            case 1:''', "settings click")
    # Telegram's LocaleController resolves only registered language-pack keys.
    # Custom resource IDs may return LOC_ERR:null even when R.string compiles.
    # Use Android Resources directly for NabdhGram-only strings.
    # Match the literal Java calls; do not double-escape regex metacharacters.
    import re
    pattern = r'getString\(R\.string\.(NabdhGram\w+|NabdhShield\w+)\)'
    s, count = re.subn(pattern,
                       lambda m: 'getParentActivity().getString(R.string.' + m.group(1) + ')', s)
    if count < 8:
        raise SystemExit(f"Expected at least 8 NabdhGram strings, found {count}")
    print(f"Patched {count} custom Settings string lookups")
    p.write_text(s, encoding="utf-8")
    # A real subpage for all current and future NabdhGram feature settings.
    feature_page = root / "TMessagesProj/src/main/java/org/telegram/ui/NabdhGramSettingsActivity.java"
    feature_page.write_text(r'''package org.telegram.ui;

import android.content.Context;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ActionBar.ActionBar;

public class NabdhGramSettingsActivity extends BaseFragment {
    @Override
    public View createView(Context context) {
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setTitle(context.getString(R.string.NabdhGramSettingsTitle));
        actionBar.setAllowOverlayTitle(true);
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
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
        section(context, content, R.string.NabdhShieldTitle, R.string.NabdhShieldExplanation);
        section(context, content, R.string.NabdhGramFeaturesTitle, R.string.NabdhGramFeaturesExplanation);
        fragmentView = scroll;
        return fragmentView;
    }

    private void section(Context context, LinearLayout parent, int titleRes, int descriptionRes) {
        LinearLayout card = new LinearLayout(context);
        card.setOrientation(LinearLayout.VERTICAL);
        int d = (int) (16 * context.getResources().getDisplayMetrics().density);
        card.setPadding(d, d, d, d);
        card.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = d;
        parent.addView(card, lp);
        TextView heading = new TextView(context);
        heading.setText(context.getString(titleRes));
        heading.setTextSize(18);
        heading.setTypeface(null, Typeface.BOLD);
        heading.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        card.addView(heading);
        TextView description = new TextView(context);
        description.setText(context.getString(descriptionRes));
        description.setTextSize(14);
        description.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        LinearLayout.LayoutParams textLp = new LinearLayout.LayoutParams(-1, -2);
        textLp.topMargin = d / 2;
        card.addView(description, textLp);
    }
}
''', encoding="utf-8")

    # SettingsActivity compiles in :TMessagesProj, so its R.string symbols must
    # be generated by that module, not :TMessagesProj_App.
    values = root / "TMessagesProj/src/main/res"
    strings = {
        "values": {
            "NabdhGramCredits": "NabdhGram - Based on Telegram v13.1.1 (7237)\\nDesigned by @alrasby",
            "NabdhGramSettingsTitle": "NabdhGram Settings",
            "NabdhShieldTitle": "NabdhShield",
            "NabdhShieldStatus": "Local link safety — in development",
            "NabdhGramFeaturesTitle": "NabdhGram Features",
            "NabdhGramFeaturesStatus": "Privacy, productivity, network and media",
            "NabdhShieldExplanation": "NabdhShield is being developed. URL risk signals are not a guarantee of safety. Link previews and download checks are not enabled yet.",
            "NabdhGramFeaturesExplanation": "Planned: Focus Lens, Message Workspace, Catch Me Up, Smart Chat Preview, Privacy Screen, translation, Voice Clarity and Network Intelligence. Email sign-in codes are available only when Telegram servers offer them. No independent email login is implemented."
        },
        "values-ar": {
            "NabdhGramCredits": "NabdhGram v13.1.1 (7237) release arm64-v8a\\nBased on Telegram v13.1.1 (7237)\\nDesigned by @alrasby",
            "NabdhGramSettingsTitle": "إعدادات نبض جرام",
            "NabdhShieldTitle": "NabdhShield — درع نبض",
            "NabdhShieldStatus": "فحص الروابط المحلي — قيد التطوير",
            "NabdhGramFeaturesTitle": "مميزات نبض جرام",
            "NabdhGramFeaturesStatus": "الخصوصية والإنتاجية والشبكة والوسائط",
            "NabdhShieldExplanation": "ميزة NabdhShield قيد التطوير. إشارات خطورة الروابط ليست ضمانًا للأمان. معاينة الروابط وفحص التنزيلات غير مفعّلين بعد.",
            "NabdhGramFeaturesExplanation": "المميزات المخططة: Focus Lens وMessage Workspace وCatch Me Up ومعاينة المحادثات وشاشة الخصوصية والترجمة وتحسين الصوت والشبكة. رمز الدخول بالبريد متاح فقط عندما يقدمه خادم Telegram، ولم نضف تسجيل دخول مستقلًا بالبريد."
        }
    }
    from xml.sax.saxutils import escape
    for folder, mapping in strings.items():
        dest = values / folder / "nabdhgram_settings.xml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
        for key, val in mapping.items():
            lines.append(f'    <string name="{key}">{escape(val)}</string>')
        lines.append('</resources>')
        dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("NabdhGram Settings hub and branded credits installed.")

if __name__ == "__main__":
    main()
