#!/usr/bin/env bash
# Opt-in ARM64 runtime audit. No root, no chat/export dump, no automatic uploads.
# Usage: bash scripts/profile-nabdh-runtime.sh [output-directory] [samples]
set -euo pipefail
PACKAGE="net.nabdhserv.nabdhgram"
OUT="${1:-./nabdh-runtime-local}"
SAMPLES="${2:-8}"
if ! [[ "$SAMPLES" =~ ^[0-9]+$ ]] || (( SAMPLES < 3 || SAMPLES > 60 )); then
  echo "Samples must be an integer between 3 and 60" >&2; exit 2
fi
command -v adb >/dev/null || { echo "ADB is required; install Android Platform Tools" >&2; exit 2; }
CONNECTED="$(adb devices | awk '$2=="device" {print $1}' | wc -l | tr -d ' ')"
if [[ "$CONNECTED" != 1 ]]; then
  echo "Connect exactly one unlocked, authorized Android device" >&2
  adb devices
  exit 2
fi
ARCH="$(adb shell getprop ro.product.cpu.abilist | tr -d '\r')"
[[ "$ARCH" == *arm64-v8a* ]] || { echo "Physical ARM64 device required" >&2; exit 2; }
adb shell pm path "$PACKAGE" >/dev/null || { echo "NabdhGram is not installed" >&2; exit 2; }
mkdir -p "$OUT"
echo "Device ABI: $ARCH" > "$OUT/summary.txt"
echo "Android SDK: $(adb shell getprop ro.build.version.sdk | tr -d '\r')" >> "$OUT/summary.txt"
echo "Package: $PACKAGE" >> "$OUT/summary.txt"
echo "Do not upload raw ADB diagnostics: they may contain personal information." >> "$OUT/summary.txt"
cat <<'NOTE'
Testing starts without reboot/reset/force-stop, so login/session data are preserved.
For the next sampling window, manually test in this order:
1. Main chats & scrolling; 2. Open/close audio playback repeatedly;
3. NabdhAI model status or a short local prompt; 4. Camera capture/video;
5. Return to home and idle. Raw dumps stay ON THIS COMPUTER.
NOTE
printf 'sample,utc,pss_kb\n' > "$OUT/pss.csv"
for ((i=1; i<=SAMPLES; ++i)); do
  NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  adb shell dumpsys meminfo "$PACKAGE" > "$OUT/meminfo-$i.txt"
  # Android meminfo format changes by API and vendor; do not invent metrics.
  PSS="$(awk '/TOTAL PSS:/ {gsub(/,/, "", $3); print $3; exit}' "$OUT/meminfo-$i.txt")"
  if [[ -z "$PSS" ]]; then
    PSS="$(awk '/^ *TOTAL +[0-9]+/ {print $2;exit}' "$OUT/meminfo-$i.txt")"
  fi
  printf '%s,%s,%s\n' "$i" "$NOW" "${PSS:-NA}" >> "$OUT/pss.csv"
  echo "Sample $i/$SAMPLES: total PSS ${PSS:-unavailable} kB"
  if ((i < SAMPLES)); then sleep 15; fi
done
adb shell dumpsys gfxinfo "$PACKAGE" > "$OUT/gfxinfo.txt" 2>&1 || true
adb shell dumpsys batterystats --charged "$PACKAGE" > "$OUT/batterystats.txt" 2>&1 || true
adb shell dumpsys battery > "$OUT/battery-device.txt" 2>&1 || true
printf '\nRaw results: %s\n' "$OUT"
cat <<'NOTE'
A PSS trend cannot prove a leak or stable lifetime: replay audio and
inspect a Java heap dump/LeakCanary on a DEBUG build to establish retention.
Battery statistics are cumulative since last charge, NOT a controlled
per-feature energy measurement; use a repeatable 30-minute idle/active
comparison and Android Studio Energy Profiler before signing off.
No uploads are performed and no messages/call logs are deliberately read.
NOTE
