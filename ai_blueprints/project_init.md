# AI Workspace Initialization Directives

You are initializing a zero-bloat environment for this project. Follow these steps exactly without verbose explanations.

1. **Skill Loading**: Create a `.skills/` directory. Analyze this project's purpose and copy the TOP 3 most relevant `.md` files from `~/.dotfiles/ai_blueprints/agent-skills/` into `./.skills/`.
2. **Memory Card**: Create a `CLAUDE.md` file in the root. This will act as our persistent memory card to save tokens.
3. **MCP Configuration**: Create `.codex/config.toml` with these exact local tool definitions:

[mcp.servers.n2-qln]
command = "n2-qln"

[mcp.servers.context-mode]
command = "context-mode"

[mcp.servers.graphify]
command = "python"
args = ["-m", "graphify.serve", "graphify-out/graph.json"]

4. **Confirmation**: Output exactly: "System primed. Loaded [Skill 1], [Skill 2], [Skill 3]. QLN Router Active."
