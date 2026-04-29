# Benchmarks

Purpose: measure token savings for `baseline` vs `stack` runs with identical local scenarios.

## Run Flow

1. Define scenarios in `benchmarks/scenarios/`.
2. Run baseline benchmark:
   - `bash benchmarks/run_benchmark.sh --mode baseline --out benchmarks/results/baseline.json`
3. Run stack benchmark:
   - `bash benchmarks/run_benchmark.sh --mode stack --out benchmarks/results/stack.json`
4. Generate report:
   - `python benchmarks/scripts/generate_report.py --baseline benchmarks/results/baseline.json --stack benchmarks/results/stack.json --out benchmarks/reports/token-savings.md`

## Directory Map

- `scenarios/`: benchmark scenario manifests
- `scripts/`: token counting + report generation
- `results/`: generated benchmark JSON/log artifacts
- `reports/`: generated markdown reports with charts

## Caveman A/B Benchmark

Offline deterministic run (no external model/API required):

```bash
python benchmarks/scripts/caveman_benchmark.py \
  --prompts benchmarks/scenarios/caveman_prompts.json \
  --runner heuristic \
  --out-json benchmarks/results/caveman-ab.json \
  --out-report benchmarks/reports/caveman-ab.md
```

## Full Stack Benchmark

Single command to benchmark combined savings from:
- RTK CLI filtering scenarios
- Caveman response compression scenarios

```bash
python benchmarks/scripts/full_stack_benchmark.py --caveman-runner heuristic --out-json benchmarks/results/full-stack.json --out-report benchmarks/reports/full-stack.md
```

Read merged report:

```bash
cat benchmarks/reports/full-stack.md
```

## Generate Graphic

Generate social graphics (1200x627) from latest full-stack benchmark:

```bash
python benchmarks/scripts/generate_graphic.py --input benchmarks/results/full-stack.json --output benchmarks/reports/token-savings-graphic.svg
python benchmarks/scripts/generate_graphic_png.py --input benchmarks/results/full-stack.json --output benchmarks/reports/token-savings-graphic.png
```

Top-level README snapshot uses:
- `benchmarks/reports/token-savings-graphic.png`

Real model run (same prompts, two system modes):

```bash
python benchmarks/scripts/caveman_benchmark.py \
  --prompts benchmarks/scenarios/caveman_prompts.json \
  --runner command \
  --normal-command "your-llm-cli --system \"$BENCH_SYSTEM_PROMPT\" --prompt-file \"$BENCH_PROMPT_FILE\"" \
  --caveman-command "your-llm-cli --system \"$BENCH_SYSTEM_PROMPT\" --prompt-file \"$BENCH_PROMPT_FILE\"" \
  --normal-system "Respond clearly with complete professional sentences." \
  --caveman-system "Respond terse like smart caveman. Keep technical accuracy. Drop filler and hedging." \
  --out-json benchmarks/results/caveman-ab.json \
  --out-report benchmarks/reports/caveman-ab.md
```
