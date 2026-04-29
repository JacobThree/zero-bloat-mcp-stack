import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.scripts.generate_report import build_markdown  # noqa: E402
from benchmarks.scripts.token_counter import compare_runs  # noqa: E402


def test_generate_report_markdown_regression() -> None:
    baseline = {
        "mode": "baseline",
        "results": [
            {"id": "s1", "command": "echo hi", "combined_bytes": 40, "exit_code": 0, "timed_out": False},
            {"id": "s2", "command": "cat f", "combined_bytes": 20, "exit_code": 0, "timed_out": False},
        ],
    }
    stack = {
        "mode": "stack",
        "results": [
            {"id": "s1", "command": "echo hi", "combined_bytes": 20, "exit_code": 0, "timed_out": False},
            {"id": "s2", "command": "cat f", "combined_bytes": 12, "exit_code": 0, "timed_out": False},
        ],
    }

    report = compare_runs(baseline, stack, bytes_per_token=4)
    markdown = build_markdown(report)

    expected = textwrap.dedent(
        """\
        # Token Savings Report

        - Token source: `estimated`
        - Estimation ratio: `4 bytes/token`

        ## Totals

        | Metric | Baseline | Stack | Saved | Saved % |
        |---|---:|---:|---:|---:|
        | Input tokens | 4 | 4 | 0 | 0.0% |
        | Output tokens | 15 | 8 | 7 | 46.67% |
        | Total tokens | 19 | 12 | 7 | 36.84% |

        ## Baseline vs Stack (Estimated Tokens)

        ```mermaid
        xychart-beta
          title "Baseline vs Stack Token Comparison"
          x-axis ["Input","Output","Total"]
          y-axis "Tokens" 0 --> 21
          bar "Baseline" [4,15,19]
          bar "Stack" [4,8,12]
        ```

        ## Per-Scenario Breakdown

        | Scenario | Baseline Total | Stack Total | Saved | Saved % |
        |---|---:|---:|---:|---:|
        | `s1` | 12 | 7 | 5 | 41.67% |
        | `s2` | 7 | 5 | 2 | 28.57% |
        """
    )

    assert markdown == expected
