#!/usr/bin/env bash
set -euo pipefail

mkdir -p .codex
out=".codex/stack-check.md"

if ! ( : > "$out" ) 2>/dev/null; then
  out="stack-check.md"
fi

run_check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "- PASS: ${label}" >> "$out"
  else
    echo "- FAIL: ${label}" >> "$out"
  fi
}

{
  echo "# Stack Smoke Check"
  echo
  echo "- Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "- Directory: $(pwd)"
  echo
  echo "## Results"
} > "$out"

run_check "rtk available" rtk --version
run_check "n2-qln available" n2-qln --help
run_check "context-mode available" context-mode --help
run_check "graphify available" python -m graphify --help

echo >> "$out"
echo "Done. Wrote $out"
