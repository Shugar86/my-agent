#!/usr/bin/env bash
# Fail if tracked files contain live API key patterns or .env secrets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0

if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "ERROR: .env is tracked in git — remove it and rotate keys"
  fail=1
fi

PATTERNS=(
  'sk-or-v1-'
  'sk-kimi-'
  'tvly-dev-'
  'NEUROAPI_API_KEY=[^[:space:]]'
)

while IFS= read -r -d '' file; do
  case "$file" in
    *.example|*.md|scripts/check-secrets.sh|.github/*|TROUBLES.md|tests/*|core/kimi_provider.py) continue ;;
  esac
  for pat in "${PATTERNS[@]}"; do
    if grep -qE "$pat" "$file" 2>/dev/null; then
      echo "ERROR: possible secret in $file (pattern: $pat)"
      fail=1
    fi
  done
done < <(git ls-files -z '*.py' '*.json' '*.yaml' '*.yml' '*.toml' '*.sh' '*.env*' 2>/dev/null || true)

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi

echo "Secrets check passed"
