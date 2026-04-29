#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.scripts.token_counter import percent_saved


def _run(cmd: list[str], cwd: Path) -> None:
    completed = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if completed.returncode != 0:
        err = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise SystemExit(f"Command failed ({' '.join(cmd)}): {err}")


def _build_report(doc: dict[str, Any]) -> str:
    cli = doc["components"]["cli_stack"]
    cav = doc["components"]["caveman_ab"]
    overall = doc["overall"]

    b_in = overall["baseline"]["input_tokens_estimated"]
    b_out = overall["baseline"]["output_tokens_estimated"]
    b_total = overall["baseline"]["total_tokens_estimated"]

    s_in = overall["stack"]["input_tokens_estimated"]
    s_out = overall["stack"]["output_tokens_estimated"]
    s_total = overall["stack"]["total_tokens_estimated"]

    y_max = max(b_total, s_total, 10)
    y = int(y_max * 1.1) + 1

    lines = [
        "# Full Stack Token Savings Report",
        "",
        "- Scope: RTK CLI filtering + Caveman response compression",
        "- Token source: `estimated`",
        f"- Estimation ratio: `{doc['estimation']['bytes_per_token']} bytes/token`",
        "",
        "## Component Breakdown",
        "",
        "| Component | Baseline Total | Stack Total | Saved | Saved % |",
        "|---|---:|---:|---:|---:|",
        f"| CLI stack (RTK wrappers) | {cli['baseline_total_tokens_estimated']} | {cli['stack_total_tokens_estimated']} | {cli['total_tokens_saved']} | {cli['total_percent_saved']}% |",
        f"| Caveman A/B (responses) | {cav['baseline_total_tokens_estimated']} | {cav['stack_total_tokens_estimated']} | {cav['total_tokens_saved']} | {cav['total_percent_saved']}% |",
        "",
        "## Overall Totals",
        "",
        "| Metric | Baseline | Stack | Saved | Saved % |",
        "|---|---:|---:|---:|---:|",
        f"| Input tokens | {b_in} | {s_in} | {overall['savings']['input_tokens_saved']} | {overall['savings']['input_percent_saved']}% |",
        f"| Output tokens | {b_out} | {s_out} | {overall['savings']['output_tokens_saved']} | {overall['savings']['output_percent_saved']}% |",
        f"| Total tokens | {b_total} | {s_total} | {overall['savings']['total_tokens_saved']} | {overall['savings']['total_percent_saved']}% |",
        "",
        "## Baseline vs Stack (Estimated Tokens)",
        "",
        "```mermaid",
        "xychart-beta",
        '  title "Full Stack Baseline vs Stack Tokens"',
        '  x-axis ["Input","Output","Total"]',
        f'  y-axis "Tokens" 0 --> {y}',
        f'  bar "Baseline" [{b_in},{b_out},{b_total}]',
        f'  bar "Stack" [{s_in},{s_out},{s_total}]',
        "```",
        "",
        "## Notes",
        "",
        "- Included now: RTK command filtering and Caveman style compression.",
        "- Not included yet: n2-qln/context-mode/graphify runtime effects (need app-level harness).",
        "",
    ]
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full stack benchmark (RTK CLI + Caveman A/B) and merge totals.")
    parser.add_argument("--bytes-per-token", type=int, default=4)
    parser.add_argument("--cli-scenarios", default="benchmarks/scenarios/scenarios.json")
    parser.add_argument("--caveman-prompts", default="benchmarks/scenarios/caveman_prompts.json")
    parser.add_argument("--caveman-runner", choices=["heuristic", "command"], default="heuristic")
    parser.add_argument("--normal-command", default="")
    parser.add_argument("--caveman-command", default="")
    parser.add_argument("--normal-system", default="Respond clearly with complete professional sentences.")
    parser.add_argument(
        "--caveman-system",
        default="Respond terse like smart caveman. Keep technical accuracy. Drop filler and hedging.",
    )
    parser.add_argument("--out-json", default="benchmarks/results/full-stack.json")
    parser.add_argument("--out-report", default="benchmarks/reports/full-stack.md")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    cwd = ROOT

    cli_baseline = Path("benchmarks/results/baseline.json")
    cli_stack = Path("benchmarks/results/stack.json")
    cli_estimates = Path("benchmarks/results/token-estimates.json")

    cav_json = Path("benchmarks/results/caveman-ab.json")
    cav_report = Path("benchmarks/reports/caveman-ab.md")

    _run(
        [
            "bash",
            "benchmarks/run_benchmark.sh",
            "--mode",
            "baseline",
            "--out",
            str(cli_baseline),
            "--scenarios",
            args.cli_scenarios,
        ],
        cwd,
    )
    _run(
        [
            "bash",
            "benchmarks/run_benchmark.sh",
            "--mode",
            "stack",
            "--out",
            str(cli_stack),
            "--scenarios",
            args.cli_scenarios,
        ],
        cwd,
    )
    _run(
        [
            "python",
            "benchmarks/scripts/token_counter.py",
            "--baseline",
            str(cli_baseline),
            "--stack",
            str(cli_stack),
            "--out",
            str(cli_estimates),
            "--bytes-per-token",
            str(args.bytes_per_token),
        ],
        cwd,
    )

    cav_cmd = [
        "python",
        "benchmarks/scripts/caveman_benchmark.py",
        "--prompts",
        args.caveman_prompts,
        "--runner",
        args.caveman_runner,
        "--out-json",
        str(cav_json),
        "--out-report",
        str(cav_report),
        "--normal-system",
        args.normal_system,
        "--caveman-system",
        args.caveman_system,
        "--bytes-per-token",
        str(args.bytes_per_token),
    ]
    if args.caveman_runner == "command":
        if not args.normal_command or not args.caveman_command:
            raise SystemExit("caveman-runner=command requires --normal-command and --caveman-command")
        cav_cmd.extend(["--normal-command", args.normal_command, "--caveman-command", args.caveman_command])
    _run(cav_cmd, cwd)

    cli_doc = json.loads((cwd / cli_estimates).read_text())
    cav_doc = json.loads((cwd / cav_json).read_text())

    cli_base = cli_doc["baseline"]["totals"]
    cli_stack_tot = cli_doc["stack"]["totals"]
    cav_base = cav_doc["normal"]["totals"]
    cav_stack_tot = cav_doc["caveman"]["totals"]

    base_in = cli_base["input_tokens_estimated"] + cav_base["input_tokens_estimated"]
    base_out = cli_base["output_tokens_estimated"] + cav_base["output_tokens_estimated"]
    base_total = cli_base["total_tokens_estimated"] + cav_base["total_tokens_estimated"]

    stack_in = cli_stack_tot["input_tokens_estimated"] + cav_stack_tot["input_tokens_estimated"]
    stack_out = cli_stack_tot["output_tokens_estimated"] + cav_stack_tot["output_tokens_estimated"]
    stack_total = cli_stack_tot["total_tokens_estimated"] + cav_stack_tot["total_tokens_estimated"]

    doc: dict[str, Any] = {
        "schema_version": 1,
        "token_source": "estimated",
        "estimation": {"bytes_per_token": args.bytes_per_token},
        "components": {
            "cli_stack": {
                "baseline_total_tokens_estimated": cli_base["total_tokens_estimated"],
                "stack_total_tokens_estimated": cli_stack_tot["total_tokens_estimated"],
                "total_tokens_saved": cli_doc["savings"]["total_tokens_saved"],
                "total_percent_saved": cli_doc["savings"]["total_percent_saved"],
            },
            "caveman_ab": {
                "baseline_total_tokens_estimated": cav_base["total_tokens_estimated"],
                "stack_total_tokens_estimated": cav_stack_tot["total_tokens_estimated"],
                "total_tokens_saved": cav_doc["savings"]["total_tokens_saved"],
                "total_percent_saved": cav_doc["savings"]["total_percent_saved"],
            },
        },
        "overall": {
            "baseline": {
                "input_tokens_estimated": base_in,
                "output_tokens_estimated": base_out,
                "total_tokens_estimated": base_total,
            },
            "stack": {
                "input_tokens_estimated": stack_in,
                "output_tokens_estimated": stack_out,
                "total_tokens_estimated": stack_total,
            },
            "savings": {
                "input_tokens_saved": base_in - stack_in,
                "output_tokens_saved": base_out - stack_out,
                "total_tokens_saved": base_total - stack_total,
                "input_percent_saved": percent_saved(base_in, stack_in),
                "output_percent_saved": percent_saved(base_out, stack_out),
                "total_percent_saved": percent_saved(base_total, stack_total),
            },
        },
    }

    out_json = Path(args.out_json)
    out_report = Path(args.out_report)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(doc, indent=2))
    out_report.write_text(_build_report(doc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
