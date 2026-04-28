# AI Workspace Initialization Directives
Execute these steps strictly.

1. **Permissions**: Run `mkdir -p .skills .codex` immediately.
2. **Skill Loading**: Analyze project; copy TOP 3 relevant skills from `~/.dotfiles/ai_blueprints/agent-skills/` to `./.skills/`.
3. **Memory Card**: Create `CLAUDE.md`. Populate with exactly:
   """
   # Project Context
   Purpose: [Deducted Purpose]
   Status: Initialized
   
   ## Context Efficiency Rules
   - Use relative paths (e.g., `./.skills/`) for all file and shell operations.
   - Never output full paths unless explicitly requested.
   - Use $caveman brevity for all responses.
   """
4. **Config**: Write `.codex/config.toml` using `cat`:
[mcp.servers.n2-qln]
command = "n2-qln"
[mcp.servers.context-mode]
command = "context-mode"
[mcp.servers.graphify]
command = "python"
args = ["-m", "graphify.serve", "graphify-out/graph.json"]

5. **Confirm**: Output "System primed. Relative paths enforced."
