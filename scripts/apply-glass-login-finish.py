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
    "                nabdhLoginLogo.setScaleType(ImageView.ScaleType.CENTER_CROP);",
    """                nabdhLoginLogo.setScaleType(ImageView.ScaleType.CENTER_CROP);
                // Layout owns the logo position; no translation leaving a
                // ghost-sized hit box or invisible margin under the mark.""",
    "approved artwork position")
s = replace_once(s,
    "Gravity.CENTER_HORIZONTAL, 0, 0, 0, 12));",
    "Gravity.CENTER_HORIZONTAL, 0, 0, 0, 4));",
    "logo to heading spacing")
# Preserve the upstream title text size: prior optional 18->19dp tweak
# depended on a brittle constructor-local anchor and blocked all builds.
# The validated Glass login layout remains applied by the other anchors.
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

# Telegram's public auth API documents Firebase SMS as an official-client
# channel. NabdhGram is a separate API app/package and cannot complete that
# privileged integrity flow. Disable advertising this unsupported capability;
# leave all server-selected ordinary app/SMS/email/voice fallbacks intact.
firebase_original = (
    "settings.allow_app_hash = settings.allow_firebase = "
    "PushListenerController.GooglePushListenerServiceProvider.INSTANCE.hasServices();"
)
firebase_compatible = (
    "settings.allow_app_hash = "
    "PushListenerController.GooglePushListenerServiceProvider.INSTANCE.hasServices();"
    "\n            settings.allow_firebase = false; // Third-party app: no privileged Firebase SMS"
)
if s.count(firebase_original) != 1:
    raise SystemExit("Telegram codeSettings Firebase capability anchor changed")
