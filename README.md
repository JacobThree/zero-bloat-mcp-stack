# Zero-Bloat MCP Agent Stack

A highly optimized, token-efficient AI developer environment. 

This repository provides a zero-bloat pipeline for AI coding assistants. By combining Model Context Protocol (MCP) semantic routing, local CLI sandboxing, and progressive prompt disclosure, this stack prevents context rot and reduces input and output token costs. It is designed for token-efficient local development without exhausting system memory.

## Compatibility

This stack is primarily built and tested for UNIX-like environments and modern AI coding assistants.

* **Operating Systems:** macOS (Apple Silicon / M-Series tested) and Linux.
* **AI Assistants:** Fully compatible with Codex (Claude Code CLI). The underlying MCP servers and orchestration patterns can also be ported to Cursor and Google Antigravity with minor configuration tweaks.
* **Prerequisites:** Git, Node.js (npm), Python 3 (pip), and bash/zsh.

## The Stack

This dotfiles configuration automatically installs and links the following open-source tools:

* **[n2-qln](https://www.npmjs.com/package/n2-qln)**: A semantic MCP proxy router that acts as a gatekeeper, dynamically fetching tools only when the AI explicitly needs them.
* **[Context-Mode](https://www.npmjs.com/package/context-mode)**: Intercepts large terminal outputs (like test suites), runs them in an isolated sandbox, and returns compressed summaries to the AI.
* **[Graphifyy](https://pypi.org/project/graphifyy/)**: Builds a structural knowledge graph of your project, preventing the AI from reading raw files to understand architecture.
* **[RTK (Rust Token Killer)](https://github.com/rtk-ai/rtk)**: A background CLI hook that automatically strips formatting and verbosity from terminal logs before the LLM processes them.
* **[Caveman](https://github.com/JuliusBrussee/caveman)**: A system prompt skill that forces the AI to drop conversational filler and output bare-metal code.
* **[Agent Skills](https://github.com/addyosmani/agent-skills)**: Addy Osmani's progressive disclosure engineering prompts for modular, zero-bloat roleplaying.

## Installation

Clone this repository into a `.dotfiles` directory and run the installer.

```bash
git clone https://github.com/JacobThree/zero-bloat-mcp-stack.git ~/.dotfiles
cd ~/.dotfiles
chmod +x install.sh
./install.sh
```
What the script does:

- Installs global NPM packages for routing and sandboxing.

- Installs Python MCP servers for codebase mapping.

- Installs and initializes the Rust Token Killer.

- Clones the Caveman skill and Addy Osmani's agent skills directly into your local AI blueprints directory.

Usage

To initialize this architecture in a new or existing project, navigate to your project directory and run:

```bash
$caveman Execute ~/.dotfiles/ai_blueprints/project_init.md strictly.
```
This command will:

- Scaffold a local .skills/ directory containing only the exact domain-specific prompts needed for the current project.

- Generate a .codex/config.toml that routes your MCP tools through the QLN semantic proxy.

- Generate a CLAUDE.md memory card to persist architectural context across sessions, preventing the AI from re-reading the entire directory structure.

License

This project is licensed under the MIT License. See the LICENSE file for details.
