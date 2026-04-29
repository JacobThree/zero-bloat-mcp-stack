# Implementation Plan: Token Savings Measurement + Visualization

## Overview
Implement local benchmark pipeline that measures input/output token estimates for identical scenarios in two modes (`baseline`, `stack`), then generates single Markdown report with aggregate savings and Mermaid graph.

## Architecture Decisions
- Use Markdown + Mermaid only for graph output in v1. Reason: zero extra runtime dependencies.
- Use deterministic local token estimator in v1 and label metrics as `estimated`. Reason: no provider/API dependency.
- Keep scenarios repo-local and deterministic. Reason: reproducible results and low setup cost.
- Compare only baseline vs full stack in v1. Reason: smallest useful scope; ablation deferred.

## Task List

### Phase 1: Foundation

## Task 1: Create benchmark skeleton
**Description:** Add benchmark directories and empty scenario/result/report placeholders.

**Acceptance criteria:**
- [ ] `benchmarks/scenarios`, `benchmarks/scripts`, `benchmarks/results`, `benchmarks/reports` exist.
- [ ] Placeholder README in `benchmarks/` explains run flow.

**Verification:**
- [ ] Manual check: `rtk rg --files benchmarks`

**Dependencies:** None

**Files likely touched:**
- `benchmarks/README.md`
- `benchmarks/.gitkeep` files as needed

**Estimated scope:** Small

## Task 2: Define deterministic scenario set
**Description:** Create scenario manifest with repo-local commands executed in both modes.

**Acceptance criteria:**
- [ ] Scenario manifest exists and is machine-readable (JSON or YAML).
- [ ] Each scenario has stable `id`, `command`, `timeout_sec`.
- [ ] Scenario list excludes network-dependent commands.

**Verification:**
- [ ] Manual check: inspect scenario manifest.

**Dependencies:** Task 1

**Files likely touched:**
- `benchmarks/scenarios/scenarios.json`

**Estimated scope:** Small

### Checkpoint: Foundation
- [ ] Directory structure complete
- [ ] Scenario set approved and reproducible

### Phase 2: Measurement Pipeline

## Task 3: Implement benchmark runner
**Description:** Build `run_benchmark.sh` to execute scenarios, capture stdout/stderr, and emit structured JSON.

**Acceptance criteria:**
- [ ] Runner supports `--mode baseline|stack` and `--out <file>`.
- [ ] Output JSON includes per-scenario raw lengths and timestamps.
- [ ] Runner exits non-zero on invalid arguments.

**Verification:**
- [ ] Run: `bash benchmarks/run_benchmark.sh --mode baseline --out benchmarks/results/baseline.json`
- [ ] Run: `rtk bash benchmarks/run_benchmark.sh --mode stack --out benchmarks/results/stack.json`

**Dependencies:** Task 2

**Files likely touched:**
- `benchmarks/run_benchmark.sh`

**Estimated scope:** Medium

## Task 4: Implement token estimator + aggregator
**Description:** Add Python module that converts captured text lengths to deterministic token estimates and computes savings.

**Acceptance criteria:**
- [ ] Estimator returns input/output totals per scenario and aggregate totals.
- [ ] Output marks source as `estimated`.
- [ ] Savings math includes absolute and percent values.

**Verification:**
- [ ] Run unit tests for math helpers.
- [ ] Manual check of aggregate JSON.

**Dependencies:** Task 3

**Files likely touched:**
- `benchmarks/scripts/token_counter.py`
- `benchmarks/tests/test_token_counter.py`

**Estimated scope:** Medium

### Checkpoint: Measurement Pipeline
- [ ] Baseline + stack JSON both generated
- [ ] Aggregate savings math validated

### Phase 3: Reporting

## Task 5: Generate Markdown report with Mermaid graph
**Description:** Build report generator that emits summary table and Mermaid bars for input/output baseline vs stack.

**Acceptance criteria:**
- [ ] Report contains totals, percent savings, per-scenario table.
- [ ] Report contains Mermaid chart for input/output comparison.
- [ ] Report includes token source label (`estimated`).

**Verification:**
- [ ] Run: `python benchmarks/scripts/generate_report.py --baseline benchmarks/results/baseline.json --stack benchmarks/results/stack.json --out benchmarks/reports/token-savings.md`
- [ ] Manual render check of Mermaid block.

**Dependencies:** Task 4

**Files likely touched:**
- `benchmarks/scripts/generate_report.py`
- `benchmarks/reports/token-savings.md` (generated)

**Estimated scope:** Medium

## Task 6: Add regression and usage docs
**Description:** Add tests for report stability and top-level usage instructions.

**Acceptance criteria:**
- [ ] Regression test verifies stable report metrics for fixture input.
- [ ] README section documents one-command workflow.

**Verification:**
- [ ] Run: `pytest benchmarks/tests -q`
- [ ] Manual check: commands in docs run as written.

**Dependencies:** Task 5

**Files likely touched:**
- `benchmarks/tests/test_generate_report.py`
- `README.md` (benchmark section)

**Estimated scope:** Medium

### Checkpoint: Complete
- [ ] All criteria in `SPEC.md` satisfied
- [ ] End-to-end run produces final report and graph
- [ ] Ready for `/build`

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Token estimate not representative of billed tokens | Medium | Label all numbers `estimated`; keep deterministic method explicit |
| Scenario outputs too small to show meaningful delta | Medium | Include at least one high-output local scenario |
| Non-deterministic command output causes noisy comparisons | Medium | Use stable local commands and fixed fixtures |
| Missing runtime tools on machine | Low | Gate with preflight checks and clear fail messages |

## Open Questions
- None for v1 scope. Ablation and provider-exact usage tracked as v2 enhancements.
