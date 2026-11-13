#!/usr/bin/env bash
# Physical Android smoke check; does not install, clear data, log out, or send messages.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash scripts/device-smoke-check.sh [--serial ADB_SERIAL] [--expect-version VERSION] [--screenshot LOCAL_PNG]

Verifies an ALREADY INSTALLED NabdhGram test build on one authorized Android device.
Checks installed package, launcher intent, Android activity start and app process.
--screenshot is explicitly opt-in: the file may contain private chats and stays local.
No app data, Telegram session, logcat history, installed APK, or settings are changed.
Connect exactly one authorized device, or select one with --serial / ADB_SERIAL.
USAGE
}

package=net.nabdhserv.nabdhgram
serial="${ADB_SERIAL:-}"
expected_version=""
screenshot=""
while (($#)); do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --serial)
      (($# >= 2)) || { echo "Missing --serial value" >&2; exit 2; }
      serial="$2"; shift 2 ;;
    --expect-version)
      (($# >= 2)) || { echo "Missing --expect-version value" >&2; exit 2; }
      expected_version="$2"; shift 2 ;;
    --screenshot)
      (($# >= 2)) || { echo "Missing --screenshot path" >&2; exit 2; }
      screenshot="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

command -v adb >/dev/null || { echo "ERROR: adb is unavailable" >&2; exit 1; }
if [[ -z "$serial" ]]; then
  mapfile -t devices < <(adb devices | awk 'NR > 1 && $2 == "device" { print $1 }')
  if (("${#devices[@]}" != 1)); then
    echo "ERROR: connect exactly one authorized Android device or use --serial." >&2
    exit 1
  fi
  serial="${devices[0]}"
fi
adb_cmd=(adb -s "$serial")
[[ "$("${adb_cmd[@]}" get-state)" == device ]] ||
  { echo "ERROR: chosen device is not authorized and ready" >&2; exit 1; }

paths="$("${adb_cmd[@]}" shell pm path "$package" | tr -d '\r')"
if [[ "$paths" != *"package:"* ]]; then
  echo "ERROR: $package is not installed. This script never installs APKs." >&2
  exit 1
fi
echo "PASS: NabdhGram installed on selected device."

if [[ -n "$expected_version" ]]; then
  # Do not use grep -m1 here: dumpsys may exit with SIGPIPE under
  # set -o pipefail when the first versionName is found too early.
  version="$("${adb_cmd[@]}" shell dumpsys package "$package" |
    awk '/versionName=/ && !found { found=1; value=$0 }
         END { if (found) { sub(/.*versionName=/, "", value);
                            sub(/[[:space:]].*/, "", value); print value } }' | tr -d '\r')"
  [[ "$version" == "$expected_version" ]] ||
    { echo "ERROR: expected version $expected_version, found $version" >&2; exit 1; }
  echo "PASS: package version $version."
fi

resolved="$("${adb_cmd[@]}" shell cmd package resolve-activity --brief \
  -a android.intent.action.MAIN -c android.intent.category.LAUNCHER \
  -p "$package" | tr -d '\r')"
if [[ "$resolved" != *"$package"* ]]; then
  echo "ERROR: the default Android launcher does not resolve to NabdhGram." >&2
  exit 1
fi
echo "PASS: launcher resolves to installed NabdhGram activity."

result="$("${adb_cmd[@]}" shell am start -W -a android.intent.action.MAIN \
  -c android.intent.category.LAUNCHER -p "$package" | tr -d '\r')"
if [[ "$result" != *"Status: ok"* ]] || [[ "$result" == *"Error:"* ]]; then
  echo "ERROR: Android could not start NabdhGram through its public launcher." >&2
  echo "$result" | grep -E '^(Status:|Error:|Exception:)' >&2 || true
  exit 1
fi
echo "PASS: Android launched NabdhGram."

# This is a cold/foreground-launch smoke check, not a crash-free guarantee
# for every feature. Do not stop or restart any Telegram account session.
sleep 2
pid="$("${adb_cmd[@]}" shell pidof "$package" | tr -d '\r' | tr -d '[:space:]')"
if [[ -z "$pid" ]]; then
  echo "ERROR: NabdhGram process did not remain alive after launching." >&2
  exit 1
fi
echo "PASS: app process remained running after launch."

if [[ -n "$screenshot" ]]; then
  umask 077
  echo "WARNING: device screenshot may contain personal content; keep it private." >&2
  "${adb_cmd[@]}" exec-out screencap -p > "$screenshot"
  [[ -s "$screenshot" ]] ||
    { echo "ERROR: screenshot was empty." >&2; exit 1; }
  echo "Saved locally to: $screenshot"
fi
echo "PASS: basic Android device smoke. Manual settings/theme/login QA is STILL REQUIRED."
