#!/usr/bin/env python3
"""Route Telegram's bundled Roboto font requests through the selected NabdhGram font.

The change is intentionally limited to AndroidUtilities.getTypeface; Android
system fonts and special-purpose typefaces remain untouched.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-global-font.py TELEGRAM_SOURCE")
p = Path(sys.argv[1]) / "TMessagesProj/src/main/java/org/telegram/messenger/AndroidUtilities.java"
s = p.read_text(encoding="utf-8")
bold_anchor = "    public static Typeface bold() {\n"
if s.count(bold_anchor) != 1:
    raise SystemExit("AndroidUtilities.bold anchor changed")
bold_replacement = """    public static Typeface bold() {
        // A saved custom font must take priority over Android's cached
        // mediumTypeface. This also refreshes headings when users switch fonts.
        if (ApplicationLoader.applicationContext != null) {
            String selectedFamily = ApplicationLoader.applicationContext
                    .getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
                    .getString("font_family", "system-default");
            if (!"system-default".equals(selectedFamily)) {
                Typeface chosenBold = getTypeface(TYPEFACE_ROBOTO_MEDIUM);
                if (chosenBold != null) {
                    return chosenBold;
                }
            }
        }
"""
s = s.replace(bold_anchor, bold_replacement, 1)
anchor = "    public static Typeface getTypeface(String assetPath) {\n"
if s.count(anchor) != 1:
    raise SystemExit("AndroidUtilities.getTypeface anchor changed")
replacement = """    private static final java.util.HashMap<String, Typeface> nabdhFontCache = new java.util.HashMap<>();

    public static Typeface getTypeface(String assetPath) {
        // NabdhGram: honor the persisted font choice for Telegram's Roboto
        // text assets. Leave monospace, icon and other specialty fonts alone.
        if (assetPath != null && (assetPath.equals("fonts/rmedium.ttf")
                || assetPath.equals("fonts/rregular.ttf")
                || assetPath.equals("fonts/rextrabold.ttf")
                || assetPath.equals("fonts/rmediumitalic.ttf"))) {
            if (ApplicationLoader.applicationContext != null) {
                String family = ApplicationLoader.applicationContext
                        .getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
                        .getString("font_family", "system-default");
                boolean userBold = ApplicationLoader.applicationContext
                        .getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
                        .getBoolean("font_bold", false);
                // Custom families start Regular: bold is a user opt-in only.
                boolean bold = userBold;
                boolean italic = assetPath.contains("italic");
                String cacheKey = family + ":" + bold + ":" + italic;
                synchronized (nabdhFontCache) {
                    Typeface cached = nabdhFontCache.get(cacheKey);
                    if (cached != null) {
                        return cached;
                    }
                    Typeface selected = null;
                    if ("system-default".equals(family)) {
                        selected = Typeface.create(Typeface.DEFAULT,
                                (bold ? Typeface.BOLD : Typeface.NORMAL)
                                | (italic ? Typeface.ITALIC : Typeface.NORMAL));
                    } else if ("sans-serif".equals(family) || "serif".equals(family)) {
                        selected = Typeface.create(family,
                                (bold ? Typeface.BOLD : Typeface.NORMAL)
                                | (italic ? Typeface.ITALIC : Typeface.NORMAL));
                    } else if ("readex-pro".equals(family) || "vazirmatn".equals(family)
                            || "noto-sans-arabic".equals(family) || "tajawal".equals(family)
                            || "rubik".equals(family)) {
                        String fontFile = "vazirmatn".equals(family) ? "Vazirmatn.ttf"
                                : "noto-sans-arabic".equals(family) ? "NotoSansArabic.ttf"
                                : "tajawal".equals(family) ? "Tajawal.ttf"
                                : "rubik".equals(family) ? "Rubik.ttf" : "ReadexPro.ttf";
                        Typeface bundled = getTypeface("fonts/" + fontFile);
                        if (bundled != null) {
                            selected = Typeface.create(bundled,
                                    (bold ? Typeface.BOLD : Typeface.NORMAL)
                                    | (italic ? Typeface.ITALIC : Typeface.NORMAL));
                        }
                    }
                    if (selected != null) {
                        nabdhFontCache.put(cacheKey, selected);
                        return selected;
                    }
                }
            }
        }
"""
s=s.replace(anchor,replacement,1)
p.write_text(s,encoding="utf-8")
print("NabdhGram font selection wired into Telegram bundled text typefaces.")
