#!/usr/bin/env python3
"""Add opt-in debug connection diagnostics; do not change transport behavior."""
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply-network-diagnostics.py TELEGRAM_SOURCE")
    p = Path(sys.argv[1]).resolve() / "TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java"
    source = p.read_text(encoding="utf-8")
    old = '''        if (BuildVars.LOGS_ENABLED) {
            FileLog.d("selected ip strategy " + selectedStrategy);
        }
        native_setIpStrategy(currentAccount, selectedStrategy);'''
    new = '''        if (BuildVars.LOGS_ENABLED) {
            // NabdhGram debug-only: no hostnames, IP addresses, credentials or message data.
            FileLog.d("NabdhGram network state=" + getConnectionState()
                    + " online=" + ApplicationLoader.isNetworkOnline()
                    + " type=" + ApplicationLoader.getCurrentNetworkType()
                    + " slow=" + ApplicationLoader.isConnectionSlow()
                    + " ipStrategy=" + selectedStrategy);
        }
        native_setIpStrategy(currentAccount, selectedStrategy);'''
    if source.count(old) != 1:
        raise SystemExit("Pinned Telegram checkConnection anchor mismatch")
    p.write_text(source.replace(old, new, 1), encoding="utf-8")
    print("Debug-only connection diagnostics installed; reconnect policy unchanged.")

if __name__ == "__main__":
    main()
