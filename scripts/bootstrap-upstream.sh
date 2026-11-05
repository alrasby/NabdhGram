#!/usr/bin/env bash
set -euo pipefail

# Run in a clean working directory. Never run over an existing source tree.
UPSTREAM_URL="https://github.com/DrKLO/Telegram.git"
TARGET="${1:-Telegram-upstream}"
if [[ -e "$TARGET" ]]; then
  echo "Target already exists: $TARGET" >&2
  exit 1
fi

git clone --recursive --shallow-submodules "$UPSTREAM_URL" "$TARGET"
cd "$TARGET"
git submodule update --init --recursive --depth=1
echo "Upstream commit: $(git rev-parse HEAD)"
git submodule status --recursive
echo "Source fetched. This is NOT yet a branded or configured NabdhGram build."
