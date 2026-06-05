#!/usr/bin/env bash
set -uo pipefail

echo "═══════════════════════════════════════"
echo "  Tax God — Pre-Deploy Checks"
echo "═══════════════════════════════════════"
echo ""

PASS=0
FAIL=0

run_check() {
  local name="$1"
  shift
  echo -n "  [$name] ... "
  if "$@" >/dev/null 2>&1; then
    echo "✅ PASS"
    ((PASS++))
  else
    echo "❌ FAIL"
    ((FAIL++))
  fi
}

# 1. Lint
run_check "ruff lint" ruff check app/ tests/

# 2. Tests
run_check "pytest" pytest tests/ -q --tb=no

# 3. Git status clean
echo -n "  [git clean] ... "
if [ -z "$(git status --porcelain)" ]; then
  echo "✅ PASS"
  ((PASS++))
else
  echo "⚠️  DIRTY ($(git status --porcelain | wc -l | tr -d ' ') files)"
  ((FAIL++))
fi

# 4. Integrity
echo -n "  [integrity] ... "
if [ -s .dev/integrity.json ] && [ "$(cat .dev/integrity.json)" != "{}" ]; then
  echo "✅ PASS (snapshot exists)"
  ((PASS++))
else
  echo "⚠️  SKIP (no snapshot)"
  ((PASS++))
fi

echo ""
echo "═══════════════════════════════════════"
if [ "$FAIL" -eq 0 ]; then
  echo "  Result: ✅ GO ($PASS/$((PASS+FAIL)) passed)"
  exit 0
else
  echo "  Result: ❌ NO-GO ($FAIL failed, $PASS passed)"
  exit 1
fi
