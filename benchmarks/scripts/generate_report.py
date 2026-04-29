#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.scripts.token_counter import compare_runs


def _max_value(*values: int) -> int:
    m = max(values) if values else 0
    if m <= 0:
        return 10
    return int(m * 1.1) + 1


def build_markdown(report: dict) -> str:
    baseline_totals = report["baseline"]["totals"]
    stack_totals = report["stack"]["totals"]
    savings = report["savings"]
    token_source = report.get("token_source", "estimated")

    b_input = baseline_totals["input_tokens_estimated"]
    b_output = baseline_totals["output_tokens_estimated"]
    b_total = baseline_totals["total_tokens_estimated"]

    s_input = stack_totals["input_tokens_estimated"]
    s_output = stack_totals["output_tokens_estimated"]
    s_total = stack_totals["total_tokens_estimated"]

    y_max = _max_value(b_input, b_output, b_total, s_input, s_output, s_total)

    lines: list[str] = []
    lines.append("# Token Savings Report")
    lines.append("")
    lines.append(f"- Token source: `{token_source}`")
    lines.append(f"- Estimation ratio: `{report['estimation']['bytes_per_token']} bytes/token`")
    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append("| Metric | Baseline | Stack | Saved | Saved % |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(
        f"| Input tokens | {b_input} | {s_input} | {savings['input_tokens_saved']} | {savings['input_percent_saved']}% |"
    )
    lines.append(
        f"| Output tokens | {b_output} | {s_output} | {savings['output_tokens_saved']} | {savings['output_percent_saved']}% |"
    )
    lines.append(
        f"| Total tokens | {b_total} | {s_total} | {savings['total_tokens_saved']} | {savings['total_percent_saved']}% |"
    )
    lines.append("")
    lines.append("## Baseline vs Stack (Estimated Tokens)")
    lines.append("")
    lines.append("```mermaid")
    lines.append("xychart-beta")
    lines.append('  title "Baseline vs Stack Token Comparison"')
    lines.append('  x-axis ["Input","Output","Total"]')
    lines.append(f'  y-axis "Tokens" 0 --> {y_max}')
    lines.append(f'  bar "Baseline" [{b_input},{b_output},{b_total}]')
    lines.append(f'  bar "Stack" [{s_input},{s_output},{s_total}]')
    lines.append("```")
    lines.append("")
    lines.append("## Per-Scenario Breakdown")
    lines.append("")
    lines.append("| Scenario | Baseline Total | Stack Total | Saved | Saved % |")
    lines.append("|---|---:|---:|---:|---:|")

    stack_by_id = {item["id"]: item for item in report["stack"]["scenarios"]}
    savings_by_id = {item["id"]: item for item in report["savings"]["per_scenario"]}
    for base in report["baseline"]["scenarios"]:
        sid = base["id"]
        stack = stack_by_id.get(sid)
        save = savings_by_id.get(sid)
        if stack is None or save is None:
            continue
        lines.append(
            f"| `{sid}` | {base['total_tokens_estimated']} | {stack['total_tokens_estimated']} | {save['total_tokens_saved']} | {save['total_percent_saved']}% |"
        )

    lines.append("")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate markdown token savings report with Mermaid chart.")
    parser.add_argument("--baseline", required=True, help="Path to baseline run JSON")
    parser.add_argument("--stack", required=True, help="Path to stack run JSON")
    parser.add_argument("--out", required=True, help="Output markdown path")
    parser.add_argument(
        "--bytes-per-token",
        type=int,
        default=4,
        help="Deterministic conversion ratio for estimated tokens (default: 4)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    import json

    baseline = json.loads(Path(args.baseline).read_text())
    stack = json.loads(Path(args.stack).read_text())
    report = compare_runs(baseline, stack, bytes_per_token=args.bytes_per_token)
    markdown = build_markdown(report)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
