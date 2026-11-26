package org.telegram.messenger.nabdhgram;

import java.net.IDN;
import java.net.URI;
import java.util.Locale;

/**
 * NabdhShield v1: local, conservative URL risk signals.
 * This is not a malware verdict and performs no network requests.
 * It deliberately never logs or stores URLs.
 */
public final class NabdhShieldUrlRisk {
    public enum Signal { NONE, INVALID_URL, INSECURE_HTTP, IP_LITERAL, USERINFO, PUNYCODE_HOST }

    private NabdhShieldUrlRisk() {}

    public static Signal inspect(String input) {
        if (input == null || input.length() > 8192) return Signal.INVALID_URL;
        final String value = input.trim();
        if (value.isEmpty()) return Signal.INVALID_URL;
        try {
            URI uri = new URI(value);
            String scheme = uri.getScheme();
            if (scheme == null) return Signal.INVALID_URL;
            scheme = scheme.toLowerCase(Locale.ROOT);
            if (!"http".equals(scheme) && !"https".equals(scheme)) return Signal.INVALID_URL;
            String host = uri.getHost();
            if (host == null || host.isEmpty()) return Signal.INVALID_URL;
            if (uri.getRawUserInfo() != null) return Signal.USERINFO;
            if ("http".equals(scheme)) return Signal.INSECURE_HTTP;
            String ascii = IDN.toASCII(host, IDN.USE_STD3_ASCII_RULES).toLowerCase(Locale.ROOT);
            if (ascii.startsWith("xn--") || ascii.contains(".xn--")) return Signal.PUNYCODE_HOST;
            if (host.startsWith("[") || host.indexOf(':') >= 0 || host.matches("[0-9.]+")) return Signal.IP_LITERAL;
            return Signal.NONE;
        } catch (Exception ignored) {
            return Signal.INVALID_URL;
        }
    }
}
