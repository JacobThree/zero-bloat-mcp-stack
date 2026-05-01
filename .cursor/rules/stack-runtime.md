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
