#!/usr/bin/env bash
set -euo pipefail
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
mkdir -p "$WORK/classes" "$WORK/dex"
javac --release 8 -cp "$JAR" -d "$WORK/classes" "$SRC/NabdhCardRenderer.java" "$SRC/NabdhCardGeometry.java" "$HERE/tests/android/CardProbe.java"
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
