#!/usr/bin/env python3
"""Fix Telegram ProfileActivity biography's obsolete white bottom shadow.

The public AboutLinkCell is shared: keep Telegram's existing drawing in other
contexts, and opt out of the white gradient only when ProfileActivity's
native AboutLinkCell is used as a NabdhGram Glass card. Preserve links, text
measurement, expand/collapse, touch and accessibility.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-profile-bio-glass.py TELEGRAM_SOURCE")
root = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram/ui"

def replace_exact(source, old, new, name):
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{name}: expected 1 pinned native anchor, found {count}")
    return source.replace(old, new, 1)

cell = root / "Cells/AboutLinkCell.java"
source = cell.read_text(encoding="utf-8")
source = replace_exact(
    source,
    "    private FrameLayout bottomShadow;",
    """    private FrameLayout bottomShadow;
    private boolean nabdhProfileGlass;""",
    "AboutLinkCell shadow state")
source = replace_exact(
    source,
    "    private void setShowMoreMarginBottom(int marginBottom) {",
    """    public void nabdhSetProfileGlass(boolean enabled) {
        // The native 12dp white gradient_bottom leaks beneath our rounded
        // transparent profile bio card. Keep the ripple and text interactions.
        nabdhProfileGlass = enabled;
        if (enabled) {
            // The original native selector is rectangular and extends past
            // the inset Glass card. Mask both tap and long-press tint exactly
            // to the rounded 10dp horizontal / 2dp vertical card bounds.
            android.graphics.drawable.GradientDrawable nabdhMask =
                    new android.graphics.drawable.GradientDrawable();
            nabdhMask.setColor(android.graphics.Color.WHITE);
            nabdhMask.setCornerRadius(org.telegram.messenger.AndroidUtilities.dp(20));
            rippleBackground = new android.graphics.drawable.RippleDrawable(
                    android.content.res.ColorStateList.valueOf(
                            Theme.getColor(Theme.key_listSelector, resourcesProvider)),
                    null, new android.graphics.drawable.InsetDrawable(nabdhMask,
                            org.telegram.messenger.AndroidUtilities.dp(10),
                            org.telegram.messenger.AndroidUtilities.dp(2),
                            org.telegram.messenger.AndroidUtilities.dp(10),
                            org.telegram.messenger.AndroidUtilities.dp(2)));
            if (container.getBackground() != null) {
                container.setBackground(rippleBackground);
            }
        }
        if (bottomShadow != null) {
            bottomShadow.setVisibility(enabled ? GONE : VISIBLE);
        }
        invalidate();
    }

    private void setShowMoreMarginBottom(int marginBottom) {""",
    "AboutLinkCell explicit Glass opt-in")
source = replace_exact(
    source,
    """        viewAlpha = bottomShadow.getAlpha();
        if (viewAlpha > 0) {""",
    """        viewAlpha = bottomShadow.getAlpha();
        if (!nabdhProfileGlass && viewAlpha > 0) {""",
    "AboutLinkCell manual native shadow draw")
cell.write_text(source, encoding="utf-8")

profile = root / "ProfileActivity.java"
source = profile.read_text(encoding="utf-8")
anchor = """                    };
                    break;
                }
                case VIEW_TYPE_TEXT: {"""
updated = """                    };
                    // All ProfileActivity biographies use the approved
                    // Glass card; suppress only their native white gradient.
                    aboutLinkCell.nabdhSetProfileGlass(true);
                    break;
                }
                case VIEW_TYPE_TEXT: {"""
source = replace_exact(source, anchor, updated,
                       "ProfileActivity ABOUT_LINK construction")
profile.write_text(source, encoding="utf-8")
print("PASS: scoped ProfileActivity biography Glass has no native white bottom shadow")
