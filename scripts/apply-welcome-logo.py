#!/usr/bin/env python3
"""Replace the first-page Telegram intro animation with the approved transparent NabdhGram logo.

Usage: python3 scripts/apply-welcome-logo.py TELEGRAM_SOURCE PNG_FILE
Run AFTER apply-welcome.py. Keeps the original animations on pages 2-6.
"""
from pathlib import Path
import shutil
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
    content = source.read_text(encoding="utf-8")
    content = replace_once(content,
        "import android.widget.FrameLayout;",
        "import android.widget.FrameLayout;\nimport android.widget.ImageView;",
        "ImageView import")
    content = replace_once(content,
        "    private FrameLayout frameLayout2;",
        "    private FrameLayout frameLayout2;\n    private ImageView nabdhgramWelcomeLogo;\n    private TextureView nabdhgramIntroTexture;",
        "intro fields")
    content = replace_once(content,
        "        frameLayout2.addView(textureView, LayoutHelper.createFrame(ICON_WIDTH_DP, ICON_HEIGHT_DP, Gravity.CENTER));",
        """        frameLayout2.addView(textureView, LayoutHelper.createFrame(ICON_WIDTH_DP, ICON_HEIGHT_DP, Gravity.CENTER));
        nabdhgramIntroTexture = textureView;
        nabdhgramWelcomeLogo = new ImageView(context);
        nabdhgramWelcomeLogo.setImageResource(R.drawable.nabdhgram_welcome_logo);
        nabdhgramWelcomeLogo.setScaleType(ImageView.ScaleType.FIT_CENTER);
        // The PNG already contains the user's approved transparent inset.
        // Match the original intro illustration bounds; do not stretch or crop.
        frameLayout2.addView(nabdhgramWelcomeLogo,
                LayoutHelper.createFrame(ICON_WIDTH_DP, ICON_HEIGHT_DP, Gravity.CENTER));
        // Keep TextureView VISIBLE: upstream EGL initialization and drawing depend on its SurfaceTexture.""",
        "intro texture view")
    content = replace_once(content,
        """            public void onPageSelected(int i) {
                currentViewPagerPage = i;
            }""",
        """            public void onPageSelected(int i) {
                currentViewPagerPage = i;
                if (nabdhgramWelcomeLogo != null && nabdhgramIntroTexture != null) {
                    nabdhgramWelcomeLogo.setVisibility(i == 0 ? View.VISIBLE : View.GONE);
                    // Do not toggle TextureView visibility; changing it destroys the EGL surface on some devices.
                }
            }""",
        "page selection")
    drawable.parent.mkdir(parents=True, exist_ok=True)
    if drawable.exists():
        raise SystemExit("Refusing to overwrite existing welcome logo")
    shutil.copyfile(asset, drawable)
    source.write_text(content, encoding="utf-8")
    print("First welcome page: approved transparent NabdhGram logo. Other pages retain upstream animation.")

if __name__ == "__main__":
    main()
