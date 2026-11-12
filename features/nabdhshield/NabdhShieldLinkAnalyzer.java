package org.telegram.messenger;

import java.net.IDN;
import java.net.URI;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * NabdhShield local-first URL risk signals. No network access or user data collection.
 * A warning is not a malware verdict; absence of a warning is not a safety guarantee.
 */
public final class NabdhShieldLinkAnalyzer {
    private NabdhShieldLinkAnalyzer() {}

    public static List<String> analyze(String raw) {
        if (raw == null || raw.trim().isEmpty()) {
            return Collections.singletonList("invalid_url");
        }
        ArrayList<String> signals = new ArrayList<>();
        try {
            URI uri = new URI(raw.trim());
            String scheme = uri.getScheme();
            if (scheme == null || (!scheme.equalsIgnoreCase("https") && !scheme.equalsIgnoreCase("http"))) {
                signals.add("non_web_scheme");
                return signals;
            }
            if (uri.getRawUserInfo() != null) signals.add("embedded_credentials");
            String host = uri.getHost();
            if (host == null || host.isEmpty()) {
                signals.add("invalid_host");
                return signals;
            }
            String ascii = IDN.toASCII(host, IDN.USE_STD3_ASCII_RULES).toLowerCase(Locale.ROOT);
            if (ascii.startsWith("xn--") || ascii.contains(".xn--")) signals.add("internationalized_domain");
            if (ascii.matches("(?:[0-9]{1,3}\\.){3}[0-9]{1,3}")) signals.add("numeric_host");
            if (scheme.equalsIgnoreCase("http")) signals.add("unencrypted_http");
            String path = uri.getPath();
            if (path != null && path.toLowerCase(Locale.ROOT).matches(".*\\.(apk|exe|scr|bat|cmd|msi|ps1|jar)$")) {
                signals.add("executable_download");
            }
        } catch (Exception e) {
            signals.add("invalid_url");
        }
        return Collections.unmodifiableList(signals);
    }
}
