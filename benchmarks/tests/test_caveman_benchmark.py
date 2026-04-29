import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.scripts.caveman_benchmark import _heuristic_caveman, _heuristic_normal  # noqa: E402


def test_heuristic_caveman_shorter_than_normal() -> None:
    prompt = "Explain why the API request is failing and how to fix it quickly."
    normal = _heuristic_normal(prompt)
    caveman = _heuristic_caveman(prompt)
    assert len(caveman) < len(normal)


def test_heuristic_caveman_removes_common_stopwords() -> None:
    prompt = "This is a test of the emergency broadcast system."
    caveman = _heuristic_caveman(prompt).lower()
    assert " the " not in f" {caveman} "
