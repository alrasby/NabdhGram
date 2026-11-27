#!/usr/bin/env python3
"""Add native, immediately applied V1 appearance controls without changing chats."""
from pathlib import Path
import sys
from xml.sax.saxutils import escape

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-personalization.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
templates = Path(__file__).resolve().parents[1] / "overlay/java"

def once(text, before, after, desc):
    if text.count(before) != 1:
        raise SystemExit(f"Personalization {desc}: expected one anchor, got {text.count(before)}")
    return text.replace(before, after, 1)

for file, destination in [
    ("NabdhHomePrefs.java", "Components/NabdhHomePrefs.java"),
    ("NabdhStorageAudit.java", "Components/NabdhStorageAudit.java"),
    ("NabdhPersonalizeActivity.java", "NabdhPersonalizeActivity.java"),
    ("NabdhVideoActivity.java", "NabdhVideoActivity.java"),
    ("NabdhCameraGalleryActivity.java", "NabdhCameraGalleryActivity.java"),
    ("NabdhCameraFiles.java", "NabdhCameraFiles.java"),
    ("NabdhPhotoEditorActivity.java", "NabdhPhotoEditorActivity.java"),
    ("NabdhAiPhotoEditorActivity.java", "NabdhAiPhotoEditorActivity.java"),
]:
    dest = ui / destination
    if dest.exists():
        raise SystemExit("Personalization class collision: " + str(dest))
    dest.write_bytes((templates / file).read_bytes())

manifest = root / "TMessagesProj/src/main/AndroidManifest.xml"
m = manifest.read_text(encoding="utf-8")
# PiP is strictly opt-in and limited to a visible recording window.
marker = '        <activity android:name="org.telegram.ui.NabdhAppearancePickerActivity"'
m = once(m, marker, '''        <activity android:name="org.telegram.ui.NabdhPhotoEditorActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
        <activity android:name="org.telegram.ui.NabdhAiPhotoEditorActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
        <activity android:name="org.telegram.ui.NabdhCameraGalleryActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
        <activity android:name="org.telegram.ui.NabdhVideoActivity"
                  android:exported="false"
                  android:supportsPictureInPicture="true"
                  android:configChanges="screenSize|smallestScreenSize|screenLayout|orientation"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
        <activity android:name="org.telegram.ui.NabdhPersonalizeActivity"
                  android:exported="false"
                  android:theme="@android:style/Theme.Material.NoActionBar" />
''' + marker, "private settings Activity")
manifest.write_text(m, encoding="utf-8")

# A strictly scoped FileProvider mount: private files and temporary
# sanitized share copies only. No access to public MediaStore is introduced.
paths = root / "TMessagesProj/src/main/res/xml/provider_paths.xml"
xml = paths.read_text(encoding="utf-8")
if "nabdh_private_camera" in xml or "nabdh_camera/" in xml:
    raise SystemExit("Private Camera provider path collision")
xml = once(xml, "</paths>",
    '    <files-path name="nabdh_private_camera" path="nabdh_camera/" />\n'
    '    <cache-path name="nabdh_private_share" path="nabdh_private_share/" />\n'
    "</paths>", "FileProvider narrowly scoped directories")
paths.write_text(xml, encoding="utf-8")

# Bundled Android API 23+ model used for genuinely on-device selfie
# segmentation in the opt-in portrait editor, no Gemini Nano dependency.
build = root / "TMessagesProj/build.gradle"
gradle = build.read_text(encoding="utf-8")
gradle = once(gradle, "dependencies {",
    "dependencies {\n    implementation 'com.google.mlkit:segmentation-selfie:16.0.0-beta6'",
    "bundled local portrait ML Kit model")
build.write_text(gradle, encoding="utf-8")

page = ui / "NabdhGramFeatureCategoryActivity.java"
p = page.read_text(encoding="utf-8")
marker = '''        nabdhFeatureRow(context, content, 602);

        org.telegram.ui.Components.NabdhCompactSettings.header'''
