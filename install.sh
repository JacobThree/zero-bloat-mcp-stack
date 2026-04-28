#!/bin/bash
set -e

echo "Deploying Zero-Bloat AI Stack..."

# 1. Install global routing and sandboxing tools
echo "-> Installing QLN and Context-Mode..."
npm install -g context-mode n2-qln

echo "-> Installing Graphify..."
pip install graphifyy

# 2. Install RTK (Rust Token Killer)
echo "-> Installing RTK..."
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
rtk init --global

# 3. Install Caveman
echo "-> Installing Caveman Skill..."
mkdir -p ~/.claude/skills/caveman
git clone https://github.com/JuliusBrussee/caveman.git /tmp/caveman-tmp
cp -r /tmp/caveman-tmp/caveman/. ~/.claude/skills/caveman/
rm -rf /tmp/caveman-tmp

# 4. Fetch Agent Skills
echo "-> Fetching Addy Osmani's Agent Skills..."
mkdir -p ~/.dotfiles/ai_blueprints
if [ ! -d "$HOME/.dotfiles/ai_blueprints/agent-skills" ]; then
    git clone https://github.com/addyosmani/agent-skills.git ~/.dotfiles/ai_blueprints/agent-skills
fi

echo "====================================="
echo "Stack deployed successfully!"
echo "To initialize a new project, run:"
echo "\$caveman Execute ~/.dotfiles/ai_blueprints/project_init.md strictly."
echo "====================================="
