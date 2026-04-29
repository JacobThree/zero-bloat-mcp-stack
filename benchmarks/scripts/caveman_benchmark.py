#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.scripts.token_counter import estimate_tokens_from_bytes, percent_saved

DEFAULT_BYTES_PER_TOKEN = 4

NORMAL_SYSTEM_DEFAULT = "Respond clearly with complete professional sentences."
CAVEMAN_SYSTEM_DEFAULT = (
    "Respond terse like smart caveman. Keep technical accuracy. Drop filler and hedging."
)

STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "to",
    "of",
    "and",
    "that",
    "this",
    "it",
    "with",
    "for",
    "in",
    "on",
    "as",
    "at",
    "be",
    "by",
    "from",
    "or",
}


def _heuristic_normal(prompt: str) -> str:
    return (
        "Summary:\n"
        f"{prompt}\n\n"
        "Approach:\n"
        "1. Identify primary constraints and failure modes.\n"
        "2. Apply targeted fixes, then validate with measurable checks.\n"
        "3. Document follow-up actions for reliability and maintainability.\n"
    )


def _heuristic_caveman(prompt: str) -> str:
    words = re.findall(r"[A-Za-z0-9_'-]+|[^\w\s]", prompt)
    kept: list[str] = []
    for w in words:
        lw = w.lower()
        if re.match(r"^[A-Za-z]+$", w) and lw in STOPWORDS:
            continue
        kept.append(w)

    prompt_line = " ".join(kept)
    prompt_line = re.sub(r"\s+([,.;:!?])", r"\1", prompt_line).strip()
    return (
        f"{prompt_line}.\n"
        "Find bottleneck. Fix hot path. Verify metrics.\n"
        "Ship small steps. Watch errors. Iterate.\n"
    )


def _run_command(cmd: str, prompt: str, system_prompt: str, timeout_sec: int) -> tuple[str, int, str]:
    env = os.environ.copy()
    env["BENCH_SYSTEM_PROMPT"] = system_prompt

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
        tmp.write(prompt)
        prompt_file = tmp.name

    env["BENCH_PROMPT_FILE"] = prompt_file
    try:
        completed = subprocess.run(
            ["bash", "-lc", cmd],
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=timeout_sec,
            check=False,
            env=env,
        )
        stdout = (completed.stdout or b"").decode("utf-8", errors="replace")
        stderr = (completed.stderr or b"").decode("utf-8", errors="replace")
        return stdout, int(completed.returncode), stderr
    finally:
        try:
            os.unlink(prompt_file)
        except OSError:
            pass


def _estimate(prompt: str, response: str, system_prompt: str, bytes_per_token: int) -> dict[str, int]:
    input_bytes = len((system_prompt + "\n" + prompt).encode("utf-8"))
    output_bytes = len(response.encode("utf-8"))
    input_tokens = estimate_tokens_from_bytes(input_bytes, bytes_per_token)
    output_tokens = estimate_tokens_from_bytes(output_bytes, bytes_per_token)
    return {
        "input_bytes": input_bytes,
        "output_bytes": output_bytes,
        "input_tokens_estimated": input_tokens,
        "output_tokens_estimated": output_tokens,
        "total_tokens_estimated": input_tokens + output_tokens,
    }


def _load_prompts(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text())
    prompts = data.get("prompts", [])
    if not isinstance(prompts, list):
        raise SystemExit("Invalid prompts file: key 'prompts' must be a list")
    cleaned = []
    for idx, item in enumerate(prompts):
        if not isinstance(item, dict) or "id" not in item or "prompt" not in item:
            raise SystemExit(f"Invalid prompt at index {idx}")
        cleaned.append({"id": str(item["id"]), "prompt": str(item["prompt"])})
    return cleaned