p = once(p, marker, '''        nabdhFeatureRow(context, content, 602);

        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhUiStyleTitle),
                NabdhStrings.get(context, R.string.NabdhUiStyleSummary),
                R.drawable.settings_chat,
                () -> {
                    final String[] styles = {
                        NabdhStrings.get(context, R.string.NabdhUiStyleClassic),
                        NabdhStrings.get(context, R.string.NabdhUiStyleMaterial),
                        NabdhStrings.get(context, R.string.NabdhUiStyleGlass),
                        NabdhStrings.get(context, R.string.NabdhUiStyleHybrid)
                    };
                    int selected = org.telegram.ui.Components.NabdhAppearancePrefs.uiStyle();
                    String selectedLabel = styles[selected];
                    styles[selected] = "✓  " + selectedLabel;
                    new org.telegram.ui.ActionBar.AlertDialog.Builder(context)
                            .setTitle(NabdhStrings.get(context, R.string.NabdhUiStyleTitle))
                            .setItems(styles, (dialog, which) -> {
                                        org.telegram.ui.Components.NabdhAppearancePrefs.setUiStyle(context, which);
                                        nabdhInvalidateStyleTree(content.getRootView());
                                        content.requestLayout();
                                        if (which != selected) {
                                            content.post(() -> {
                                                if (getParentLayout() != null) {
                                                    getParentLayout().rebuildAllFragmentViews(true, true);
                                                }
                                            });
                                        }
                                        android.widget.Toast.makeText(context,
                                                which == selected ? selectedLabel : styles[which],
                                                android.widget.Toast.LENGTH_SHORT).show();
                                    })
                            .setNegativeButton(org.telegram.messenger.LocaleController.isRTL ? "إغلاق" : "Close", null)
                            .show();
                });

        org.telegram.ui.Components.NabdhCompactSettings.header(context, content,
                NabdhStrings.get(context, R.string.NabdhStorageSection));
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhStorageAuditTitle),
                NabdhStrings.get(context, R.string.NabdhStorageAuditSummary),
                R.drawable.settings_data,
                () -> org.telegram.ui.Components.NabdhStorageAudit.show(context));

        // User-visible native home, bubble and Camera2 settings under themes.
        org.telegram.ui.Components.NabdhCompactSettings.header(context, content,
                NabdhStrings.get(context, R.string.NabdhPersonalizeSection));
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhPersonalizeHome),
                NabdhStrings.get(context, R.string.NabdhPersonalizeHomeInfo),
                R.drawable.settings_chat,
                () -> nabdhPersonalize(context, NabdhPersonalizeActivity.HOME));
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhPersonalizeBubbles),
                NabdhStrings.get(context, R.string.NabdhPersonalizeBubbleInfo),
                R.drawable.settings_chat,
                () -> nabdhPersonalize(context, NabdhPersonalizeActivity.BUBBLES));
        org.telegram.ui.Components.NabdhCompactSettings.row(context, content,
                NabdhStrings.get(context, R.string.NabdhPersonalizeCamera),
                NabdhStrings.get(context, R.string.NabdhPersonalizeCameraInfo),
                R.drawable.nabdh_tool_camera,
                () -> nabdhPersonalize(context, NabdhPersonalizeActivity.CAMERA));

        org.telegram.ui.Components.NabdhCompactSettings.header''', "appearance menu after themes")
marker = '''    private void nabdhAppearancePicker(Context context, String kind) {'''
method = '''    private static void nabdhInvalidateStyleTree(android.view.View view) {
        view.invalidate();
        if (view instanceof android.view.ViewGroup) {
            android.view.ViewGroup group = (android.view.ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                nabdhInvalidateStyleTree(group.getChildAt(i));
            }
        }
    }

    private void nabdhPersonalize(Context context, String kind) {
        android.content.Intent intent = new android.content.Intent(context,
                NabdhPersonalizeActivity.class);
        intent.putExtra(NabdhPersonalizeActivity.EXTRA_SECTION, kind);
        context.startActivity(intent);
    }

''' + marker
p = once(p, marker, method, "personalization launcher")
page.write_text(p, encoding="utf-8")

