#!/usr/bin/env python3
"""NabdhGram login polish and privacy-safe verification delivery diagnostics.

Only adjusts Android views and draws; original Telegram auth RPC, retry
timers, server-selected delivery channel, validation and input listeners remain.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-glass-login-finish.py TELEGRAM_SOURCE")
root = Path(sys.argv[1])
login = root / "TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java"
keyboard = root / "TMessagesProj/src/main/java/org/telegram/ui/Components/CustomPhoneKeyboardView.java"
code_fields = root / "TMessagesProj/src/main/java/org/telegram/ui/CodeFieldContainer.java"

def replace_once(source, original, replacement, label):
    count = source.count(original)
    if count != 1:
        raise SystemExit(f"{label}: expected one upstream anchor, found {count}")
    return source.replace(original, replacement, 1)

s = login.read_text(encoding="utf-8")
s = replace_once(s,
    "                nabdhLoginLogo.setScaleType(ImageView.ScaleType.FIT_CENTER);",
    """                nabdhLoginLogo.setScaleType(ImageView.ScaleType.FIT_CENTER);
                // Lift the actual approved logo slightly, not the form controls.
                nabdhLoginLogo.setTranslationY(-dp(14));""",
    "approved artwork position")
s = replace_once(s,
    "Gravity.CENTER_HORIZONTAL, 0, 0, 0, 12));",
    "Gravity.CENTER_HORIZONTAL, 0, 0, 0, 4));",
    "logo to heading spacing")
# PhoneView is not the only LoginActivity view with a titleView. Edit only
# the title declared directly inside PhoneView, never recovery or SMS screens.
phone_ctor = "        public PhoneView(Context context) {"
if s.count(phone_ctor) != 1:
    raise SystemExit("PhoneView constructor changed")
phone_pos = s.index(phone_ctor)
phone_title = "            titleView = new TextView(context);\\n            titleView.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 18);"
title_pos = s.find(phone_title, phone_pos)
if title_pos < 0 or title_pos - phone_pos > 1600:
    raise SystemExit("PhoneView title anchor changed")
s = s[:title_pos] + phone_title.replace("18);", "19);") + s[title_pos + len(phone_title):]
s = replace_once(s,
    "addView(subtitleView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL, 32, 8, 32, 0));",
    "addView(subtitleView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL, 28, 7, 28, 0));",
    "phone subtitle spacing")
s = replace_once(s,
    "addView(countryOutlineView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 58, 16, 24, 16, 14));",
    "addView(countryOutlineView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 58, 16, 20, 16, 8));",
    "country input top and bottom gaps")
s = replace_once(s,
    "addView(phoneOutlineView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 58, 16, 8, 16, 8));",
    "addView(phoneOutlineView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 58, 16, 8, 16, 8));",
    "phone input geometry") if False else s

# Refined back arrow surface, using built-in Telegram glyphs, keeping click area
# and exit behavior exactly intact.
s = replace_once(s,
    "        backButtonView.setImageResource(R.drawable.ic_ab_back);",
    """        backButtonView.setImageResource(R.drawable.ic_ab_back);
        backButtonView.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        android.graphics.drawable.GradientDrawable nabdhBackGlass =
                new android.graphics.drawable.GradientDrawable();
        int nabdhNavTint = Theme.getColor(Theme.key_listSelector);
        nabdhBackGlass.setColor(android.graphics.Color.argb(67,
                android.graphics.Color.red(nabdhNavTint),
                android.graphics.Color.green(nabdhNavTint),
                android.graphics.Color.blue(nabdhNavTint)));
        nabdhBackGlass.setCornerRadius(dp(14));
        backButtonView.setBackground(nabdhBackGlass);""",
    "navigation button icon")

# Telegram uses a special 1.5dp border around each OTP box. Color and corner
# radius can be polished without disturbing the code selection or timers.
s = replace_once(s,
    "addView(codeFieldContainer, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, 42, Gravity.CENTER_HORIZONTAL, 0, 32, 0, 0));",
    "codeFieldContainer.setNabdhLoginGlass(true);\\n                addView(codeFieldContainer, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, 42, Gravity.CENTER_HORIZONTAL, 0, 32, 0, 0));",
    "code input boxes main") if False else s
# Ensure every login verification box gets the same visual treatment; no
# edits to the constructors or to processNextPressed() callbacks.
code_add = "addView(codeFieldContainer, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, 42, Gravity.CENTER_HORIZONTAL, 0, 32, 0, 0));"
if s.count(code_add) != 2:
    raise SystemExit(f"Standard code-layout count changed: {s.count(code_add)}")
s = s.replace(code_add,
        "codeFieldContainer.setNabdhLoginGlass(true);\n                " + code_add)
email_add = "addView(codeFieldContainer, LayoutHelper.createLinear(LayoutHelper.WRAP_CONTENT, 42, Gravity.CENTER_HORIZONTAL, 0, setup ? 48 : 32, 0, 0));"
if s.count(email_add) != 1:
    raise SystemExit("Email code field layout changed")
s = s.replace(email_add,
        "codeFieldContainer.setNabdhLoginGlass(true);\n            " + email_add, 1)

# Non-sensitive route diagnostic: records only Telegram TL code type, available
# fallback type and numeric RPC status. Does NOT log phone, code, hash, api hash,
# SMS contents, account ID, passwords or authorization tokens.
route_anchor = "        if (res.type instanceof TLRPC.TL_auth_sentCodeTypeFirebaseSms && !res.type.verifiedFirebase && !isRequestingFirebaseSms) {"
route_trace = """        if (BuildVars.LOGS_ENABLED) {
            FileLog.d("NabdhGram auth delivery type="
                    + (res.type == null ? "none" : res.type.getClass().getSimpleName())
                    + " next="
                    + (res.next_type == null ? "none" : res.next_type.getClass().getSimpleName()));
        }
