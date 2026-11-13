#!/usr/bin/env python3
"""Add REAL QR-login to the pinned native Telegram LoginActivity.

No extra login provider, camera permission, password bypass or email enumeration.
Existing phone/email-code, 2FA, proxy and screen navigation remain native.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: apply-nabdh-qr-login.py TELEGRAM_SOURCE")

root = Path(sys.argv[1])
login = root / "TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java"
res = root / "TMessagesProj/src/main/res"
s = login.read_text(encoding="utf-8")

def once(old, new, label):
    global s
    if s.count(old) != 1:
        raise SystemExit(f"{label}: expected one pinned source anchor, found {s.count(old)}")
    s = s.replace(old, new, 1)

fields = """
    // QR login has its own short-lived server token, not the phone/email code.
    // No token is persisted, uploaded to analytics, copied, or logged.
    private AlertDialog nabdhQrDialog;
    private android.widget.ImageView nabdhQrCodeView;
    private android.widget.TextView nabdhQrStatusView;
    private int nabdhQrRequestId = -1;
    private int nabdhQrGeneration;
    private boolean nabdhQrWaiting;
    private Runnable nabdhQrRefresh;

    private boolean nabdhQrActive(int generation) {
        return generation == nabdhQrGeneration && nabdhQrDialog != null
                && nabdhQrDialog.isShowing() && getParentActivity() != null;
    }

    private void nabdhStopQrLogin() {
        nabdhQrGeneration++;
        if (nabdhQrRefresh != null) {
            AndroidUtilities.cancelRunOnUIThread(nabdhQrRefresh);
            nabdhQrRefresh = null;
        }
        if (nabdhQrRequestId >= 0) {
            getConnectionsManager().cancelRequest(nabdhQrRequestId, true);
            nabdhQrRequestId = -1;
        }
        nabdhQrWaiting = false;
        nabdhQrCodeView = null;
        nabdhQrStatusView = null;
        nabdhQrDialog = null;
    }

    private void nabdhShowQrLogin() {
        if (getParentActivity() == null || activityMode != MODE_LOGIN
                || currentViewNum != VIEW_PHONE_INPUT) return;
        if (nabdhQrDialog != null && nabdhQrDialog.isShowing()) return;

        final android.content.Context context = getParentActivity();
        android.widget.LinearLayout panel = new android.widget.LinearLayout(context);
        panel.setOrientation(android.widget.LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER_HORIZONTAL);
        panel.setPadding(dp(24), dp(12), dp(24), dp(20));

        nabdhQrCodeView = new android.widget.ImageView(context);
        nabdhQrCodeView.setAdjustViewBounds(true);
        nabdhQrCodeView.setScaleType(android.widget.ImageView.ScaleType.FIT_CENTER);
        nabdhQrCodeView.setContentDescription(context.getString(R.string.NabdhQrLoginTitle));
        panel.addView(nabdhQrCodeView, new android.widget.LinearLayout.LayoutParams(dp(248), dp(248)));

        nabdhQrStatusView = new android.widget.TextView(context);
        nabdhQrStatusView.setTextSize(android.util.TypedValue.COMPLEX_UNIT_DIP, 14);
        nabdhQrStatusView.setGravity(Gravity.CENTER);
        nabdhQrStatusView.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
        nabdhQrStatusView.setText(R.string.NabdhQrLoginInstructions);
        android.widget.LinearLayout.LayoutParams statusParams =
                new android.widget.LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        statusParams.topMargin = dp(14);
        panel.addView(nabdhQrStatusView, statusParams);

        android.widget.TextView retry = new android.widget.TextView(context);
        retry.setText(R.string.NabdhQrLoginRetry);
        retry.setGravity(Gravity.CENTER);
        retry.setTextSize(android.util.TypedValue.COMPLEX_UNIT_DIP, 14);
        retry.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        retry.setBackground(org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
        android.widget.LinearLayout.LayoutParams retryParams =
                new android.widget.LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, dp(48));
        retryParams.topMargin = dp(12);
        panel.addView(retry, retryParams);
        retry.setOnClickListener(view -> nabdhRequestQrToken());

        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle(context.getString(R.string.NabdhQrLoginTitle));
        builder.setView(panel);
        builder.setNegativeButton(context.getString(R.string.Cancel), null);
        final AlertDialog dialog = builder.create();
        nabdhQrDialog = dialog;
        dialog.setOnDismissListener(ignored -> {
            if (nabdhQrDialog == dialog) nabdhStopQrLogin();
        });
        showDialog(dialog);
        if (dialog.isShowing()) nabdhRequestQrToken();
    }

    private void nabdhRequestQrToken() {
        if (nabdhQrDialog == null || !nabdhQrDialog.isShowing()
                || nabdhQrWaiting || getParentActivity() == null) return;
        if (nabdhQrRefresh != null) {
            AndroidUtilities.cancelRunOnUIThread(nabdhQrRefresh);
            nabdhQrRefresh = null;
        }
        nabdhQrWaiting = true;
        final int generation = ++nabdhQrGeneration;
        nabdhQrStatusView.setText(R.string.NabdhQrLoginLoading);

        TLRPC.TL_auth_exportLoginToken request = new TLRPC.TL_auth_exportLoginToken();
        request.api_id = BuildVars.APP_ID;
        request.api_hash = BuildVars.APP_HASH;
        for (int account = 0; account < UserConfig.MAX_ACCOUNT_COUNT; account++) {
            UserConfig config = UserConfig.getInstance(account);
            if (config.isClientActivated()) {
                request.except_ids.add(config.getClientUserId());
            }
        }
        final int flags = ConnectionsManager.RequestFlagWithoutLogin
                | ConnectionsManager.RequestFlagEnableUnauthorized
                | ConnectionsManager.RequestFlagTryDifferentDc
                | ConnectionsManager.RequestFlagFailOnServerErrors;
        nabdhQrRequestId = getConnectionsManager().sendRequest(request,
                (response, error) -> AndroidUtilities.runOnUIThread(() -> {
                    if (!nabdhQrActive(generation)) return;
                    nabdhQrRequestId = -1;
                    nabdhQrWaiting = false;
                    nabdhProcessQrToken(response, error, generation, flags);
                }), flags);
    }

    private void nabdhProcessQrToken(TLObject response, TLRPC.TL_error error,
                                    int generation, int flags) {
        if (!nabdhQrActive(generation)) return;
        if (response instanceof TLRPC.TL_auth_loginToken) {
            TLRPC.TL_auth_loginToken token = (TLRPC.TL_auth_loginToken) response;
            final String url = "tg://login?token=" + Base64.encodeToString(token.token,
                    Base64.URL_SAFE | Base64.NO_WRAP | Base64.NO_PADDING);
            try {
                java.util.HashMap<com.google.zxing.EncodeHintType, Object> hints =
                        new java.util.HashMap<>();
                hints.put(com.google.zxing.EncodeHintType.ERROR_CORRECTION,
                        com.google.zxing.qrcode.decoder.ErrorCorrectionLevel.M);
                hints.put(com.google.zxing.EncodeHintType.MARGIN, 1);
                org.telegram.messenger.TelegramQRCodeWriter writer =
                        new org.telegram.messenger.TelegramQRCodeWriter();
                android.graphics.Bitmap bitmap = writer.encode(url, 512, 512, hints, null);
                if (bitmap == null) throw new IllegalStateException("QR rendering failed");
                nabdhQrCodeView.setImageBitmap(bitmap);
                nabdhQrStatusView.setText(R.string.NabdhQrLoginInstructions);
            } catch (Exception exception) {
                nabdhQrStatusView.setText(R.string.NabdhQrLoginError);
                nabdhQrCodeView.setImageDrawable(null);
                return;
            }
            // The token expires server-side (usually in 30 seconds).
            // One scheduled renewal per token, only while the dialog is open:
            // no background polling or unexpected account traffic.
            long refreshAfterMs = ((long) token.expires) * 1000L
                    - System.currentTimeMillis() + 1000L;
            refreshAfterMs = Math.max(2000L, Math.min(refreshAfterMs, 35000L));
            nabdhQrRefresh = () -> {
                nabdhQrRefresh = null;
                if (nabdhQrActive(generation)) nabdhRequestQrToken();
            };
            AndroidUtilities.runOnUIThread(nabdhQrRefresh, refreshAfterMs);
        } else if (response instanceof TLRPC.TL_auth_loginTokenMigrateTo) {
            TLRPC.TL_auth_loginTokenMigrateTo migration =
                    (TLRPC.TL_auth_loginTokenMigrateTo) response;
            getConnectionsManager().setDefaultDatacenterId(migration.dc_id);
            nabdhQrWaiting = true;
            TLRPC.TL_auth_importLoginToken importRequest = new TLRPC.TL_auth_importLoginToken();
            importRequest.token = migration.token;
            nabdhQrRequestId = getConnectionsManager().sendRequest(importRequest,
                    (result, importError) -> AndroidUtilities.runOnUIThread(() -> {
                        if (!nabdhQrActive(generation)) return;
                        nabdhQrRequestId = -1;
                        nabdhQrWaiting = false;
                        nabdhProcessQrToken(result, importError, generation, flags);
                    }), flags);
        } else if (response instanceof TLRPC.TL_auth_loginTokenSuccess) {
            TLRPC.auth_Authorization auth =
                    ((TLRPC.TL_auth_loginTokenSuccess) response).authorization;
            AlertDialog current = nabdhQrDialog;
            if (current != null) current.dismiss();
            if (auth instanceof TLRPC.TL_auth_authorization) {
                onAuthSuccess((TLRPC.TL_auth_authorization) auth);
            } else if (auth instanceof TLRPC.TL_auth_authorizationSignUpRequired) {
                TLRPC.TL_auth_authorizationSignUpRequired signup =
                        (TLRPC.TL_auth_authorizationSignUpRequired) auth;
                if (signup.terms_of_service != null) currentTermsOfService = signup.terms_of_service;
                setPage(VIEW_REGISTER, true, new Bundle(), false);
            }
        } else if (error != null && "SESSION_PASSWORD_NEEDED".equals(error.text)) {
            nabdhQrStartPassword();
        } else {
            // Keep a manual retry button; do not spin indefinitely on errors.
            nabdhQrCodeView.setImageDrawable(null);
            nabdhQrStatusView.setText(R.string.NabdhQrLoginError);
        }
    }

    private void nabdhQrStartPassword() {
        if (nabdhQrDialog == null || !nabdhQrDialog.isShowing()) return;
        final AlertDialog current = nabdhQrDialog;
        current.dismiss();
        TL_account.getPassword passwordRequest = new TL_account.getPassword();
        getConnectionsManager().sendRequest(passwordRequest,
                (response, error) -> AndroidUtilities.runOnUIThread(() -> {
                    if (getParentActivity() == null) return;
                    if (error == null && response instanceof TL_account.Password) {
                        TL_account.Password password = (TL_account.Password) response;
                        if (!TwoStepVerificationActivity.canHandleCurrentPassword(password, true)) {
                            AlertsCreator.showUpdateAppAlert(getParentActivity(),
                                    getString(R.string.UpdateAppAlert), true);
                            return;
                        }
                        Bundle bundle = new Bundle();
                        SerializedData data = new SerializedData(password.getObjectSize());
                        password.serializeToStream(data);
                        bundle.putString("password", Utilities.bytesToHex(data.toByteArray()));
                        setPage(VIEW_PASSWORD, true, bundle, false);
                    } else {
                        needShowAlert(getString(R.string.AppName),
                                getString(R.string.NabdhQrLoginError));
                    }
                }), ConnectionsManager.RequestFlagWithoutLogin);
    }

