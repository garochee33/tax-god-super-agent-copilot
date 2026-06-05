#!/usr/bin/env bash
set -euo pipefail

REPORT="BUILD_STATUS.md"
GITHUB_USER="garochee33"

declare -A REPOS=(
  ["tax-god-super-agent-copilot"]="/tmp/tax-audit/tax-god-copilot"
  ["DSH"]="$HOME/DSH"
  ["DOME-HUB"]=""
  ["trinity-unified-ai"]=""
  ["dome-brain"]=""
  ["dome-console"]=""
  ["sacred-geometry-agents"]=""
  ["resonance-coordination-layer"]=""
)

cat > "$REPORT" <<EOF
# Build Status Report
Generated: $(date -Iseconds)

| Repo | Branch | Last Commit | Behind/Ahead | Uncommitted | Health |
|------|--------|-------------|--------------|-------------|--------|
EOF

for repo in "${!REPOS[@]}"; do
  local_path="${REPOS[$repo]}"
  github_url="https://github.com/${GITHUB_USER}/${repo}.git"

  if [[ -z "$local_path" || ! -d "$local_path/.git" ]]; then
    echo "⏭  $repo — no local clone (remote: $github_url)"
    echo "| $repo | — | — | no local clone | — | — |" >> "$REPORT"
    continue
  fi

  echo "🔄 $repo ($local_path)"
  cd "$local_path"

  git fetch origin 2>/dev/null || { echo "  ⚠️  fetch failed"; continue; }

  branch=$(git rev-parse --abbrev-ref HEAD)
  last_commit=$(git log -1 --format="%ci" 2>/dev/null || echo "unknown")
  
  ahead=$(git rev-list --count "origin/$branch..HEAD" 2>/dev/null || echo "?")
  behind=$(git rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo "?")
  
  uncommitted=$(git status --porcelain | wc -l | tr -d ' ')
  [[ "$uncommitted" == "0" ]] && uncommitted="clean" || uncommitted="${uncommitted} files"

  echo "  branch=$branch ahead=$ahead behind=$behind uncommitted=$uncommitted"

  health="—"
  if [[ -f "pytest.ini" || -f "pyproject.toml" || -f "setup.cfg" ]]; then
    if command -v pytest &>/dev/null && pytest --co -q &>/dev/null 2>&1; then
      health="pytest available"
    fi
  fi
  if [[ -f "scripts/check.sh" ]]; then
    health="check.sh present"
  fi

  echo "| $repo | $branch | $last_commit | ↓${behind} ↑${ahead} | $uncommitted | $health |" >> "$REPORT"
done

echo ""
echo "✅ Report written to $REPORT"
cat "$REPORT"
