#!/bin/bash
set -euo pipefail

echo "Deploying Zero-Bloat AI Stack..."

# 1. Install global routing and sandboxing tools
npm install -g context-mode n2-qln
pip install graphifyy
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
rtk init --global

# 1b. Stabilize n2-qln runtime paths (avoid global-dir writes and watcher hangs)
mkdir -p "$HOME/.n2-qln/data"
N2_QLN_INSTALL_DIR="$(npm root -g)/n2-qln"
if [ -d "$N2_QLN_INSTALL_DIR" ]; then
  cat > "$N2_QLN_INSTALL_DIR/config.local.js" <<EOF
module.exports = {
  dataDir: '${HOME}/.n2-qln/data',
  providers: { enabled: false },
};
EOF
fi

# 2. Deploy Global Agent Skills (Native Lazy-Loading)
echo "-> Linking Agent Skills to Global CLI..."
mkdir -p ~/.claude/skills
SKILLS_PATH="$HOME/.dotfiles/ai_blueprints/agent-skills/skills"

# Map the high-level lifecycle commands
ln -sf "$SKILLS_PATH/spec-driven-development/SKILL.md" ~/.claude/skills/spec.md
ln -sf "$SKILLS_PATH/planning-and-task-breakdown/SKILL.md" ~/.claude/skills/plan.md
ln -sf "$SKILLS_PATH/incremental-implementation/SKILL.md" ~/.claude/skills/build.md
ln -sf "$SKILLS_PATH/test-driven-development/SKILL.md" ~/.claude/skills/test.md
ln -sf "$SKILLS_PATH/code-review-and-quality/SKILL.md" ~/.claude/skills/review.md
ln -sf "$SKILLS_PATH/code-simplification/SKILL.md" ~/.claude/skills/code-simplify.md
ln -sf "$SKILLS_PATH/shipping-and-launch/SKILL.md" ~/.claude/skills/ship.md

# Link domain-specific skills for auto-discovery
ln -sf "$SKILLS_PATH/frontend-ui-engineering/SKILL.md" ~/.claude/skills/ui.md
ln -sf "$SKILLS_PATH/security-and-hardening/SKILL.md" ~/.claude/skills/security.md

echo "-> Running global smoke check..."
command -v rtk >/dev/null
command -v n2-qln >/dev/null
command -v context-mode >/dev/null
python -c "import graphify" >/dev/null 2>&1

echo "Stack deployed."
echo "Skills mapped: /spec /plan /build /test /review /ship"
echo "Per-project verify: ./ai_blueprints/stack_smoke_test.sh"
