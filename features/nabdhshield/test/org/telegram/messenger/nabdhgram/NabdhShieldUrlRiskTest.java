package org.telegram.messenger.nabdhgram;

import org.junit.Test;
import static org.junit.Assert.assertEquals;

public class NabdhShieldUrlRiskTest {
    @Test public void ordinaryHttpsIsNotFlagged() {
        assertEquals(NabdhShieldUrlRisk.Signal.NONE, NabdhShieldUrlRisk.inspect("https://example.org/a"));
    }
    @Test public void insecureHttpIsFlagged() {
        assertEquals(NabdhShieldUrlRisk.Signal.INSECURE_HTTP, NabdhShieldUrlRisk.inspect("http://example.org"));
    }
    @Test public void credentialLikeUrlIsFlagged() {
        assertEquals(NabdhShieldUrlRisk.Signal.USERINFO, NabdhShieldUrlRisk.inspect("https://user@host.example/path"));
    }
    @Test public void punycodeIsFlagged() {
        assertEquals(NabdhShieldUrlRisk.Signal.PUNYCODE_HOST, NabdhShieldUrlRisk.inspect("https://xn--e1afmkfd.xn--p1ai"));
    }
    @Test public void invalidSchemeIsRejected() {
        assertEquals(NabdhShieldUrlRisk.Signal.INVALID_URL, NabdhShieldUrlRisk.inspect("javascript:alert(1)"));
    }
    @Test public void ipAddressIsFlagged() {
        assertEquals(NabdhShieldUrlRisk.Signal.IP_LITERAL, NabdhShieldUrlRisk.inspect("https://192.0.2.1/a"));
    }
}