"""
s = replace_once(s, route_anchor, route_trace + route_anchor, "auth route diagnostic")
request_anchor = """            int reqId = ConnectionsManager.getInstance(currentAccount).sendRequest(req, (response, error) -> AndroidUtilities.runOnUIThread(() -> {
                nextPressed = false;"""
request_trace = """            int reqId = ConnectionsManager.getInstance(currentAccount).sendRequest(req, (response, error) -> AndroidUtilities.runOnUIThread(() -> {
                nextPressed = false;
                if (BuildVars.LOGS_ENABLED) {
                    FileLog.d("NabdhGram auth sendCode: " + (error == null
                            ? "accepted" : "server_or_network_error_code_" + error.code));
                }"""
# The same callback syntax exists in other auth stages; target only the
# phone entry request after TL_auth_sendCode, never the other requests.
phone_send_anchor = "TLRPC.TL_auth_sendCode sendCode = new TLRPC.TL_auth_sendCode();"
if s.count(phone_send_anchor) != 1:
    raise SystemExit("Phone auth_sendCode constructor changed")
before_send, after_send = s.split(phone_send_anchor, 1)
if request_anchor not in after_send:
    raise SystemExit("Phone sendCode callback changed")
after_send = after_send.replace(request_anchor, request_trace, 1)
s = before_send + phone_send_anchor + after_send
login.write_text(s,encoding="utf-8")

k = keyboard.read_text(encoding="utf-8")
k = replace_once(k,
    "private final static int SIDE_PADDING = 10, BUTTON_PADDING = 6;",
    "private final static int SIDE_PADDING = 12, BUTTON_PADDING = 7;",
    "keypad breathing room")
k = replace_once(k,
    """        final int defaultColor = Theme.getColor(Theme.key_listSelector);
        final int pressedColor = ColorUtils.setAlphaComponent(Theme.getColor(Theme.key_listSelector), 30);""",
    """        // Genuine translucent keypad, not an overlay blocking key presses.
        // Selected-theme colors make light, dark and imported Glass work.
        final int defaultColor = ColorUtils.setAlphaComponent(
                Theme.getColor(Theme.key_listSelector), 138);
        final int pressedColor = ColorUtils.setAlphaComponent(
                Theme.getColor(Theme.key_windowBackgroundWhiteBlueText), 73);""",
    "keypad translucent key paints")
k = replace_once(k,
    "dp(isRight && isTop ? 24 : 12),",
    "dp(isRight && isTop ? 24 : 17),",
    "top-right key corners")
k = replace_once(k,
    "dp(isLeft && isTop ? 24 : 12),",
    "dp(isLeft && isTop ? 24 : 17),",
    "top-left key corners")
k = replace_once(k,
    "dp(isRight && isBottom ? 24 : 12),",
    "dp(isRight && isBottom ? 24 : 17),",
    "bottom-right key corners")
k = replace_once(k,
    "dp(/*index == 10 || index == 6 ||*/ isLeft && isBottom ? 24 : 12),",
    "dp(isLeft && isBottom ? 24 : 17),",
    "bottom-left key corners")
# Constructor and updateColors both tint the same icon; handle both.
backspace_icon = "backButton.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));"
if k.count(backspace_icon) != 2:
    raise SystemExit("Backspace icon anchors changed")
k = k.replace(backspace_icon,
    "backButton.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));")
k = replace_once(k,
    "numberTextPaint.setTextSize(dp(24));",
    "numberTextPaint.setTextSize(dp(23));",
    "numeric key size")
k = replace_once(k,
    "symbolsTextPaint.setTextSize(dp(14));",
    "symbolsTextPaint.setTextSize(dp(12));",
    "key secondary letters")
keyboard.write_text(k, encoding="utf-8")

f = code_fields.read_text(encoding="utf-8")
f = replace_once(f,
    "    Paint bitmapPaint = new Paint(Paint.ANTI_ALIAS_FLAG);",
    """    Paint bitmapPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private boolean nabdhLoginGlass;
    private final Paint nabdhLoginFill = new Paint(Paint.ANTI_ALIAS_FLAG);
    public void setNabdhLoginGlass(boolean enabled) {
        nabdhLoginGlass = enabled;
        invalidate();
    }""",
    "OTP visuals opt-in")
f = replace_once(f,
    "                canvas.drawRoundRect(AndroidUtilities.rectTmp, AndroidUtilities.dp(4), AndroidUtilities.dp(4), paint);",
    """                if (nabdhLoginGlass) {
                    int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
                    nabdhLoginFill.setColor(android.graphics.Color.argb(22,
                            android.graphics.Color.red(accent),
                            android.graphics.Color.green(accent),
                            android.graphics.Color.blue(accent)));
                    canvas.drawRoundRect(AndroidUtilities.rectTmp, AndroidUtilities.dp(9),
                            AndroidUtilities.dp(9), nabdhLoginFill);
                }
                canvas.drawRoundRect(AndroidUtilities.rectTmp,
                        AndroidUtilities.dp(nabdhLoginGlass ? 9 : 4),
                        AndroidUtilities.dp(nabdhLoginGlass ? 9 : 4), paint);""",
    "verification field outlines")
code_fields.write_text(f,encoding="utf-8")
print("Glass login polished: raised logo, compact fields, tinted nav, translucent keypad, rounded code inputs, safe delivery diagnostics.")