"""
once("    private View cachedFragmentView;\n", fields + "    private View cachedFragmentView;\n", "QR controller location")
once(
    "            addView(phoneOutlineView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 58, 16, 8, 16, 8));",
    """            addView(phoneOutlineView, LayoutHelper.createLinear(LayoutHelper.MATCH_PARENT, 58, 16, 8, 16, 8));
            if (activityMode == MODE_LOGIN) {
                TextView nabdhQrButton = new TextView(context);
                nabdhQrButton.setText(R.string.NabdhQrLoginButton);
                nabdhQrButton.setGravity(Gravity.CENTER);
                nabdhQrButton.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 15);
                nabdhQrButton.setTypeface(AndroidUtilities.bold());
                nabdhQrButton.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
                // Change horizontal size only: keep its 52dp touch height.
                nabdhQrButton.setMinWidth(dp(220));
                nabdhQrButton.setPadding(dp(24), 0, dp(24), 0);
                nabdhQrButton.setBackground(
                        org.telegram.ui.Components.NabdhGlassRowDecoration.newCardBackground());
                nabdhQrButton.setContentDescription(context.getString(R.string.NabdhQrLoginButton));
                nabdhQrButton.setOnClickListener(view -> nabdhShowQrLogin());
                addView(nabdhQrButton, LayoutHelper.createLinear(
                        LayoutHelper.WRAP_CONTENT, 52, Gravity.CENTER_HORIZONTAL, 28, 14, 28, 8));
            }""",
    "phone form QR button")
once("    public void onFragmentDestroy() {\n        super.onFragmentDestroy();",
     """    public void onFragmentDestroy() {
        // Stop server-token refresh and cancel in-flight work before teardown.
        if (nabdhQrDialog != null) nabdhQrDialog.dismiss();
        nabdhStopQrLogin();
        super.onFragmentDestroy();""", "QR teardown")
login.write_text(s, encoding="utf-8")

strings = (
    ("NabdhQrLoginTitle", "Log in via QR", "تسجيل الدخول عبر QR"),
    ("NabdhQrLoginButton", "Log in with QR code", "تسجيل الدخول عبر رمز QR"),
    ("NabdhQrLoginInstructions", "Open Telegram on another device, then Settings > Devices > Link Desktop Device. Scan and approve this code.", "افتح Telegram على جهاز آخر، ثم الإعدادات ← الأجهزة ← ربط جهاز. امسح الرمز ووافق على تسجيل الدخول."),
    ("NabdhQrLoginRetry", "Refresh QR code", "تحديث رمز QR"),
    ("NabdhQrLoginLoading", "Requesting a secure code…", "جارٍ الحصول على رمز آمن…"),
    ("NabdhQrLoginError", "QR login is currently unavailable. Check your connection and tap Refresh.", "تعذر تسجيل الدخول عبر QR حاليًا. تحقق من الاتصال واضغط تحديث."),
)
for folder, index in (("values", 1), ("values-ar", 2)):
    target = res / folder / "nabdh_qr_login.xml"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<resources>']
    for name, en, ar in strings:
        value = en if index == 1 else ar
        lines.append('    <string name="' + name + '">' + value.replace('&', '&amp;').replace('>', '&gt;') + '</string>')
    lines.append('</resources>')
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("PASS: native QR login button, token export/migrate/success, timed expiry and 2FA fallback")
