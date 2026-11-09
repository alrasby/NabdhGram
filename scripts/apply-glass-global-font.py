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
anchor = "    public static Typeface getTypeface(String assetPath) {\n"
if s.count(anchor) != 1:
    raise SystemExit("AndroidUtilities.getTypeface anchor changed")
replacement = """    public static Typeface getTypeface(String assetPath) {
        // NabdhGram: honor the persisted font choice for Telegram's Roboto
        // text assets. Leave monospace, icon and other specialty fonts alone.
        if (assetPath != null && (assetPath.equals("fonts/rmedium.ttf")
                || assetPath.equals("fonts/rregular.ttf")
                || assetPath.equals("fonts/rextrabold.ttf")
                || assetPath.equals("fonts/rmediumitalic.ttf"))) {
            String family = ApplicationLoader.applicationContext
                    .getSharedPreferences("nabdhgram_appearance", Context.MODE_PRIVATE)
                    .getString("font_family", "readex-pro");
            if ("sans-serif".equals(family) || "serif".equals(family)) {
                boolean bold = assetPath.contains("medium") || assetPath.contains("extrabold");
                return Typeface.create(family, bold ? Typeface.BOLD : Typeface.NORMAL);
            }
            if ("readex-pro".equals(family)) {
                Typeface bundled = getTypeface("fonts/ReadexPro.ttf");
                if (bundled != null) {
                    boolean bold = assetPath.contains("medium") || assetPath.contains("extrabold");
                    return Typeface.create(bundled, bold ? Typeface.BOLD : Typeface.NORMAL);
                }
            }
        }
"""
s=s.replace(anchor,replacement,1)
p.write_text(s,encoding="utf-8")
print("NabdhGram font selection wired into Telegram bundled text typefaces.")