s = s.replace(firebase_original, firebase_compatible, 1)

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
request_trace = """            final long nabdhSendCodeStartedMs = android.os.SystemClock.elapsedRealtime();
            int reqId = ConnectionsManager.getInstance(currentAccount).sendRequest(req, (response, error) -> AndroidUtilities.runOnUIThread(() -> {
                nextPressed = false;
                if (BuildVars.LOGS_ENABLED) {
                    // Privacy-safe timing only: never log phone, code or auth tokens.
                    FileLog.d("NabdhGram auth sendCode: " + (error == null
                            ? "accepted" : "server_or_network_error_code_" + error.code)
                            + " elapsed_ms=" + (android.os.SystemClock.elapsedRealtime() - nabdhSendCodeStartedMs)
                            + " connection_state=" + getConnectionsManager().getConnectionState());
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

# Pre-auth controls: keep native proxy management and language selection
# available even while MTProto is disconnected.
s = replace_once(s,
    "    private ImageView proxyButtonView;",
    """    private ImageView proxyButtonView;
    private ImageView nabdhLanguageButtonView;""",
    "login language view field")
s = replace_once(s,
    """                marginLayoutParams = (MarginLayoutParams) proxyButtonView.getLayoutParams();
                marginLayoutParams.topMargin = AndroidUtilities.dp(16) + statusBarHeight;""",
    """                marginLayoutParams = (MarginLayoutParams) proxyButtonView.getLayoutParams();
                marginLayoutParams.topMargin = AndroidUtilities.dp(16) + statusBarHeight;
                if (nabdhLanguageButtonView != null) {
                    marginLayoutParams = (MarginLayoutParams) nabdhLanguageButtonView.getLayoutParams();
                    marginLayoutParams.topMargin = AndroidUtilities.dp(16) + statusBarHeight;
                }""",
    "login language safe-area geometry")
s = replace_once(s,
    """        sizeNotifierFrameLayout.addView(proxyButtonView, LayoutHelper.createFrame(32, 32, Gravity.RIGHT | Gravity.TOP, 16, 16, 16, 16));
        updateProxyButton(false, true);""",
    """        proxyButtonView.setContentDescription(getString(R.string.ProxySettings));
        proxyButtonView.setPadding(dp(7), dp(7), dp(7), dp(7));
        sizeNotifierFrameLayout.addView(proxyButtonView,
                LayoutHelper.createFrame(40, 40, Gravity.LEFT | Gravity.TOP, 16, 16, 0, 16));
        nabdhLanguageButtonView = new ImageView(context);
        nabdhLanguageButtonView.setImageResource(R.drawable.nabdh_login_language);
        nabdhLanguageButtonView.setContentDescription(getString(R.string.Language));
        nabdhLanguageButtonView.setPadding(dp(8), dp(8), dp(8), dp(8));
        nabdhLanguageButtonView.setOnClickListener(v -> presentFragment(new LanguageSelectActivity()));
        sizeNotifierFrameLayout.addView(nabdhLanguageButtonView,
                LayoutHelper.createFrame(40, 40, Gravity.LEFT | Gravity.TOP, 68, 16, 0, 16));
        updateProxyButton(false, true);""",
    "native pre-auth language and proxy controls")
s = replace_once(s,
    """        } else if (getMessagesController().blockedCountry && !SharedConfig.proxyList.isEmpty() || connecting) {""",
    """        } else if (activityMode == MODE_LOGIN) {
            proxyDrawable.setConnected(false, connected, animated);
            showProxyButton(true, animated);
        } else if (getMessagesController().blockedCountry && !SharedConfig.proxyList.isEmpty() || connecting) {""",
    "preauth proxy always accessible")
s = replace_once(s,
    """        proxyButtonView.setBackground(Theme.createSelectorDrawable(Theme.getColor(Theme.key_listSelector)));""",
    """        proxyButtonView.setBackground(new android.graphics.drawable.RippleDrawable(
                android.content.res.ColorStateList.valueOf(Theme.getColor(Theme.key_listSelector)),
                nabdhLoginSurface(14, .10f), null));
        if (nabdhLanguageButtonView != null) {
            nabdhLanguageButtonView.setBackground(new android.graphics.drawable.RippleDrawable(
                    android.content.res.ColorStateList.valueOf(Theme.getColor(Theme.key_listSelector)),
                    nabdhLoginSurface(14, .10f), null));
            nabdhLanguageButtonView.setColorFilter(
                    Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        }""",
    "theme-updated native quick controls")
s = replace_once(s,
    """    @Override
    public void onResume() {
        super.onResume();
        if (newAccount) {""",
    """    @Override
    public void onResume() {
        super.onResume();
        if (activityMode == MODE_LOGIN && ApplicationLoader.isNetworkOnline()) {
            // Single preflight on foreground return, no polling/retry loop.
            final ConnectionsManager loginNetwork = getConnectionsManager();
            final int state = loginNetwork.getConnectionState();
            if (state != ConnectionsManager.ConnectionStateConnected
                    && state != ConnectionsManager.ConnectionStateUpdating) {
                loginNetwork.checkConnection();
                loginNetwork.resumeNetworkMaybe();
            }
        }
        if (newAccount) {""",
    "native network preflight")
s = replace_once(s,
    """                ConnectionsManager.getInstance(currentAccount).cleanup(false);

                TLRPC.TL_auth_sendCode sendCode = new TLRPC.TL_auth_sendCode();""",
    """                ConnectionsManager.getInstance(currentAccount).cleanup(false);
                // Wake the original native MTProto transport after reset.
                if (ApplicationLoader.isNetworkOnline()) {
                    ConnectionsManager.getInstance(currentAccount).resumeNetworkMaybe();
                }

                TLRPC.TL_auth_sendCode sendCode = new TLRPC.TL_auth_sendCode();""",
    "MTProto resume after login state cleanup")


# Keep an observable difference between network delay and the native success
# animation after a correct SMS/Telegram code. The original animations delay
# navigation by around 0.7-0.9s. Keep the feedback, halve only its hold time.
if s.count("codeFieldContainer.postDelayed(()-> codeFieldContainer.codeField[finalI].animateSuccessProgress(1f), i * 75L);") != 2:
    raise SystemExit("Telegram successful code animation anchors changed")
s = s.replace(
    "codeFieldContainer.postDelayed(()-> codeFieldContainer.codeField[finalI].animateSuccessProgress(1f), i * 75L);",
    "codeFieldContainer.postDelayed(()-> codeFieldContainer.codeField[finalI].animateSuccessProgress(1f), i * 45L);")
if s.count("}, codeFieldContainer.codeField.length * 75L + 400L);") != 2:
    raise SystemExit("Telegram post-code navigation delay anchors changed")
s = s.replace("}, codeFieldContainer.codeField.length * 75L + 400L);",
              "}, codeFieldContainer.codeField.length * 45L + 180L);")
# Record only the time for Telegram to answer signIn, not the secret code.
auth_anchor = """                    int reqId = ConnectionsManager.getInstance(currentAccount).sendRequest(req, (response, error) -> AndroidUtilities.runOnUIThread(() -> {
                        tryHideProgress(false, true);"""
auth_trace = """                    final long nabdhSignInStartedMs = android.os.SystemClock.elapsedRealtime();
                    int reqId = ConnectionsManager.getInstance(currentAccount).sendRequest(req, (response, error) -> AndroidUtilities.runOnUIThread(() -> {
                        tryHideProgress(false, true);
                        if (BuildVars.LOGS_ENABLED) {
                            FileLog.d("NabdhGram auth signIn elapsed_ms="
                                    + (android.os.SystemClock.elapsedRealtime() - nabdhSignInStartedMs)
                                    + " result=" + (error == null ? "accepted" : "error_code_" + error.code));
                        }"""
# The same callback shape appears in another authorization route.
# Instrument only the SMS/Telegram-code TL_auth_signIn branch, not other flows.
sign_in_anchor = "                    TLRPC.TL_auth_signIn req = new TLRPC.TL_auth_signIn();"
if s.count(sign_in_anchor) != 1:
    raise SystemExit("Telegram SMS auth sign-in branch changed")
sign_in_before, sign_in_after = s.split(sign_in_anchor, 1)
if auth_anchor not in sign_in_after:
    raise SystemExit("Telegram SMS sign-in callback changed")
sign_in_after = sign_in_after.replace(auth_anchor, auth_trace, 1)
s = sign_in_before + sign_in_anchor + sign_in_after

# Measure post-auth local initialization separately from the server RPC.
# Only duration and connection state are logged, never identity or tokens.
post_auth = """    private void onAuthSuccess(TLRPC.TL_auth_authorization res, boolean afterSignup) {
        MessagesController.getInstance(currentAccount).cleanup();"""
post_auth_instrumented = """    private void onAuthSuccess(TLRPC.TL_auth_authorization res, boolean afterSignup) {
        final long nabdhLocalAuthStarted = android.os.SystemClock.elapsedRealtime();
        MessagesController.getInstance(currentAccount).cleanup();"""
s = replace_once(s, post_auth, post_auth_instrumented, "post-auth initialization start")
finish_anchor = """        needFinishActivity(afterSignup, res.setup_password_required, res.otherwise_relogin_days);
    }"""
finish_instrumented = """        if (BuildVars.LOGS_ENABLED) {
            FileLog.d("NabdhGram auth local_init elapsed_ms="
                    + (android.os.SystemClock.elapsedRealtime() - nabdhLocalAuthStarted)
                    + " connection_state=" + getConnectionsManager().getConnectionState());
        }
        needFinishActivity(afterSignup, res.setup_password_required, res.otherwise_relogin_days);
    }"""
s = replace_once(s, finish_anchor, finish_instrumented, "post-auth initialization end")

# The stock SMS view uses a weighted bottomContainer with the resend action
# pinned to its bottom edge, leaving a disproportionately empty middle.
# Center that action inside the flexible region without moving the keypad or
# changing its click handler; this remains responsive on different heights.
s = replace_once(s,
    "bottomContainer.addView(errorViewSwitcher, LayoutHelper.createFrame(currentType == VIEW_CODE_FRAGMENT_SMS ? LayoutHelper.MATCH_PARENT : LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL | Gravity.BOTTOM, 0, 0, 0, 32));",
    "bottomContainer.addView(errorViewSwitcher, LayoutHelper.createFrame(currentType == VIEW_CODE_FRAGMENT_SMS ? LayoutHelper.MATCH_PARENT : LayoutHelper.WRAP_CONTENT, LayoutHelper.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL | Gravity.CENTER_VERTICAL, 0, 0, 0, 0));",
    "SMS resend control vertical alignment")

login.write_text(s,encoding="utf-8")
language_vector = root / "TMessagesProj/src/main/res/drawable/nabdh_login_language.xml"
language_vector.parent.mkdir(parents=True, exist_ok=True)
language_vector.write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#00000000"
        android:strokeColor="#FF101010" android:strokeWidth="1.8"
        android:pathData="M12,2A10,10 0,1 1,12 22A10,10 0,1 1,12 2zM2,12L22,12M12,2C8,6 8,18 12,22M12,2C16,6 16,18 12,22"/>
</vector>
""", encoding="utf-8")

k = keyboard.read_text(encoding="utf-8")
k = replace_once(k,
    "private final static int SIDE_PADDING = 10, BUTTON_PADDING = 6;",
    "private final static int SIDE_PADDING = 10, BUTTON_PADDING = 6;",
    "keypad breathing room")
# The keypad lives in wide grid cells. A corner radius only produces
# horizontal pills; draw an actual circle fitted to the smaller dimension.
# Keep the original NumberButtonView, EditText and backspace listeners.
k = replace_once(k,
    "    private static Drawable getButtonDrawable(int index) {",
    """    // A stateful circle fills its actual centered diameter regardless of
    // the Android key cell's width, avoiding stretched oval/pill keys.
    private static final class NabdhCircleKey extends android.graphics.drawable.Drawable {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final int resting, active;
        private boolean pressed;
        private int alpha = 255;

        NabdhCircleKey(int resting, int active) {
            this.resting = resting;
            this.active = active;
        }

        @Override public boolean isStateful() { return true; }
        @Override protected boolean onStateChange(int[] stateSet) {
            boolean down = false;
            for (int state : stateSet) {
                if (state == android.R.attr.state_pressed || state == android.R.attr.state_focused) {
                    down = true;
                    break;
                }
            }
            if (pressed != down) {
                pressed = down;
                invalidateSelf();
                return true;
            }
            return false;
        }
        @Override public void draw(Canvas canvas) {
            android.graphics.Rect box = getBounds();
            float radius = Math.max(1f, Math.min(box.width(), box.height()) * .5f - dp(1));
            paint.setColor(pressed ? active : resting);
            paint.setAlpha(alpha);
            canvas.drawCircle(box.exactCenterX(), box.exactCenterY(), radius, paint);
        }
        @Override public void setAlpha(int value) { alpha = value; invalidateSelf(); }
        @Override public void setColorFilter(android.graphics.ColorFilter colorFilter) {
            paint.setColorFilter(colorFilter);
            invalidateSelf();
        }
        @Override public int getOpacity() {
            return android.graphics.PixelFormat.TRANSLUCENT;
        }
    }

    private static Drawable getButtonDrawable(int index) {""",
    "keyboard circular drawable declaration")
key_start = k.index("    private static Drawable getButtonDrawable(int index) {")
key_end = k.index("\n    public void updateColors() {", key_start)
if key_end < key_start:
    raise SystemExit("Custom keyboard color update boundary changed")
# Replace complete shape logic rather than tweaking any of its 4 corner radii.
k = k[:key_start] + """    private static Drawable getButtonDrawable(int index) {
        final int base = Theme.getColor(Theme.key_windowBackgroundWhite);
        final int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        // A subtly tinted blue key at rest, a clearly stronger cyan press.
        // Resolve colors on updateColors() for light/dark/imported themes.
        int rest = android.graphics.Color.rgb(
                (android.graphics.Color.red(base) * 83 + android.graphics.Color.red(accent) * 17) / 100,
                (android.graphics.Color.green(base) * 83 + android.graphics.Color.green(accent) * 17) / 100,
                (android.graphics.Color.blue(base) * 83 + android.graphics.Color.blue(accent) * 17) / 100);
        int active = android.graphics.Color.rgb(
                (android.graphics.Color.red(base) * 54 + android.graphics.Color.red(accent) * 46) / 100,
                (android.graphics.Color.green(base) * 54 + android.graphics.Color.green(accent) * 46) / 100,
                (android.graphics.Color.blue(base) * 54 + android.graphics.Color.blue(accent) * 46) / 100);
        int ink = android.graphics.Color.argb(165,
                android.graphics.Color.red(accent),
                android.graphics.Color.green(accent),
                android.graphics.Color.blue(accent));
        return new android.graphics.drawable.RippleDrawable(
                android.content.res.ColorStateList.valueOf(ink),
                new NabdhCircleKey(rest, active),
                new NabdhCircleKey(android.graphics.Color.WHITE,
                        android.graphics.Color.WHITE));
    }
""" + k[key_end:]
# Expand actual *key cell height*, not only the drawable radius. The stock
# 230dp keyboard uses 10dp outer + 6dp inter-key gaps, capping circles to
# about 47dp. Smaller gutters yield 52dp keys (+11%) at the SAME 230dp height
# without overlapping adjacent touch views or covering the number field.
k = replace_once(k,
    "private final static int SIDE_PADDING = 10, BUTTON_PADDING = 6;",
    "private final static int SIDE_PADDING = 4, BUTTON_PADDING = 3;",
    "expand keypad circles by enlarging available cell height")
# Telegram's original CustomPhoneKeyboardView.onMeasure reads getWidth()
# and getHeight(), i.e. previous layout dimensions, instead of the incoming
# MeasureSpec. During the first frame these can be zero, so the enlarged
# circles are still laid out against stale/small key bounds. Measure actual
# available width/height and then use these values for 3x4 key sizing.
measure = """        int btnWidth = (getWidth() - dp(SIDE_PADDING * 2 + BUTTON_PADDING * 2)) / 3;
        int btnHeight = (getHeight() - dp(SIDE_PADDING * 3 + BUTTON_PADDING * 2)) / 4;"""
# The first occurrence is onLayout (correct), the second is onMeasure.
if k.count(measure) != 2:
    raise SystemExit("CustomPhoneKeyboardView onLayout/onMeasure sizing has changed")
# Replace only the onMeasure occurrence, retaining native onLayout.
original = """        int btnWidth = (getWidth() - dp(SIDE_PADDING * 2 + BUTTON_PADDING * 2)) / 3;
        int btnHeight = (getHeight() - dp(SIDE_PADDING * 3 + BUTTON_PADDING * 2)) / 4;"""
pos = k.index(original)
pos2 = k.index(original, pos + len(original))
k = k[:pos2] + """        // Measure child hit targets from the *new* parent constraints.
        // getHeight() is stale/zero on the first layout pass.
        final int availableWidth = MeasureSpec.getSize(widthMeasureSpec);
        final int availableHeight = MeasureSpec.getSize(heightMeasureSpec);
        int btnWidth = Math.max(1,
                (availableWidth - dp(SIDE_PADDING * 2 + BUTTON_PADDING * 2)) / 3);
        int btnHeight = Math.max(1,
                (availableHeight - dp(SIDE_PADDING * 3 + BUTTON_PADDING * 2)) / 4);""" + k[pos2 + len(original):]
# Constructor and updateColors both tint the same icon; handle both.
backspace_icon = "backButton.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));"
if k.count(backspace_icon) != 2:
    raise SystemExit("Backspace icon anchors changed")
k = k.replace(backspace_icon,
    "backButton.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));")
k = replace_once(k,
    "numberTextPaint.setTextSize(dp(24));",
    "numberTextPaint.setTextSize(dp(22));",
    "numeric key size")
k = replace_once(k,
    "symbolsTextPaint.setTextSize(dp(14));",
    "symbolsTextPaint.setTextSize(dp(10));",
    "key secondary letters")
# Use a clean filled backspace glyph instead of Telegram's outlined
# cyan asset. Keep the existing ImageView, tap handler and key repeat intact.
k = replace_once(k,
    "backButton.setImageResource(R.drawable.msg_clear_input);",
    "backButton.setImageResource(R.drawable.nabdh_keypad_delete);",
    "keypad delete glyph")
# Telegram's stock keypad positions the digit at 25% of the full key cell
# and its letters at 70%. Once the background becomes a centered circle,
# those two labels sit OUTSIDE it. Center both inside the same drawable circle.
# Keep the original NumberButtonView, number/symbol strings and touch handlers.
key_text_before = """            float symbolsWidth = symbolsTextPaint.measureText(mSymbols);
            float numberWidth = numberTextPaint.measureText(mNumber);

            numberTextPaint.getTextBounds(mNumber, 0, mNumber.length(), rect);
            float textOffsetNumber = rect.height() / 2f;
            symbolsTextPaint.getTextBounds(mSymbols, 0, mSymbols.length(), rect);
            float textOffsetSymbols = rect.height() / 2f;

            canvas.drawText(mNumber, getWidth() * 0.25f - numberWidth / 2f, getHeight() / 2f + textOffsetNumber, numberTextPaint);
            canvas.drawText(mSymbols, getWidth() * 0.7f - symbolsWidth / 2f, getHeight() / 2f + textOffsetSymbols, symbolsTextPaint);"""
key_text_after = """            // Both text lines share the exact center of the circular key.
            // Use font metrics rather than character bounds for stable
            // baseline alignment of 1, 0, Arabic locale and Latin labels.
            final float centerX = getWidth() / 2f;
            final float centerY = getHeight() / 2f;
            numberTextPaint.setTextAlign(Paint.Align.CENTER);
            symbolsTextPaint.setTextAlign(Paint.Align.CENTER);
            final boolean hasSymbols = mSymbols != null && !mSymbols.isEmpty();
            final Paint.FontMetrics numberFont = numberTextPaint.getFontMetrics();
            // Use the same radius as the center-aligned circular key drawable,
            // adapting to compact devices and display scales.
            final float keyRadius = Math.max(1f,
                    Math.min(getWidth(), getHeight()) * .5f - dp(1));
            final float numberCenter = centerY - (hasSymbols ? keyRadius * .18f : 0);
            final float numberBaseline = numberCenter
                    - (numberFont.ascent + numberFont.descent) / 2f;
            canvas.drawText(mNumber, centerX, numberBaseline, numberTextPaint);
            if (hasSymbols) {
                final Paint.FontMetrics symbolsFont = symbolsTextPaint.getFontMetrics();
                final float symbolsBaseline = centerY + keyRadius * .48f
                        - (symbolsFont.ascent + symbolsFont.descent) / 2f;
                canvas.drawText(mSymbols, centerX, symbolsBaseline, symbolsTextPaint);
            }"""
k = replace_once(k, key_text_before, key_text_after,
    "center keypad number and letters in the circular surface")
keyboard.write_text(k, encoding="utf-8")
delete_icon = root / "TMessagesProj/src/main/res/drawable/nabdh_keypad_delete.xml"
delete_icon.parent.mkdir(parents=True, exist_ok=True)
delete_icon.write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF"
        android:pathData="M22,3H7c-0.69,0 -1.23,0.35 -1.59,0.88L0,12l5.41,8.11C5.77,20.65 6.31,21 7,21h15c1.1,0 2,-0.9 2,-2V5c0,-1.1 -0.9,-2 -2,-2zM19,16.59L17.59,18 14,14.41 10.41,18 9,16.59 12.59,13 9,9.41 10.41,8 14,11.59 17.59,8 19,9.41 15.41,13z"/>
</vector>
""", encoding="utf-8")

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
