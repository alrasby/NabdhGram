#!/usr/bin/env python3
"""Add privacy-minimal connection-state diagnostics to the pinned Telegram source.

Diagnostic-only: does not change reconnect timing, IP strategy, DC endpoints or proxy.
Usage: python3 scripts/apply-network-diagnostics.py TELEGRAM_SOURCE
"""
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-network-diagnostics.py TELEGRAM_SOURCE")
    p = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java"
    source = p.read_text(encoding="utf-8")
    old = """        if (BuildVars.LOGS_ENABLED) {
            FileLog.d("selected ip strategy " + selectedStrategy);
        }
        native_setIpStrategy(currentAccount, selectedStrategy);"""
    new = """        if (BuildVars.LOGS_ENABLED) {
            // NabdhGram N0 diagnostics: account index, connectivity and strategy only.
            // Never log IP addresses, auth keys, phone numbers or message contents.
            FileLog.d("NabdhGram network check accountIndex=" + currentAccount
                    + " state=" + getConnectionState()
                    + " online=" + ApplicationLoader.isNetworkOnline()
                    + " networkType=" + ApplicationLoader.getCurrentNetworkType()
                    + " slow=" + ApplicationLoader.isConnectionSlow()
                    + " ipStrategy=" + selectedStrategy);
        }
        native_setIpStrategy(currentAccount, selectedStrategy);"""
    if source.count(old) != 1:
        raise SystemExit(f"Expected one pinned checkConnection diagnostic anchor; found {source.count(old)}")
    p.write_text(source.replace(old, new, 1), encoding="utf-8")
    print("NabdhGram debug-only network diagnostics installed (no transport changes).")

if __name__ == "__main__":
    main()
