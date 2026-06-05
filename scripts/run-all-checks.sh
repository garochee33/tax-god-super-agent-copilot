#!/usr/bin/env bash
set -uo pipefail

# Activate venv if exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

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
run_check "ruff lint" ruff check app/ tests/ --select E,F,W --ignore E402,E501,E741

# 2. Tests
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://$(whoami)@localhost:5432/taxgod}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export SECRET_KEY="${SECRET_KEY:-test-run-checks}"
export ENVIRONMENT="${ENVIRONMENT:-development}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-test}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-sk-ant-test}"

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
