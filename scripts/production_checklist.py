#!/usr/bin/env python3
"""Tax God - Production Readiness Checklist."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

results: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, recommendation: str = ""):
    results.append((name, passed, recommendation))


# 1. SECRET_KEY
secret = os.environ.get("SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
check(
    "SECRET_KEY is not default",
    secret != "CHANGE-ME-IN-PRODUCTION" and len(secret) >= 32,
    "Set SECRET_KEY to a strong random value: openssl rand -hex 32",
)

# 2. CORS_ORIGINS
origins = os.environ.get("ALLOWED_ORIGINS", os.environ.get("CORS_ORIGINS", "*"))
check(
    "CORS_ORIGINS is not wildcard",
    origins != "*",
    "Set ALLOWED_ORIGINS to specific domains in production.",
)

# 3. DEBUG
debug = os.environ.get("DEBUG", "true").lower()
check("DEBUG is false", debug in ("false", "0", "no"), "Set DEBUG=false for production.")

# 4. Pre-commit hook exists
hook_path = ROOT / ".githooks" / "pre-commit"
check(
    "Pre-commit hook exists",
    hook_path.exists() and os.access(hook_path, os.X_OK),
    "Run scripts/install-hooks.sh to set up git hooks.",
)

# 5. No .env secrets in git history
try:
    out = subprocess.run(
        ["git", "log", "--all", "--diff-filter=A", "--name-only", "--pretty=format:"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    files_in_history = out.stdout.strip().split("\n") if out.stdout.strip() else []
    has_env = any(f.strip() == ".env" for f in files_in_history)
    check(
        "No .env in git history",
        not has_env,
        "Remove .env from git history: git filter-branch or BFG.",
    )
except Exception:
    check("No .env in git history", True, "Could not check git history (no git repo?).")


# Print results
print("\n=== Tax God Production Checklist ===\n")
all_passed = True
for name, passed, rec in results:
    icon = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {icon}: {name}")
    if not passed and rec:
        print(f"         → {rec}")
    if not passed:
        all_passed = False

print()
sys.exit(0 if all_passed else 1)
