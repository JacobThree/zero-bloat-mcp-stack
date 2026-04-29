#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash benchmarks/run_benchmark.sh --mode <baseline|stack> --out <output-json> [--scenarios <path>]

Required:
  --mode       baseline | stack
  --out        output JSON file path

Optional:
  --scenarios  scenario manifest path (default: benchmarks/scenarios/scenarios.json)
EOF
}

MODE=""
OUT=""
SCENARIOS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      [[ $# -ge 2 ]] || { echo "Missing value for --mode" >&2; usage; exit 2; }
      MODE="$2"
      shift 2
      ;;
    --out)
      [[ $# -ge 2 ]] || { echo "Missing value for --out" >&2; usage; exit 2; }
      OUT="$2"
      shift 2
      ;;
    --scenarios)
      [[ $# -ge 2 ]] || { echo "Missing value for --scenarios" >&2; usage; exit 2; }
      SCENARIOS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$MODE" || -z "$OUT" ]]; then
  echo "Both --mode and --out are required." >&2
  usage
  exit 2
fi

if [[ "$MODE" != "baseline" && "$MODE" != "stack" ]]; then
  echo "Invalid --mode: $MODE (expected baseline or stack)" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -z "$SCENARIOS" ]]; then
  SCENARIOS="$SCRIPT_DIR/scenarios/scenarios.json"
fi

if [[ ! -f "$SCENARIOS" ]]; then
  echo "Scenario file not found: $SCENARIOS" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

python - "$MODE" "$OUT" "$SCENARIOS" "$ROOT_DIR" <<'PY'
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def iso_now(ms: float) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


mode, out_path, scenario_path, root_dir = sys.argv[1:]
scenario_file = Path(scenario_path)
out_file = Path(out_path)

data = json.loads(scenario_file.read_text())
scenarios = data.get("scenarios")
if not isinstance(scenarios, list):
    raise SystemExit("Invalid scenario manifest: key 'scenarios' must be a list")

if mode == "stack" and shutil.which("rtk") is None:
    raise SystemExit("Stack mode requires 'rtk' in PATH")

results = []

for idx, scenario in enumerate(scenarios):
    if not isinstance(scenario, dict):
        raise SystemExit(f"Scenario #{idx + 1} invalid: expected object")
    missing = [k for k in ("id", "timeout_sec") if k not in scenario]
    if missing:
        raise SystemExit(f"Scenario #{idx + 1} missing required keys: {', '.join(missing)}")

    scenario_id = str(scenario["id"])
    command_default = scenario.get("command")
    command_baseline = scenario.get("baseline_command")
    command_stack = scenario.get("stack_command")

    if mode == "baseline":
        command = command_baseline if command_baseline is not None else command_default
    else:
        command = command_stack if command_stack is not None else command_default

    if command is None:
        raise SystemExit(
            f"Scenario '{scenario_id}' missing executable command for mode '{mode}'. "
            "Provide 'command' or mode-specific command fields."
        )

    command = str(command)
    timeout_sec = int(scenario["timeout_sec"])

    started_ms = time.time() * 1000
    timed_out = False
    exit_code = 0
    stdout = b""
    stderr = b""

    if mode == "baseline":
        cmd = ["bash", "-lc", command]
    else:
        # Use RTK specialized wrappers/filters via mode-specific scenario commands.
        # Fallback still runs through rtk shell wrapper when only generic command exists.
        if command_stack is not None:
            cmd = ["bash", "-lc", command]
        else:
            cmd = ["rtk", "bash", "-lc", command]

    try:
        completed = subprocess.run(
            cmd,
            cwd=root_dir,
            capture_output=True,
            timeout=timeout_sec,
            check=False,
        )
        exit_code = int(completed.returncode)
        stdout = completed.stdout or b""
        stderr = completed.stderr or b""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""

    finished_ms = time.time() * 1000

    results.append(
        {
            "id": scenario_id,
            "command": command_default,
            "executed_command": command,
            "timeout_sec": timeout_sec,
            "started_at": iso_now(started_ms),
            "finished_at": iso_now(finished_ms),
            "duration_ms": int(finished_ms - started_ms),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
            "combined_bytes": len(stdout) + len(stderr),
        }
    )

summary = {
    "total_scenarios": len(results),
    "failed_scenarios": sum(1 for r in results if r["exit_code"] != 0),
    "timed_out_scenarios": sum(1 for r in results if r["timed_out"]),
    "total_stdout_bytes": sum(r["stdout_bytes"] for r in results),
    "total_stderr_bytes": sum(r["stderr_bytes"] for r in results),
    "total_combined_bytes": sum(r["combined_bytes"] for r in results),
}

doc = {
    "schema_version": 1,
    "mode": mode,
    "scenario_file": str(scenario_file),
    "generated_at": iso_now(time.time() * 1000),
    "summary": summary,
    "results": results,
}

out_file.write_text(json.dumps(doc, indent=2))
PY
