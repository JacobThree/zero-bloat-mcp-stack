import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.scripts.token_counter import (  # noqa: E402
    aggregate_run,
    compare_runs,
    estimate_tokens_from_bytes,
    percent_saved,
)


def test_estimate_tokens_from_bytes_rounding() -> None:
    assert estimate_tokens_from_bytes(0) == 0
    assert estimate_tokens_from_bytes(1) == 1
    assert estimate_tokens_from_bytes(4) == 1
    assert estimate_tokens_from_bytes(5) == 2
    assert estimate_tokens_from_bytes(15, bytes_per_token=5) == 3


def test_percent_saved() -> None:
    assert percent_saved(100, 70) == 30.0
    assert percent_saved(0, 0) == 0.0
    assert percent_saved(0, 5) == 0.0


def test_aggregate_run_totals() -> None:
    run_doc = {
        "mode": "baseline",
        "results": [
            {
                "id": "s1",
                "command": "echo hello",
                "stdout_bytes": 40,
                "stderr_bytes": 0,
                "combined_bytes": 40,
                "exit_code": 0,
                "timed_out": False,
            },
            {
                "id": "s2",
                "command": "cat README.md",
                "stdout_bytes": 16,
                "stderr_bytes": 8,
                "combined_bytes": 24,
                "exit_code": 0,
                "timed_out": False,
            },
        ],
    }
    agg = aggregate_run(run_doc, bytes_per_token=4)

    assert agg["token_source"] == "estimated"
    assert agg["totals"]["input_tokens_estimated"] == 6
    assert agg["totals"]["output_tokens_estimated"] == 16
    assert agg["totals"]["total_tokens_estimated"] == 22
    assert len(agg["scenarios"]) == 2


def test_compare_runs_savings_math() -> None:
    baseline = {
        "mode": "baseline",
        "results": [
            {"id": "s1", "command": "abc", "combined_bytes": 40, "exit_code": 0, "timed_out": False},
            {"id": "s2", "command": "abcdef", "combined_bytes": 20, "exit_code": 0, "timed_out": False},
        ],
    }
    stack = {
        "mode": "stack",
        "results": [
            {"id": "s1", "command": "abc", "combined_bytes": 20, "exit_code": 0, "timed_out": False},
            {"id": "s2", "command": "abcdef", "combined_bytes": 12, "exit_code": 0, "timed_out": False},
        ],
    }
    report = compare_runs(baseline, stack, bytes_per_token=4)

    assert report["token_source"] == "estimated"
    assert report["savings"]["output_tokens_saved"] == 7
    assert report["savings"]["total_tokens_saved"] == 7
    assert report["savings"]["total_percent_saved"] == 38.89
    assert len(report["savings"]["per_scenario"]) == 2