strings = {
    "values": {
        "NabdhUiStyleTitle": "UI style",
        "NabdhUiStyleSummary": "Choose the appearance of cards and controls",
        "NabdhUiStyleClassic": "Classic",
        "NabdhUiStyleMaterial": "Material 3",
        "NabdhUiStyleGlass": "Siri Glass",
        "NabdhUiStyleHybrid": "Material 3 with Glass",
        "NabdhStorageSection": "Storage",
        "NabdhStorageAuditTitle": "Smart Storage",
        "NabdhStorageAuditSummary": "See how much space app data uses",
        "NabdhPersonalizeSection": "Layout and message bubbles",
        "NabdhPersonalizeHome": "Main screen layout",
        "NabdhPersonalizeHomeInfo": "Title, stories, search, compose button and folder tabs",
        "NabdhPersonalizeBubbles": "Chat bubble shapes",
        "NabdhPersonalizeBubbleInfo": "Compact, soft and extra-rounded native bubbles",
        "NabdhPersonalizeCamera": "Nabdh Camera2 options",
        "NabdhPersonalizeCameraInfo": "Lens, stabilization, mirror, resolution and zoom",
    },
    "values-ar": {
        "NabdhUiStyleTitle": "نمط الواجهة",
        "NabdhUiStyleSummary": "اختر مظهر البطاقات وعناصر الواجهة",
        "NabdhUiStyleClassic": "كلاسيكي",
        "NabdhUiStyleMaterial": "ماتيريال 3",
        "NabdhUiStyleGlass": "زجاج سيري",
        "NabdhUiStyleHybrid": "ماتيريال 3 مع الزجاج",
        "NabdhStorageSection": "التخزين",
        "NabdhStorageAuditTitle": "إدارة التخزين الذكية",
        "NabdhStorageAuditSummary": "اعرف ما يشغل مساحة بيانات التطبيق",
        "NabdhPersonalizeSection": "التنسيق وفقاعات المحادثات",
        "NabdhPersonalizeHome": "تنسيق الشاشة الرئيسية",
        "NabdhPersonalizeHomeInfo": "العنوان والقصص والبحث والزر العائم والمجلدات",
        "NabdhPersonalizeBubbles": "أشكال فقاعات المحادثات",
        "NabdhPersonalizeBubbleInfo": "مضغوطة وناعمة ودائرية باستدارة Telegram الفعلية",
        "NabdhPersonalizeCamera": "خيارات كاميرا نبض",
        "NabdhPersonalizeCameraInfo": "العدسة والتثبيت والعكس والدقة والتكبير",
    },
}
for lang, values in strings.items():
    file = root / "TMessagesProj/src/main/res" / lang / "nabdh_personalize.xml"
    if file.exists():
        raise SystemExit("Personalization resources already exist: " + str(file))
    content = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for key, value in values.items():
        content.append(f'    <string name="{key}">{escape(value)}</string>')
    file.write_text("\n".join(content + ["</resources>", ""]), encoding="utf-8")

dialogs = ui / "DialogsActivity.java"
d = dialogs.read_text(encoding="utf-8")
prefix = "org.telegram.ui.Components.NabdhHomePrefs"
d = once(d,
    '''        final boolean isVisible = !(onlySelect && initialDialogsType != 10 || folderId != 0 || communityId != 0 || inPreviewMode || (searching && !onlySelect) || floatingButtonHidden);''',
    '''        final boolean isVisible = !(onlySelect && initialDialogsType != 10 || folderId != 0 || communityId != 0 || inPreviewMode || (searching && !onlySelect) || floatingButtonHidden)
                && !(initialDialogsType == DIALOGS_TYPE_DEFAULT && !onlySelect && folderId == 0
                && communityId == 0 && ''' + prefix + '''.enabled(getContext(), "hide_fab"));''',
    "native floating action")
