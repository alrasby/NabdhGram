#!/usr/bin/env bash
set -euo pipefail
TARGET_APK="${2:-}"
ROOT="$(cd "$1" && pwd)"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$PWD/card-android-evidence"
mkdir -p "$OUT"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SDK="$ANDROID_HOME"
BT="$SDK/build-tools/36.0.0"
JAR="$SDK/platforms/android-36/android.jar"
PKG=net.nabdhserv.cardtest
SRC="$ROOT/TMessagesProj/src/main/java/org/telegram/ui/Components"
python3 "$HERE/scripts/test-nabdh-card-geometry.py" | tee "$OUT/geometry.log"
cat > "$WORK/AndroidManifest.xml" <<'XML'
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="net.nabdhserv.cardtest">
  <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="35"/>
  <application android:label="Card regression fixture" android:debuggable="true"/>
  <instrumentation android:name=".CardProbe" android:targetPackage="net.nabdhserv.cardtest"/>
</manifest>
XML
if [[ -n "$TARGET_APK" ]]; then
  sed -i '/<\/manifest>/i\  <instrumentation android:name=".DialogCellProbe" android:targetPackage="net.nabdhserv.nabdhgram"/>' "$WORK/AndroidManifest.xml"
fi
mkdir -p "$WORK/classes" "$WORK/dex"
javac --release 8 -cp "$JAR" -d "$WORK/classes" "$SRC/NabdhCardRenderer.java" "$SRC/NabdhCardGeometry.java" "$HERE/tests/android/CardProbe.java" "$HERE/tests/android/DialogCellProbe.java"
(cd "$WORK/classes" && jar cf "$WORK/classes.jar" .)
"$BT/d8" --min-api 26 --lib "$JAR" --output "$WORK/dex" "$WORK/classes.jar"
"$BT/aapt" package -f -M "$WORK/AndroidManifest.xml" -I "$JAR" -F "$WORK/unsigned.apk"
(cd "$WORK/dex" && "$BT/aapt" add "$WORK/unsigned.apk" classes.dex)
"$BT/zipalign" -f 4 "$WORK/unsigned.apk" "$WORK/aligned.apk"
keytool -genkeypair -keystore "$WORK/test.jks" -storepass android -keypass android -alias test -dname CN=CardTest -keyalg RSA -validity 365 -noprompt >/dev/null 2>&1
"$BT/apksigner" sign --ks "$WORK/test.jks" --ks-pass pass:android --key-pass pass:android --out "$WORK/test.apk" "$WORK/aligned.apk"
adb install -r "$WORK/test.apk"
set +e
timeout 180 adb shell am instrument -w -r "$PKG/.CardProbe" | tee "$OUT/android.log"
status=$?
set -e
for f in rest right left dark; do
  adb exec-out run-as "$PKG" cat "files/$f.png" > "$OUT/$f.png" || true
done
test "$status" -eq 0
grep -Fq 'CARD_GATE_PASS' "$OUT/android.log"
! grep -Eq 'CARD_GATE_FAIL|INSTRUMENTATION_FAILED|INSTRUMENTATION_ABORTED' "$OUT/android.log"
for f in rest right left dark; do test -s "$OUT/$f.png"; done

if [[ -n "$TARGET_APK" ]]; then
  "$BT/apksigner" sign --ks "$WORK/test.jks" --ks-pass pass:android --key-pass pass:android \
    --out "$WORK/dialog-target.apk" "$TARGET_APK"
  adb install "$WORK/dialog-target.apk" | tee "$OUT/dialog-install.log"
  set +e
  timeout 180 adb shell am instrument -w -r "$PKG/.DialogCellProbe" | tee "$OUT/dialog-android.log"
  status=$?
  set -e
  for f in dialog-rest dialog-right dialog-left dialog-rest-after; do
    adb exec-out run-as net.nabdhserv.nabdhgram cat "files/$f.png" > "$OUT/$f.png" || true
  done
  test "$status" -eq 0
  grep -Fq 'DIALOG_CELL_PASS' "$OUT/dialog-android.log"
  ! grep -Eq 'DIALOG_CELL_FAIL|INSTRUMENTATION_FAILED|INSTRUMENTATION_ABORTED' "$OUT/dialog-android.log"
  for f in dialog-rest dialog-right dialog-left dialog-rest-after; do test -s "$OUT/$f.png"; done
  python3 - "$OUT" <<'PIXELS' | tee "$OUT/dialog-pixel-comparison.log"
from pathlib import Path
from PIL import Image, ImageChops
import sys

evidence = Path(sys.argv[1])
with Image.open(evidence / "dialog-rest.png") as before, Image.open(evidence / "dialog-rest-after.png") as after:
    before_mask = before.convert("RGBA").getchannel("A")
    after_mask = after.convert("RGBA").getchannel("A")
    if before_mask.size != after_mask.size or ImageChops.difference(before_mask, after_mask).getbbox():
        raise SystemExit("DialogCell resting silhouette changed after repeated draws")
    print("Resting silhouette: pixel-identical alpha before and after 500 draw cycles")
PIXELS
fi
