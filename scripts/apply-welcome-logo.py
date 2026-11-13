#!/usr/bin/env python3
"""Replace the first-page Telegram intro animation with the approved transparent NabdhGram logo.

Usage: python3 scripts/apply-welcome-logo.py TELEGRAM_SOURCE PNG_FILE
Run AFTER apply-welcome.py. Keeps the original animations on pages 2-6.
"""
from pathlib import Path
import sys

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"Expected exactly one {label}; found {n}")
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: apply-welcome-logo.py TELEGRAM_SOURCE TRANSPARENT_PNG")
    root, asset = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    source = root / "TMessagesProj/src/main/java/org/telegram/ui/IntroActivity.java"
    drawable = root / "TMessagesProj/src/main/res/drawable-nodpi/nabdhgram_welcome_logo.png"
    if not source.is_file() or not asset.is_file():
        raise SystemExit("Missing pinned Telegram IntroActivity or approved PNG")
    data = asset.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("Welcome logo must be a PNG")
    # Android BitmapFactory handles transparency; require RGBA/GA PNG, not an opaque background.
    from PIL import Image
    with Image.open(asset) as im:
        if im.width < 512 or im.height < 512 or im.mode not in ("RGBA", "LA", "P"):
            raise SystemExit("Welcome logo must be >=512px with transparency")
        if (im.getextrema()[-1][0] == 255) if im.mode in ("RGBA", "LA") else ("transparency" not in im.info):
            raise SystemExit("Welcome logo has no transparent pixels")
    # Trim excessive transparent canvas padding without changing the approved artwork.
    # Preserve an 8% transparent safety margin so the icon is never cropped.
    with Image.open(asset) as im:
        rgba = im.convert("RGBA")
        alpha = rgba.getchannel("A")
        bounds = alpha.getbbox()
        if bounds is None:
            raise SystemExit("Welcome logo PNG contains no visible artwork")
        left, top, right, bottom = bounds
        w, h = right - left, bottom - top
        side = max(w, h)
        pad = max(1, round(side * 0.08))
        normalized = Image.new("RGBA", (side + pad * 2, side + pad * 2), (0, 0, 0, 0))
        normalized.alpha_composite(rgba.crop(bounds), ((side - w) // 2 + pad, (side - h) // 2 + pad))
    content = source.read_text(encoding="utf-8")
    content = replace_once(content,
        "import android.widget.FrameLayout;",
        "import android.widget.FrameLayout;\nimport android.widget.ImageView;",
        "ImageView import")
    content = replace_once(content,
        "    private FrameLayout frameLayout2;",
        "    private FrameLayout frameLayout2;\n    private ImageView nabdhgramWelcomeLogo;",
        "intro fields")
    content = replace_once(content,
        "        frameLayout2.addView(textureView, LayoutHelper.createFrame(ICON_WIDTH_DP, ICON_HEIGHT_DP, Gravity.CENTER));",
        """        frameLayout2.addView(textureView, LayoutHelper.createFrame(ICON_WIDTH_DP, ICON_HEIGHT_DP, Gravity.CENTER));
        // Opaque themed cover prevents the underlying Telegram EGL artwork from
        // showing through the transparent PNG. Keep TextureView attached and visible
        // for native EGL lifecycle and the remaining intro pages.
        FrameLayout nabdhgramCover = new FrameLayout(context);
        // NabdhGram Glass: a soft brand gradient behind the approved logo.
        int nabdhBase = Theme.getColor(Theme.key_windowBackgroundWhite);
        boolean nabdhDark = android.graphics.Color.red(nabdhBase)
                + android.graphics.Color.green(nabdhBase)
                + android.graphics.Color.blue(nabdhBase) < 360;
        android.graphics.drawable.GradientDrawable nabdhGlass = new android.graphics.drawable.GradientDrawable(
                android.graphics.drawable.GradientDrawable.Orientation.TL_BR,
                nabdhDark ? new int[] {0xFF082A34, 0xFF116B74} : new int[] {0xFFE8F9F7, 0xFFBCEBE6});
        nabdhGlass.setCornerRadius(AndroidUtilities.dp(26));
        nabdhgramCover.setBackground(nabdhGlass);
        frameLayout2.addView(nabdhgramCover,
                LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, ICON_HEIGHT_DP, Gravity.CENTER));
        nabdhgramWelcomeLogo = new ImageView(context);
        nabdhgramWelcomeLogo.setImageResource(R.drawable.nabdhgram_welcome_logo);
        nabdhgramWelcomeLogo.setScaleType(ImageView.ScaleType.FIT_CENTER);
        nabdhgramCover.addView(nabdhgramWelcomeLogo,
                LayoutHelper.createFrame(270, 270, Gravity.CENTER));
        nabdhgramCover.setTag("nabdhgramWelcomeCover");
        // Cover is hidden on subsequent pages; native animations remain unchanged.""",
        "intro texture view")
    content = replace_once(content,
        """            public void onPageSelected(int i) {
                currentViewPagerPage = i;
            }""",
        """            public void onPageSelected(int i) {
                currentViewPagerPage = i;
                if (nabdhgramWelcomeLogo != null) {
                    View cover = (View) nabdhgramWelcomeLogo.getParent();
                    cover.setVisibility(i == 0 ? View.VISIBLE : View.GONE);
                    // TextureView remains attached and visible for native EGL.
                }
            }""",
        "page selection")
    drawable.parent.mkdir(parents=True, exist_ok=True)
    if drawable.exists():
        raise SystemExit("Refusing to overwrite existing welcome logo")
    normalized.save(drawable, format="PNG")
    # Telegram 13.2.x has both updateColors() and onThemeColorsChanged().
    # Match the precise method context rather than counting a shared line
    # across the entire class. The latter is optional on older pinned builds.
    cover_color_refresh = """        if (nabdhgramWelcomeLogo != null
                && nabdhgramWelcomeLogo.getParent() instanceof View) {
            ((View) nabdhgramWelcomeLogo.getParent()).setBackgroundColor(
                    Theme.getColor(Theme.key_windowBackgroundWhite));
        }
"""
    original_update = """        fragmentView.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        switchLanguageTextView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText4));"""
    refreshed_update = """        fragmentView.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
""" + cover_color_refresh + """        switchLanguageTextView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText4));"""
    content = replace_once(content, original_update, refreshed_update,
                           "updateColors welcome-cover theme callback")
    # From Telegram 13.2.x: onThemeColorsChanged updates the same color
    # separately, so update the cover there as well (without touching UI
    # elsewhere or changing how the native theme is selected).
    newer_theme_anchor = """            fragmentView.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
            if (switchLanguageTextView != null) {"""
    if content.count(newer_theme_anchor) == 1:
        content = content.replace(newer_theme_anchor,
            """            fragmentView.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
            if (nabdhgramWelcomeLogo != null
                    && nabdhgramWelcomeLogo.getParent() instanceof View) {
                ((View) nabdhgramWelcomeLogo.getParent()).setBackgroundColor(
                        Theme.getColor(Theme.key_windowBackgroundWhite));
            }
            if (switchLanguageTextView != null) {""", 1)
    elif content.count(newer_theme_anchor) != 0:
        raise SystemExit("Ambiguous newer Telegram intro color callback")
    source.write_text(content, encoding="utf-8")
    print("First welcome page: approved transparent NabdhGram logo. Other pages retain upstream animation.")

if __name__ == "__main__":
    main()
