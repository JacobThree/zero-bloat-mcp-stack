#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

DEFAULT_BYTES_PER_TOKEN = 4


def estimate_tokens_from_bytes(byte_count: int, bytes_per_token: int = DEFAULT_BYTES_PER_TOKEN) -> int:
    if byte_count <= 0:
        return 0
    if bytes_per_token <= 0:
        raise ValueError("bytes_per_token must be > 0")
    return int(math.ceil(byte_count / bytes_per_token))


def percent_saved(before: int, after: int) -> float:
    if before <= 0:
        return 0.0
    return round(((before - after) / before) * 100, 2)


def _output_bytes(result: dict[str, Any]) -> int:
    if "combined_bytes" in result:
        return int(result.get("combined_bytes", 0))
    return int(result.get("stdout_bytes", 0)) + int(result.get("stderr_bytes", 0))


def aggregate_run(run_doc: dict[str, Any], bytes_per_token: int = DEFAULT_BYTES_PER_TOKEN) -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    input_total = 0
    output_total = 0

    for result in run_doc.get("results", []):
        scenario_id = str(result.get("id", "unknown"))
        command = str(result.get("executed_command") or result.get("command", ""))
        command_bytes = len(command.encode("utf-8"))
        output_bytes = _output_bytes(result)

        input_tokens = estimate_tokens_from_bytes(command_bytes, bytes_per_token)
        output_tokens = estimate_tokens_from_bytes(output_bytes, bytes_per_token)
        total_tokens = input_tokens + output_tokens

        input_total += input_tokens
        output_total += output_tokens

        scenarios.append(
            {
                "id": scenario_id,
                "command": command,
                "command_bytes": command_bytes,
                "output_bytes": output_bytes,
                "input_tokens_estimated": input_tokens,
                "output_tokens_estimated": output_tokens,
                "total_tokens_estimated": total_tokens,
                "exit_code": int(result.get("exit_code", 0)),
                "timed_out": bool(result.get("timed_out", False)),
            }
        )

    return {
        "mode": run_doc.get("mode", "unknown"),
        "token_source": "estimated",
        "estimation": {"bytes_per_token": bytes_per_token},
        "totals": {
            "input_tokens_estimated": input_total,
            "output_tokens_estimated": output_total,
            "total_tokens_estimated": input_total + output_total,
        },
        "scenarios": scenarios,
    }


def compare_runs(
    baseline: dict[str, Any], stack: dict[str, Any], bytes_per_token: int = DEFAULT_BYTES_PER_TOKEN
) -> dict[str, Any]:
    base_agg = aggregate_run(baseline, bytes_per_token)
    stack_agg = aggregate_run(stack, bytes_per_token)

    base_totals = base_agg["totals"]
    stack_totals = stack_agg["totals"]

    input_saved = base_totals["input_tokens_estimated"] - stack_totals["input_tokens_estimated"]
    output_saved = base_totals["output_tokens_estimated"] - stack_totals["output_tokens_estimated"]
    total_saved = base_totals["total_tokens_estimated"] - stack_totals["total_tokens_estimated"]

    stack_by_id = {item["id"]: item for item in stack_agg["scenarios"]}
    scenario_savings: list[dict[str, Any]] = []
    for base_item in base_agg["scenarios"]:
        stack_item = stack_by_id.get(base_item["id"])
        if stack_item is None:
            continue

        base_input = base_item["input_tokens_estimated"]
        stack_input = stack_item["input_tokens_estimated"]
        base_output = base_item["output_tokens_estimated"]
        stack_output = stack_item["output_tokens_estimated"]
        base_total = base_item["total_tokens_estimated"]
        stack_total = stack_item["total_tokens_estimated"]

        scenario_savings.append(
            {
                "id": base_item["id"],
                "input_tokens_saved": base_input - stack_input,
                "output_tokens_saved": base_output - stack_output,
                "total_tokens_saved": base_total - stack_total,
                "input_percent_saved": percent_saved(base_input, stack_input),
                "output_percent_saved": percent_saved(base_output, stack_output),
                "total_percent_saved": percent_saved(base_total, stack_total),
            }
        )

    return {
        "schema_version": 1,
        "token_source": "estimated",
        "estimation": {"bytes_per_token": bytes_per_token},
        "baseline": base_agg,
        "stack": stack_agg,
        "savings": {
            "input_tokens_saved": input_saved,
            "output_tokens_saved": output_saved,
            "total_tokens_saved": total_saved,
            "input_percent_saved": percent_saved(
                base_totals["input_tokens_estimated"], stack_totals["input_tokens_estimated"]
            ),
            "output_percent_saved": percent_saved(
                base_totals["output_tokens_estimated"], stack_totals["output_tokens_estimated"]
            ),
            "total_percent_saved": percent_saved(
                base_totals["total_tokens_estimated"], stack_totals["total_tokens_estimated"]
            ),
            "per_scenario": scenario_savings,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate input/output tokens from benchmark run JSON and compute baseline vs stack savings."
    )
    parser.add_argument("--baseline", required=True, help="Path to baseline run JSON")
    parser.add_argument("--stack", required=True, help="Path to stack run JSON")
    parser.add_argument("--out", required=True, help="Output JSON path for estimated token comparison")
    parser.add_argument(
        "--bytes-per-token",
        type=int,
        default=DEFAULT_BYTES_PER_TOKEN,
        help="Deterministic conversion ratio for estimated tokens (default: 4)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    baseline = json.loads(Path(args.baseline).read_text())
    stack = json.loads(Path(args.stack).read_text())
    report = compare_runs(baseline, stack, bytes_per_token=args.bytes_per_token)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
