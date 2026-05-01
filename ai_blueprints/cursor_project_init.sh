#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ~/.dotfiles/ai_blueprints/cursor_project_init.sh [project_dir]
PROJECT_DIR="${1:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_DIR="${DOTFILES_DIR}/ai_blueprints/agent-skills/skills"
RULES_DIR="${PROJECT_DIR}/.cursor/rules"
CHECK_FILE="${PROJECT_DIR}/.cursor/stack-check.md"

require_file() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "Missing required file: $file" >&2
    exit 1
  fi
}

require_file "${SKILLS_DIR}/spec-driven-development/SKILL.md"
require_file "${SKILLS_DIR}/planning-and-task-breakdown/SKILL.md"
require_file "${SKILLS_DIR}/incremental-implementation/SKILL.md"
require_file "${SKILLS_DIR}/test-driven-development/SKILL.md"
require_file "${SKILLS_DIR}/code-review-and-quality/SKILL.md"
require_file "${SKILLS_DIR}/shipping-and-launch/SKILL.md"

mkdir -p "${RULES_DIR}"

cp "${SKILLS_DIR}/spec-driven-development/SKILL.md" "${RULES_DIR}/spec-driven-development.md"
cp "${SKILLS_DIR}/planning-and-task-breakdown/SKILL.md" "${RULES_DIR}/planning-and-task-breakdown.md"
cp "${SKILLS_DIR}/incremental-implementation/SKILL.md" "${RULES_DIR}/incremental-implementation.md"
cp "${SKILLS_DIR}/test-driven-development/SKILL.md" "${RULES_DIR}/test-driven-development.md"
cp "${SKILLS_DIR}/code-review-and-quality/SKILL.md" "${RULES_DIR}/code-review-and-quality.md"
cp "${SKILLS_DIR}/shipping-and-launch/SKILL.md" "${RULES_DIR}/shipping-and-launch.md"

cat > "${RULES_DIR}/stack-runtime.md" <<'EOF'
# Zero-Bloat Stack Runtime (Cursor)

## Core Workflow
- Follow lifecycle in order: spec -> plan -> build -> test -> review -> ship.
- Keep responses concise and implementation-first.
- Prefer small diffs and verifiable steps.

## Tooling Rules
- Prefix shell commands with `rtk` when available.
- Use `n2-qln`, `context-mode`, and `graphify` if installed.
- For architecture questions, refresh graph via `graphify update .`.

## Validation Rules
- Run tests or smoke checks before final response.
- Call out unknowns and failed checks explicitly.
EOF

{
  echo "# Cursor Stack Check"
  echo
  echo "- Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "- Project: ${PROJECT_DIR}"
  echo
  echo "## Runtime"
  if command -v rtk >/dev/null 2>&1; then
    echo "- PASS: rtk available"
  else
    echo "- FAIL: rtk missing"
  fi
  if command -v n2-qln >/dev/null 2>&1; then
    echo "- PASS: n2-qln available"
  else
    echo "- FAIL: n2-qln missing"
  fi
  if command -v context-mode >/dev/null 2>&1; then
    echo "- PASS: context-mode available"
  else
    echo "- FAIL: context-mode missing"
  fi
  if python -m graphify --help >/dev/null 2>&1; then
    echo "- PASS: graphify available"
  else
    echo "- FAIL: graphify missing"
  fi
  echo
  echo "## Rules Files"
  for rule in \
    spec-driven-development.md \
    planning-and-task-breakdown.md \
    incremental-implementation.md \
    test-driven-development.md \
    code-review-and-quality.md \
    shipping-and-launch.md \
    stack-runtime.md; do
    if [ -f "${RULES_DIR}/${rule}" ]; then
      echo "- PASS: .cursor/rules/${rule}"
    else
      echo "- FAIL: .cursor/rules/${rule}"
    fi
  done
} > "${CHECK_FILE}"

echo "Cursor primed. Rules mapped. Stack check written to ${CHECK_FILE}."
