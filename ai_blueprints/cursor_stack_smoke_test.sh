#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
OUT_FILE="${PROJECT_DIR}/.cursor/stack-check.md"

mkdir -p "${PROJECT_DIR}/.cursor"

run_check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "- PASS: ${label}" >> "${OUT_FILE}"
  else
    echo "- FAIL: ${label}" >> "${OUT_FILE}"
  fi
}

{
  echo "# Cursor Stack Smoke Check"
  echo
  echo "- Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "- Project: ${PROJECT_DIR}"
  echo
  echo "## Runtime"
} > "${OUT_FILE}"

run_check "rtk available" rtk --version
run_check "n2-qln available" n2-qln --help
run_check "context-mode available" context-mode --help
run_check "graphify available" python -m graphify --help

echo >> "${OUT_FILE}"
echo "## Rules" >> "${OUT_FILE}"
for rule in \
  spec-driven-development.md \
  planning-and-task-breakdown.md \
  incremental-implementation.md \
  test-driven-development.md \
  code-review-and-quality.md \
  shipping-and-launch.md \
  stack-runtime.md; do
  if [ -f "${PROJECT_DIR}/.cursor/rules/${rule}" ]; then
    echo "- PASS: .cursor/rules/${rule}" >> "${OUT_FILE}"
  else
    echo "- FAIL: .cursor/rules/${rule}" >> "${OUT_FILE}"
  fi
done

echo "Done. Wrote ${OUT_FILE}"
