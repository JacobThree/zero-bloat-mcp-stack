# AI Workspace Initialization Directives
Execute steps strictly. No verbose explanation.

1. Create `.codex` directory: `mkdir -p .codex`.
2. Create `CLAUDE.md` with project context:
   """
   # Project Context
   Purpose: [Deducted Purpose]
   Status: Initialized

   ## Engineering Lifecycle
   Use Agent Skills commands per phase:
   - Define: /spec
   - Plan: /plan
   - Build: /build
   - Verify: /test
   - Review: /review
   - Ship: /ship

   ## Context Efficiency Rules
   - Use relative paths for file and shell operations.
   - Do not print full absolute paths unless asked.
   - Keep responses concise.
   """
3. Create `.codex/config.toml` with exact content:
   ```toml
   [mcp.servers.n2-qln]
   command = "n2-qln"

   [mcp.servers.context-mode]
   command = "context-mode"

   [mcp.servers.graphify]
   command = "python"
   args = ["-m", "graphify.serve", "graphify-out/graph.json"]
   ```
4. Run stack smoke checks and write output to `.codex/stack-check.md`:
   - `rtk --version`
   - `n2-qln --help`
   - `context-mode --help`
   - `python -m graphify --help`
   Include success/fail for each command.
5. Confirm with single line only:
   `System primed. Skills mapped. Stack check written to .codex/stack-check.md.`
