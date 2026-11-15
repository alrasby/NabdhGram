package org.telegram.ui;

import android.app.Activity;
import android.app.DownloadManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;

import java.io.ByteArrayInputStream;
import java.net.URI;
import java.util.Locale;

/**
 * Standalone, user-invoked browser. Never intercepts chat contents or
 * Telegram login transport. Tracking filter is deliberately small/local.
 */
public final class NabdhBrowserActivity extends Activity {
    private WebView web;
    private EditText address;
    private boolean blocking = true;
    private boolean scripts = false;
    private static final String[] TRACKERS = {
        "doubleclick.net", "googlesyndication.com", "google-analytics.com",
        "googletagmanager.com", "facebook.net", "connect.facebook.net",
        "analytics.tiktok.com", "bat.bing.com"
    };

    private static boolean tracker(String host) {
        if (host == null) return false;
        String value = host.toLowerCase(Locale.ROOT);
        for (String domain : TRACKERS) {
            if (value.equals(domain) || value.endsWith("." + domain)) return true;
        }
        return false;
    }

    private static Uri safe(Uri uri) {
        if (uri == null || uri.getHost() == null ||
            (!"https".equalsIgnoreCase(uri.getScheme()) &&
             !"http".equalsIgnoreCase(uri.getScheme())) ||
             uri.getUserInfo() != null) return null;
        return uri;
    }

    private Button button(String label, Runnable click) {
        Button result = new Button(this);
        result.setText(label);
        result.setAllCaps(false);
        result.setTextSize(12);
        result.setOnClickListener(v -> click.run());
        return result;
    }

    private void visit(String text) {
        if (text == null) return;
        String candidate = text.trim();
        if (candidate.length() > 2048) {
            Toast.makeText(this, "Address too long", Toast.LENGTH_SHORT).show();
            return;
        }
        if (!candidate.contains("://")) candidate = "https://" + candidate;
        try {
            Uri url = safe(Uri.parse(candidate));
            if (url == null || new URI(candidate).getHost() == null)
                throw new IllegalArgumentException();
            web.loadUrl(url.toString());
        } catch (Exception rejected) {
            Toast.makeText(this, "Only http and https pages can be opened", Toast.LENGTH_LONG).show();
        }
    }

    @Override public void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        setTitle("Nabdh Browser");
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(Color.rgb(18, 29, 33));
        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setOrientation(LinearLayout.HORIZONTAL);
        address = new EditText(this);
        address.setSingleLine(true);
        address.setTextSize(13);
        address.setTextColor(Color.WHITE);
        address.setHintTextColor(Color.LTGRAY);
        address.setHint("https://");
        address.setInputType(android.text.InputType.TYPE_CLASS_TEXT |
                             android.text.InputType.TYPE_TEXT_VARIATION_URI);
        toolbar.addView(address, new LinearLayout.LayoutParams(0, -2, 1f));
        toolbar.addView(button("Go", () -> visit(address.getText().toString())));
        page.addView(toolbar);
        LinearLayout controls = new LinearLayout(this);
        controls.setGravity(Gravity.CENTER_VERTICAL);
        controls.addView(button("‹", () -> { if (web.canGoBack()) web.goBack(); }));
        controls.addView(button("›", () -> { if (web.canGoForward()) web.goForward(); }));
        controls.addView(button("⟳", () -> web.reload()));
        Button protection = button("Shield: ON", () -> {
            blocking = !blocking;
            // The setting is intentionally session-scoped.
        });
        protection.setOnClickListener(v -> {
            blocking = !blocking;
            protection.setText(blocking ? "Shield: ON" : "Shield: OFF");
            web.reload();
        });
        controls.addView(protection, new LinearLayout.LayoutParams(0, -2, 1f));
        Button javascript = button("JS: OFF", () -> {});
        javascript.setOnClickListener(v -> {
            scripts = !scripts;
            web.getSettings().setJavaScriptEnabled(scripts);
            javascript.setText(scripts ? "JS: ON" : "JS: OFF");
            web.reload();
        });
        controls.addView(javascript, new LinearLayout.LayoutParams(0, -2, 1f));
        page.addView(controls);
        web = new WebView(this);
        WebSettings cfg = web.getSettings();
        cfg.setJavaScriptEnabled(false);
        cfg.setDomStorageEnabled(false);
        cfg.setAllowFileAccess(false);
        cfg.setAllowContentAccess(false);
        cfg.setAllowFileAccessFromFileURLs(false);
        cfg.setAllowUniversalAccessFromFileURLs(false);
        cfg.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        cfg.setSupportZoom(true);
        cfg.setBuiltInZoomControls(true);
        cfg.setDisplayZoomControls(false);
        if (Build.VERSION.SDK_INT >= 26) cfg.setSafeBrowsingEnabled(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                if (safe(request.getUrl()) == null) {
                    Toast.makeText(NabdhBrowserActivity.this,
                        "External or unsafe link blocked", Toast.LENGTH_SHORT).show();
                    return true;
                }
                return false;
            }
            @Override public void onPageFinished(WebView view, String url) {
                address.setText(url);
            }
            @Override public WebResourceResponse shouldInterceptRequest(
                    WebView view, WebResourceRequest request) {
                if (blocking && tracker(request.getUrl().getHost()))
                    return new WebResourceResponse("text/plain", "UTF-8",
                            new ByteArrayInputStream(new byte[0]));
                return null;
            }
        });
        web.setDownloadListener((url, agent, disposition, mimeType, length) -> {
            Uri target = safe(Uri.parse(url));
            if (target == null) {
                Toast.makeText(this, "Download blocked", Toast.LENGTH_SHORT).show();
                return;
            }
            try {
                DownloadManager.Request request = new DownloadManager.Request(target);
                request.setMimeType(mimeType);
                request.setNotificationVisibility(
                        DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                request.setDestinationInExternalFilesDir(this, Environment.DIRECTORY_DOWNLOADS,
                        "nabdh-download-" + System.currentTimeMillis());
                DownloadManager manager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                if (manager != null) manager.enqueue(request);
            } catch (Exception failure) {
                Toast.makeText(this, "Download unavailable", Toast.LENGTH_SHORT).show();
            }
        });
        page.addView(web, new LinearLayout.LayoutParams(-1, 0, 1f));
        setContentView(page);
        String initial = getIntent().getStringExtra("url");
        visit(initial == null ? "https://nabdhserv.net" : initial);
    }

    @Override public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }

    @Override protected void onPause() {
        if (web != null) web.onPause();
        super.onPause();
    }

    @Override protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override protected void onDestroy() {
        if (web != null) {
            ViewGroup parent = (ViewGroup) web.getParent();
            if (parent != null) parent.removeView(web);
            web.stopLoading();
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
