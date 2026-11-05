#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-Telegram-upstream}"
if [[ ! -d "$ROOT/.git" ]]; then
  echo "Missing cloned upstream repository: $ROOT" >&2
  exit 1
fi
for path in README.md settings.gradle gradle/wrapper/gradle-wrapper.properties TMessagesProj/build.gradle TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java; do
  if [[ ! -f "$ROOT/$path" ]]; then
    echo "Missing expected upstream file: $path" >&2
    exit 1
  fi
done
if grep -q 'gradle-8.13-bin.zip' "$ROOT/gradle/wrapper/gradle-wrapper.properties"; then
  echo "Gradle wrapper distribution: 8.13"
else
  echo "Gradle wrapper differs from audited 8.13; review before building" >&2
fi
echo "Commit: $(git -C "$ROOT" rev-parse HEAD)"
echo "Submodule status:"
git -C "$ROOT" submodule status --recursive
echo "Baseline source checks passed (this does not compile an APK)."
