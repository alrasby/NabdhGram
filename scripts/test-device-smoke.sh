#!/usr/bin/env bash
# No real device or credentials: exercise launch success and failure paths
# with an isolated fake ADB CLI, including a non-destructive command audit.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/adb" <<'FAKE_ADB'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$MOCK_ADB_CALLS"
if [[ "${1:-}" == devices ]]; then
  printf 'List of devices attached\nFAKE123\tdevice\n'
  exit 0
fi
if [[ "${1:-}" == -s ]]; then
  [[ "$2" == FAKE123 ]] || exit 2
  shift 2
fi
case "${1:-}/${2:-}/${3:-}" in
  get-state//) echo device ;;
  shell/pm/path) echo 'package:/data/app/example/base.apk' ;;
  shell/dumpsys/package) printf 'Packages:\n  versionName=%s\n  other=data\n' "${MOCK_VERSION:-13.2.2}" ;;
  shell/cmd/package)
    if [[ "${MOCK_RESOLVE_FAIL:-0}" == 1 ]]; then
      echo 'No activity found'
    else
      echo 'net.nabdhserv.nabdhgram/org.telegram.messenger.DefaultIcon'
    fi ;;
  shell/am/start)
    if [[ "${MOCK_START_FAIL:-0}" == 1 ]]; then
      echo 'Error: Activity not started'
    else
      echo 'Status: ok'
    fi ;;
  shell/pidof/net.nabdhserv.nabdhgram) echo '12345' ;;
  *) echo "Unexpected adb command: $*" >&2; exit 4 ;;
esac
FAKE_ADB
chmod +x "$tmp/adb"
export PATH="$tmp:$PATH" MOCK_ADB_CALLS="$tmp/adb-calls"
bash "$repo_root/scripts/device-smoke-check.sh" --expect-version 13.2.2 >"$tmp/success"
grep -q 'PASS: basic Android device smoke' "$tmp/success"
! grep -Eiq 'uninstall|install |force-stop|pm clear|logcat|screencap' "$tmp/adb-calls"

export MOCK_VERSION=0.0.0
if bash "$repo_root/scripts/device-smoke-check.sh" --expect-version 13.2.2 >"$tmp/failure" 2>&1; then
  echo "FAIL: wrong package version incorrectly accepted" >&2
  exit 1
fi
unset MOCK_VERSION
export MOCK_RESOLVE_FAIL=1
if bash "$repo_root/scripts/device-smoke-check.sh" --expect-version 13.2.2 >"$tmp/failure" 2>&1; then
  echo "FAIL: missing launcher incorrectly accepted" >&2
  exit 1
fi
unset MOCK_RESOLVE_FAIL
export MOCK_START_FAIL=1
if bash "$repo_root/scripts/device-smoke-check.sh" --expect-version 13.2.2 >"$tmp/failure" 2>&1; then
  echo "FAIL: failed Activity start incorrectly accepted" >&2
  exit 1
fi
echo 'PASS: device smoke tests: positive start, wrong version, launcher missing, start failure.'
