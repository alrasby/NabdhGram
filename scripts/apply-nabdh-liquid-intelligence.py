#!/usr/bin/env python3
"""Nabdh Liquid Glass and private local Context Lens on pinned Telegram.

Keep Telegram's native message draw geometry, native AI Editor, translation,
voice transcription, selection, send and auth flow. Pinned anchors fail closed.
No external models, network requests or sensitive-content storage are added.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-liquid-intelligence.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve()
ui = root / "TMessagesProj/src/main/java/org/telegram/ui"
templates = Path(__file__).resolve().parent.parent / "overlay/java"

def patch(text, original, modified, label):
    actual = text.count(original)
    if actual != 1:
        raise SystemExit(f"{label}: expected one pinned anchor, got {actual}")
    return text.replace(original, modified, 1)

for filename in ("NabdhGlassStyle.java", "NabdhContextLens.java"):
    destination = ui / "Components" / filename
    if destination.exists():
        raise SystemExit(f"Unexpected pre-existing native helper: {filename}")
    destination.write_text((templates / filename).read_text(encoding="utf-8"),
                           encoding="utf-8")

# Existing draw method already uses Telegram's native path and cached wallpaper
# blur. Tune its tint/rim only; never allocate bitmaps, views or models per draw.
bubble = ui / "ActionBar/MessageDrawable.java"
src = bubble.read_text(encoding="utf-8")
# Reuse a cached fixed-size light shader. Width/height changes of
# recycled message cells never cause shader/bitmap allocations.
src = patch(src,
    """    private final Paint nabdhCrystalTint = new Paint(Paint.ANTI_ALIAS_FLAG);""",
    """    private final Paint nabdhCrystalTint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint nabdhLiquidLight = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Matrix nabdhLiquidMatrix = new Matrix();
    private final RectF nabdhLiquidBounds = new RectF();
    private android.graphics.LinearGradient nabdhLiquidShader;
    private int nabdhLiquidStyleCache = -1;
    private int nabdhLiquidAccentCache;""",
    "cached native bubble specular paints")
src = patch(src,
    """    private void nabdhDrawCrystalSurface(Canvas canvas, Path bubblePath) {""",
    """    private void nabdhDrawLiquidLight(Canvas canvas, Path bubblePath, int style, int accent) {
        if (style == org.telegram.ui.Components.NabdhGlassStyle.SOFT) return;
        if (nabdhLiquidShader == null || nabdhLiquidStyleCache != style
                || nabdhLiquidAccentCache != accent) {
            final int top = style == org.telegram.ui.Components.NabdhGlassStyle.CRYSTAL ? 48 : 30;
            final int bottom = style == org.telegram.ui.Components.NabdhGlassStyle.CRYSTAL ? 28 : 14;
            nabdhLiquidShader = new android.graphics.LinearGradient(
                    0, 0, 0, AndroidUtilities.dp(128),
                    new int[] {
                        Color.argb(top, 255, 255, 255),
                        Color.argb(8, 250, 255, 255),
                        Color.argb(0, 255, 255, 255),
                        Color.argb(bottom, Color.red(accent),
                                Color.green(accent), Color.blue(accent))
                    },
                    new float[] {0f, 0.28f, 0.70f, 1f},
                    android.graphics.Shader.TileMode.CLAMP);
            nabdhLiquidLight.setShader(nabdhLiquidShader);
            nabdhLiquidStyleCache = style;
            nabdhLiquidAccentCache = accent;
        }
        bubblePath.computeBounds(nabdhLiquidBounds, true);
        nabdhLiquidMatrix.setTranslate(0, nabdhLiquidBounds.top);
        nabdhLiquidShader.setLocalMatrix(nabdhLiquidMatrix);
        nabdhLiquidLight.setAlpha(alpha);
        canvas.drawPath(bubblePath, nabdhLiquidLight);
    }

    private void nabdhDrawCrystalSurface(Canvas canvas, Path bubblePath) {""",
    "native cached refraction ramp")
src = patch(src,
    """        canvas.drawPath(bubblePath, nabdhCrystalTint);""",
    """        canvas.drawPath(bubblePath, nabdhCrystalTint);
        nabdhDrawLiquidLight(canvas, bubblePath, nabdhStyle, accent);""",
    "native bubble light reflection")
src = patch(src,
    "        final int accent = getColor(Theme.key_windowBackgroundWhiteBlueText);",
    """        final int nabdhStyle = org.telegram.ui.Components.NabdhGlassStyle.current();
        final int accent = getColor(Theme.key_windowBackgroundWhiteBlueText);""",
    "bubble preset getter")
src = patch(src,
    """nabdhCrystalTint.setColor(Color.argb((isOut ? 60 : 46) * alpha / 255,""",
    """nabdhCrystalTint.setColor(Color.argb(
                (nabdhStyle == 0 ? 25 : nabdhStyle == 2 ? 76 : (isOut ? 60 : 46))
                * alpha / 255,""",
    "bubble overlay tint")
src = patch(src,
    """nabdhCrystalRim.setStrokeWidth(AndroidUtilities.dpf2(0.85f));""",
    """nabdhCrystalRim.setStrokeWidth(AndroidUtilities.dpf2(
                nabdhStyle == 0 ? 0.55f : nabdhStyle == 2 ? 1.2f : 0.85f));""",
    "bubble border width")
src = patch(src,
    """nabdhCrystalRim.setColor(Color.argb(165 * alpha / 255,""",
    """nabdhCrystalRim.setColor(Color.argb(
                (nabdhStyle == 0 ? 76 : nabdhStyle == 2 ? 194 : 165)
                * alpha / 255,""",
    "bubble border intensity")
src = patch(src,
    """        bubblePath.computeBounds(nabdhCrystalBounds, true);
        canvas.save();""",
    """        if (nabdhStyle == 0) return; // Soft Glass has no specular strip.
        bubblePath.computeBounds(nabdhCrystalBounds, true);
        canvas.save();""",
    "bubble specular opt-out")
src = patch(src,
    """nabdhCrystalRim.setColor(Color.argb(115 * alpha / 255, 245, 255, 255));""",
    """nabdhCrystalRim.setColor(Color.argb(
                (nabdhStyle == 2 ? 174 : 115) * alpha / 255,
                245, 255, 255));""",
    "bubble specular intensity")
bubble.write_text(src, encoding="utf-8")

# Long-press the EXISTING Telegram AI editor icon (non-secret chats only) to
# invoke local tools. Normal click remains native, with its own consent and
# Telegram provider behavior. Never intercept sending or selected messages.
composer = ui / "Components/ChatActivityEnterView.java"
s = composer.read_text(encoding="utf-8")
old = """        aiButton.setVisibility(View.GONE);
        aiButton.setAlpha(0.0f);"""
new = """        aiButton.setOnLongClickListener(v -> {
            if (parentFragment == null || parentFragment.isSecretChat()
                    || messageEditText == null) return false;
            return NabdhContextLens.show(getContext(), messageEditText.getText(),
                    text -> {
                        if (messageEditText == null) return;
                        messageEditText.setText(text);
                        messageEditText.setSelection(messageEditText.length());
                    });
        });
        aiButton.setVisibility(View.GONE);
        aiButton.setAlpha(0.0f);"""
s = patch(s, old, new, "native AI Editor long-press hook")
s = patch(s,
    """showAiButton(lineCount > 2 && editable != null && !TextUtils.isEmpty(editable.toString().trim()));""",
    """showAiButton(editable != null && !TextUtils.isEmpty(editable.toString().trim())
                        && (lineCount > 2 || NabdhGlassStyle.lensEnabled(getContext())));""",
    "visible opt-in Lens access in short composer text")
composer.write_text(s, encoding="utf-8")

# Appearance & local-assistant settings live in the approved NabdhGram feature
# hub, not in upstream Telegram Settings rows. Keep brand and core untouched.
hub = ui / "NabdhGramSettingsActivity.java"
s = hub.read_text(encoding="utf-8")
s = patch(s,
    """        section(context, content, R.string.NabdhAppearanceTitle, R.string.NabdhAppearanceExplanation);""",
    """        section(context, content, R.string.NabdhAppearanceTitle, R.string.NabdhAppearanceExplanation);
        section(context, content, R.string.NabdhIntelligenceTitle, R.string.NabdhIntelligenceDescription);""",
    "Intelligence hub card")
hub.write_text(s, encoding="utf-8")

page = ui / "NabdhGramFeatureCategoryActivity.java"
s = page.read_text(encoding="utf-8")
# Earlier official appearance overlay already introduces an Appearance block
# between Privacy and the native fragmentView assignment. Attach our
# additional controls at the stable end-of-content anchor instead of
# assuming adjacent if statements from the unmodified feature page.
s = patch(s,
    """        fragmentView = scroll;""",
    """        if (titleRes == R.string.NabdhAppearanceTitle) {
            addNabdhGlassPresets(context, content);
        }
        if (titleRes == R.string.NabdhIntelligenceTitle) {
            addNabdhLensTools(context, content);
        }
        fragmentView = scroll;""",
    "feature category routes")
point = "    private void addPrivacyControls(Context context, LinearLayout content) {"
additional = """    private int nabdhDp(Context context, int dp) {
        return Math.round(dp * context.getResources().getDisplayMetrics().density);
    }

    private void addNabdhGlassPresets(Context context, LinearLayout content) {
        final int[] titleRes = { R.string.NabdhSoftGlass, R.string.NabdhLiquidGlass,
                                 R.string.NabdhCrystalGlass };
        final TextView[] choices = new TextView[3];
        for (int i = 0; i < 3; ++i) {
            final int preset = i;
            final TextView row = new TextView(context);
            choices[i] = row;
            row.setGravity(android.view.Gravity.CENTER_VERTICAL);
            row.setTextSize(16);
            row.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            row.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
            row.setPadding(nabdhDp(context, 25), nabdhDp(context, 18),
                           nabdhDp(context, 25), nabdhDp(context, 18));
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
            params.bottomMargin = nabdhDp(context, 8);
            content.addView(row, params);
            row.setOnClickListener(v -> {
                org.telegram.ui.Components.NabdhGlassStyle.choose(context, preset);
                for (int k = 0; k < 3; ++k) {
                    choices[k].setText(nabdhText(context, titleRes[k]) +
                        (k == preset ? "  ✓" : ""));
                }
            });
        }
        final int current = org.telegram.ui.Components.NabdhGlassStyle.current();
        for (int i = 0; i < 3; ++i) {
            choices[i].setText(nabdhText(context, titleRes[i]) +
                    (i == current ? "  ✓" : ""));
        }
        TextView note = new TextView(context);
        note.setText(nabdhText(context, R.string.NabdhGlassPresetNote));
        note.setTextSize(13);
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        content.addView(note);
    }

    private void addNabdhLensTools(Context context, LinearLayout content) {
        android.widget.Switch toggle = new android.widget.Switch(context);
        toggle.setText(nabdhText(context, R.string.NabdhLensSwitch));
        toggle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        toggle.setChecked(org.telegram.ui.Components.NabdhGlassStyle.lensEnabled(context));
        toggle.setOnCheckedChangeListener((button, enabled) ->
            org.telegram.ui.Components.NabdhGlassStyle.setLensEnabled(context, enabled));
        content.addView(toggle);

        TextView note = new TextView(context);
        note.setText(nabdhText(context, R.string.NabdhLensPrivacyNote));
        note.setTextSize(13);
        note.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText2));
        LinearLayout.LayoutParams noteParams = new LinearLayout.LayoutParams(-1, -2);
        noteParams.topMargin = nabdhDp(context, 12);
        content.addView(note, noteParams);

        android.widget.EditText input = new android.widget.EditText(context);
        input.setTextSize(15);
        input.setMinLines(3);
        input.setMaxLines(8);
        input.setGravity(android.view.Gravity.TOP);
        input.setHint(nabdhText(context, R.string.NabdhLensSampleHint));
        input.setInputType(android.text.InputType.TYPE_CLASS_TEXT |
                           android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        LinearLayout.LayoutParams editParams = new LinearLayout.LayoutParams(-1, -2);
        editParams.topMargin = nabdhDp(context, 18);
        content.addView(input, editParams);

        TextView run = new TextView(context);
        run.setGravity(android.view.Gravity.CENTER);
        run.setText(nabdhText(context, R.string.NabdhLensAnalyze));
        run.setTextSize(16);
        run.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        run.setPadding(nabdhDp(context, 24), nabdhDp(context, 16),
                       nabdhDp(context, 24), nabdhDp(context, 16));
        run.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        LinearLayout.LayoutParams runParams = new LinearLayout.LayoutParams(-1, -2);
        runParams.topMargin = nabdhDp(context, 16);
        content.addView(run, runParams);
        run.setOnClickListener(v -> {
            if (!org.telegram.ui.Components.NabdhContextLens.show(context, input.getText(),
                text -> { input.setText(text); input.setSelection(input.length()); })) {
                android.widget.Toast.makeText(context, nabdhText(context, R.string.NabdhLensEmpty),
                    android.widget.Toast.LENGTH_SHORT).show();
            }
        });
    }

"""
s = patch(s, point, additional + point, "feature page controls")
page.write_text(s, encoding="utf-8")

# Both locales are true Android strings, not arbitrary server-side Telegram
# language-pack keys. No personal content is ever placed in string resources.
translations = {
    "values": {
        "NabdhIntelligenceTitle": "Nabdh Intelligence",
        "NabdhIntelligenceDescription": "Local text tools; native Telegram AI and voice remain separate",
        "NabdhSoftGlass": "Soft Glass — quiet and efficient",
        "NabdhLiquidGlass": "Liquid Glass — balanced depth",
        "NabdhCrystalGlass": "Crystal Glass — vivid highlights",
        "NabdhGlassPresetNote": "Theme colors and original bubble shapes are always preserved. Changes apply to the next chat drawing pass.",
        "NabdhLensSwitch": "Show Lens and AI Editor for short drafts",
        "NabdhLensPrivacyNote": "Long-press the native AI Editor icon to open local Lens tools. Message text stays on device. Google ML Kit may send usage metrics, not text; Telegram AI Editor and translation may use Telegram services. No generative model is bundled.",
        "NabdhLensSampleHint": "Enter or paste text for a local summary, task extraction, link hints or spacing cleanup",
        "NabdhLensAnalyze": "Open local Context Lens",
        "NabdhLensEmpty": "Type or paste some text first"
    },
    "values-ar": {
        "NabdhIntelligenceTitle": "ذكاء نبض",
        "NabdhIntelligenceDescription": "أدوات نصية محلية مع الحفاظ على وظائف Telegram الأصلية",
        "NabdhSoftGlass": "زجاج هادئ — خفيف وسريع",
        "NabdhLiquidGlass": "زجاج سائل — عمق متوازن",
        "NabdhCrystalGlass": "زجاج بلوري — انعكاسات أوضح",
        "NabdhGlassPresetNote": "تظل ألوان الثيم وشكل الفقاعات الأصلي محفوظة. يظهر الاختيار في الرسم التالي للمحادثة.",
        "NabdhLensSwitch": "إظهار العدسة ومحرر الكتابة مع النصوص القصيرة",
        "NabdhLensPrivacyNote": "اضغط مطولًا على أيقونة محرر الذكاء لفتح الأدوات المحلية. يبقى نص الرسالة على جهازك. قد ترسل حزمة Google ML Kit مقاييس استخدام دون النص، وقد تستخدم خدمات Telegram الأصلية خوادمها. لا يوجد نموذج توليدي مدمج.",
        "NabdhLensSampleHint": "اكتب أو الصق نصًا لتلخيص مقتطفاته أو استخراج مهامه أو فحص مؤشرات الروابط وتنظيمه",
        "NabdhLensAnalyze": "فتح عدسة نبض المحلية",
        "NabdhLensEmpty": "اكتب نصًا أولًا"
    }
}
from xml.sax.saxutils import escape
for locale, entries in translations.items():
    dest = root / "TMessagesProj/src/main/res" / locale / "nabdh_liquid_intelligence.xml"
    if dest.exists():
        raise SystemExit(f"Unexpected duplicate app translation: {locale}")
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    lines += [f'    <string name="{key}">{escape(val)}</string>'
              for key, val in entries.items()]
    lines.append('</resources>')
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("PASS: Nabdh Liquid Glass 3 presets and opt-in offline Context Lens over native Telegram UI")
