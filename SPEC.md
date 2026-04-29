# Spec: Token Savings Measurement + Visualization for Zero-Bloat Stack

## Assumptions
1. Goal measure total token savings from full stack (`rtk`, `n2-qln`, `context-mode`, `graphify`) vs baseline flow without stack.
2. Initial deliverable can be local artifact (Markdown report + graph file), not hosted dashboard.
3. Token counts include both input and output tokens per run, plus aggregate totals.
4. We can use repeatable benchmark scenarios from repo tasks (stack checks, file scans, test-like noisy commands).
5. Exact provider-billed token counts may not always be available; fallback is deterministic tokenizer estimate.

## Objective
Build reproducible benchmarking workflow that shows how many tokens stack saves overall and per-tool contribution, with clear before/after graph for input/output tokens.

Primary user: engineer running local AI-assisted coding workflows.

Success means user can run one command and get:
- baseline token totals,
- stack token totals,
- absolute savings,
- percent savings,
- graph comparing input/output with vs without stack.

## Tech Stack
- Shell scripts (`bash`/`zsh`) for benchmark orchestration
- Python 3 for token aggregation and chart generation
- `rtk` for command execution in stack mode
- Optional graph output:
  - Markdown Mermaid charts (zero extra deps), or
  - HTML Chart.js file (if richer graph needed)

## Commands
- Initialize benchmark dirs:
  - `mkdir -p benchmarks/scenarios benchmarks/results benchmarks/reports`
- Run baseline benchmark suite:
  - `bash benchmarks/run_benchmark.sh --mode baseline --out benchmarks/results/baseline.json`
- Run stack benchmark suite:
  - `rtk bash benchmarks/run_benchmark.sh --mode stack --out benchmarks/results/stack.json`
- Generate comparison report + graph:
  - `python benchmarks/scripts/generate_report.py --baseline benchmarks/results/baseline.json --stack benchmarks/results/stack.json --out benchmarks/reports/token-savings.md`
- Verify stack tools:
  - `rtk --version`
  - `n2-qln --help`
  - `context-mode --help`
  - `python -m graphify --help`

## Project Structure
- `benchmarks/scenarios/`
  - Scenario definitions (commands + expected noise level)
- `benchmarks/scripts/`
  - `token_counter.py` (normalize counts)
  - `generate_report.py` (aggregate + graph)
- `benchmarks/run_benchmark.sh`
  - Runs scenarios in chosen mode, captures raw/processed output, writes JSON
- `benchmarks/results/`
  - Raw run artifacts (`baseline.json`, `stack.json`, timestamps)
- `benchmarks/reports/`
  - Human-readable report + embedded graph
- `SPEC.md`
  - This specification

## Code Style
Conventions:
- Deterministic output keys and sorted JSON fields
- Scenario IDs use kebab-case
- Strict exit on errors in shell (`set -euo pipefail`)
- Small pure functions in Python for parse/aggregate/render

Example:
```bash
set -euo pipefail
MODE="${1:-baseline}"
OUT="${2:-benchmarks/results/run.json}"
```

```python
def percent_savings(before: int, after: int) -> float:
    if before <= 0:
        return 0.0
    return round(((before - after) / before) * 100, 2)
```

## Testing Strategy
Framework and checks:
- Shell lint: `shellcheck benchmarks/run_benchmark.sh`
- Python tests: `pytest benchmarks/tests -q`
- Golden-report test: compare generated report against fixture for stable scenarios

Test levels:
- Unit:
  - token math, percent math, per-scenario aggregation
- Integration:
  - one baseline + one stack run on sample scenario set
- Regression:
  - same input fixtures produce same report metrics

Coverage expectation:
- 90%+ on Python aggregation/report modules

## Boundaries
- Always:
  - Keep baseline and stack scenario sets identical
  - Record tool versions with each benchmark run
  - Separate measured data from inferred commentary
- Ask first:
  - Adding third-party telemetry SDKs
  - Sending benchmark data off machine
  - Changing default graph format from Markdown report
- Never:
  - Mix baseline and stack outputs in one raw file
  - Claim billed-token accuracy when only estimates used
  - Delete historical benchmark results without approval

## Success Criteria
1. Running benchmark in both modes produces two valid JSON result files with input/output token totals.
2. Comparison report includes:
   - total input tokens baseline vs stack,
   - total output tokens baseline vs stack,
   - combined total savings (absolute + percent),
   - per-scenario breakdown table,
   - graph showing before/after input and output bars.
3. Report explicitly labels token source per metric (`provider`, `rtk`, or `estimated`).
4. Same benchmark scenario rerun yields stable savings trend (variance threshold documented).
5. User can answer in under 30 seconds: "How much tokens this stack saves overall?"

## Resolved Decisions
1. Graph target: Markdown report with embedded Mermaid bar chart only (v1). No HTML/PNG in v1.
2. Token source: local deterministic estimator first (v1), labeled `estimated` in all outputs.
3. Scenario corpus: repo-local command scenarios only (v1), no external telemetry or network calls.
4. Per-tool ablation: defer to v2. v1 compares only `baseline` vs `full stack`.