def _build_markdown(report: dict[str, Any]) -> str:
    n = report["normal"]["totals"]
    c = report["caveman"]["totals"]
    s = report["savings"]
    max_y = max(n["total_tokens_estimated"], c["total_tokens_estimated"], 10)
    y = int(max_y * 1.1) + 1

    lines = [
        "# Caveman A/B Benchmark Report",
        "",
        f"- Token source: `estimated`",
        f"- Estimation ratio: `{report['estimation']['bytes_per_token']} bytes/token`",
        f"- Runner: `{report['runner']}`",
        "",
        "## Totals",
        "",
        "| Metric | Normal | Caveman | Saved | Saved % |",
        "|---|---:|---:|---:|---:|",
        f"| Input tokens | {n['input_tokens_estimated']} | {c['input_tokens_estimated']} | {s['input_tokens_saved']} | {s['input_percent_saved']}% |",
        f"| Output tokens | {n['output_tokens_estimated']} | {c['output_tokens_estimated']} | {s['output_tokens_saved']} | {s['output_percent_saved']}% |",
        f"| Total tokens | {n['total_tokens_estimated']} | {c['total_tokens_estimated']} | {s['total_tokens_saved']} | {s['total_percent_saved']}% |",
        "",
        "## Normal vs Caveman (Estimated Tokens)",
        "",
        "```mermaid",
        "xychart-beta",
        '  title "Normal vs Caveman Token Comparison"',
        '  x-axis ["Input","Output","Total"]',
        f'  y-axis "Tokens" 0 --> {y}',
        f"  bar \"Normal\" [{n['input_tokens_estimated']},{n['output_tokens_estimated']},{n['total_tokens_estimated']}]",
        f"  bar \"Caveman\" [{c['input_tokens_estimated']},{c['output_tokens_estimated']},{c['total_tokens_estimated']}]",
        "```",
        "",
        "## Per-Prompt Breakdown",
        "",
        "| Prompt | Normal Total | Caveman Total | Saved | Saved % |",
        "|---|---:|---:|---:|---:|",
    ]

    for row in report["savings"]["per_prompt"]:
        lines.append(
            f"| `{row['id']}` | {row['normal_total_tokens_estimated']} | {row['caveman_total_tokens_estimated']} | {row['total_tokens_saved']} | {row['total_percent_saved']}% |"
        )

    lines.append("")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark response token savings: normal vs caveman mode.")
    parser.add_argument("--prompts", required=True, help="Prompt corpus JSON path")
    parser.add_argument("--out-json", required=True, help="Output JSON path")
    parser.add_argument("--out-report", required=True, help="Output Markdown report path")
    parser.add_argument(
        "--runner",
        choices=["heuristic", "command"],
        default="heuristic",
        help="heuristic=offline deterministic demo; command=run real model commands",
    )
    parser.add_argument("--normal-command", default="", help="Shell command for normal mode (runner=command)")
    parser.add_argument("--caveman-command", default="", help="Shell command for caveman mode (runner=command)")
    parser.add_argument("--normal-system", default=NORMAL_SYSTEM_DEFAULT, help="System prompt for normal mode")
    parser.add_argument("--caveman-system", default=CAVEMAN_SYSTEM_DEFAULT, help="System prompt for caveman mode")
    parser.add_argument("--timeout-sec", type=int, default=60, help="Command timeout per prompt")
    parser.add_argument("--bytes-per-token", type=int, default=DEFAULT_BYTES_PER_TOKEN)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    prompts = _load_prompts(Path(args.prompts))

    if args.runner == "command":
        if not args.normal_command or not args.caveman_command:
            raise SystemExit("runner=command requires --normal-command and --caveman-command")
        # Validate parse early for better errors.
        shlex.split(args.normal_command)
        shlex.split(args.caveman_command)

    normal_rows: list[dict[str, Any]] = []
    caveman_rows: list[dict[str, Any]] = []
    savings_rows: list[dict[str, Any]] = []

    normal_in = normal_out = caveman_in = caveman_out = 0

    for item in prompts:
        pid = item["id"]
        prompt = item["prompt"]

        if args.runner == "heuristic":
            normal_text = _heuristic_normal(prompt)
            caveman_text = _heuristic_caveman(prompt)
            normal_exit = caveman_exit = 0
            normal_err = caveman_err = ""
        else:
            normal_text, normal_exit, normal_err = _run_command(
                args.normal_command, prompt, args.normal_system, args.timeout_sec
            )
            caveman_text, caveman_exit, caveman_err = _run_command(
                args.caveman_command, prompt, args.caveman_system, args.timeout_sec
            )

        n = _estimate(prompt, normal_text, args.normal_system, args.bytes_per_token)
        c = _estimate(prompt, caveman_text, args.caveman_system, args.bytes_per_token)

        normal_in += n["input_tokens_estimated"]
        normal_out += n["output_tokens_estimated"]
        caveman_in += c["input_tokens_estimated"]
        caveman_out += c["output_tokens_estimated"]

        normal_rows.append(
            {
                "id": pid,
                "exit_code": normal_exit,
                "stderr": normal_err,
                "response_chars": len(normal_text),
                **n,
            }
        )
        caveman_rows.append(
            {
                "id": pid,
                "exit_code": caveman_exit,
                "stderr": caveman_err,
                "response_chars": len(caveman_text),
                **c,
            }
        )

        n_total = n["total_tokens_estimated"]
        c_total = c["total_tokens_estimated"]
        savings_rows.append(
            {
                "id": pid,
                "normal_total_tokens_estimated": n_total,
                "caveman_total_tokens_estimated": c_total,
                "total_tokens_saved": n_total - c_total,
                "total_percent_saved": percent_saved(n_total, c_total),
            }
        )

    normal_total = normal_in + normal_out
    caveman_total = caveman_in + caveman_out

    report: dict[str, Any] = {
        "schema_version": 1,
        "runner": args.runner,
        "token_source": "estimated",
        "estimation": {"bytes_per_token": args.bytes_per_token},
        "normal": {
            "system_prompt": args.normal_system,
            "totals": {
                "input_tokens_estimated": normal_in,
                "output_tokens_estimated": normal_out,
                "total_tokens_estimated": normal_total,
            },
            "prompts": normal_rows,
        },
        "caveman": {
            "system_prompt": args.caveman_system,
            "totals": {
                "input_tokens_estimated": caveman_in,
                "output_tokens_estimated": caveman_out,
                "total_tokens_estimated": caveman_total,
            },
            "prompts": caveman_rows,
        },
        "savings": {
            "input_tokens_saved": normal_in - caveman_in,
            "output_tokens_saved": normal_out - caveman_out,
            "total_tokens_saved": normal_total - caveman_total,
            "input_percent_saved": percent_saved(normal_in, caveman_in),
            "output_percent_saved": percent_saved(normal_out, caveman_out),
            "total_percent_saved": percent_saved(normal_total, caveman_total),
            "per_prompt": savings_rows,
        },
    }

    out_json = Path(args.out_json)
    out_report = Path(args.out_report)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2))
    out_report.write_text(_build_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