d = once(d,
    '''        hasOnlySlefStories = onlySelfStories;

        boolean oldStoriesCellVisibility''',
    '''        // Do not mutate upstream newVisibility: animator closures capture it.
        final boolean nabdhHideHomeStories = initialDialogsType == DIALOGS_TYPE_DEFAULT
                && folderId == 0 && communityId == 0
                && ''' + prefix + '''.enabled(getContext(), "hide_stories");
        if (nabdhHideHomeStories) onlySelfStories = false;
        final boolean nabdhVisibleStories = newVisibility && !nabdhHideHomeStories;
        hasOnlySlefStories = onlySelfStories;

        boolean oldStoriesCellVisibility''',
    "native stories visibility")
# Redirect only downstream uses of the computed visibility (including
# anonymous animation callbacks), leaving the upstream local unmodified.
startStories = d.index("    public void updateStoriesVisibility(boolean animated) {")
endStories = d.index("    public void createSearchViewPager() {", startStories)
story = d[startStories:endStories]
separator = "        boolean oldStoriesCellVisibility"
if story.count(separator) != 1:
    raise SystemExit("Personalization: animation binding changed upstream")
head, tail = story.split(separator, 1)
tail = tail.replace("newVisibility", "nabdhVisibleStories")
d = d[:startStories] + head + separator + tail + d[endStories:]
d = once(d,
    '''        final float factor0 = isSupportSearch() ? 1 : 0;
        final float factor1 = (1f - actionModeVisible)''',
    '''        final boolean nabdhHideSearch = initialDialogsType == DIALOGS_TYPE_DEFAULT
                && !onlySelect && folderId == 0 && communityId == 0
                && ''' + prefix + '''.enabled(getContext(), "hide_search");
        final float factor0 = isSupportSearch() && (!nabdhHideSearch
                || searchFieldVisible > 0.01f) ? 1 : 0;
        final float factor1 = (1f - actionModeVisible)''',
    "search bar (keep explicit search)")
# Default + user-defined filters: keep a real native All Chats tab visible.
d = once(d, '''        if (filters.size() > 1) {''',
         '''        if (filters.size() > 1 ||
                filters.size() == 1 && initialDialogsType == DIALOGS_TYPE_DEFAULT
                && !onlySelect && folderId == 0 && communityId == 0) {''',
         "always display real native folder bar")
d = once(d,
    '''                        filterTabsView.addTab(a, 0, LocaleController.getString(R.string.FilterAllChats), null, false, true, filters.get(a).locked);''',
    '''                        String original = LocaleController.getString(R.string.FilterAllChats);
                        int mode = ''' + prefix + '''.folderMode(getContext());
                        filterTabsView.addTab(a, 0,
                                ''' + prefix + '''.folderLabel(getContext(), original, true, 0),
                                mode == 1 ? null : null, false, true, filters.get(a).locked);''',
    "native All Chats title")
d = once(d,
    '''                        filterTabsView.addTab(a, filter.localId, filter.name, filter.entities, filter.title_noanimate, false, filters.get(a).locked);''',
    '''                        int mode = ''' + prefix + '''.folderMode(getContext());
                        filterTabsView.addTab(a, filter.localId,
                                ''' + prefix + '''.folderLabel(getContext(), filter.name, false, filter.localId),
                                mode == 1 ? filter.entities : null,
                                filter.title_noanimate, false, filters.get(a).locked);''',
    "native folder titles")
d = once(d,
    '''    public void onResume() {
        super.onResume();''',
    '''    public void onResume() {
        super.onResume();
        // Only the native main chat list owns these presentation controls.
        if (initialDialogsType == DIALOGS_TYPE_DEFAULT && !onlySelect && folderId == 0 && communityId == 0) {
            ''' + prefix + '''.applyTitle(actionBar, getContext());
            updateStoriesVisibility(false);
            updateFloatingButtonVisibility(false);
            updateFilterTabs(true, false);
            checkUi_searchFieldVisibility();
        }''',
    "native home restoration")
dialogs.write_text(d, encoding="utf-8")

# MainTabsActivity is deliberately untouched. Telegram itself owns the title
# across tab changes; adding a second setTitle owner caused proxy/status and
# stories transitions to fight the existing wordmark.
print("PASS: native home preferences; upstream title lifecycle preserved")
