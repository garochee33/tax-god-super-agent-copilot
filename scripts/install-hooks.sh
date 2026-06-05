#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.githooks"

if [[ ! -d "$HOOKS_DIR" ]]; then
  echo "❌ .githooks/ directory not found at $HOOKS_DIR"
  exit 1
fi

git config core.hooksPath .githooks
chmod +x "$HOOKS_DIR"/*

echo "✅ Git hooks installed:"
echo "   hooksPath = .githooks"
ls -1 "$HOOKS_DIR" | sed 's/^/   • /'
