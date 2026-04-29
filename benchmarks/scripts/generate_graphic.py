#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _fmt_int(value: int) -> str:
    return f"{value:,}"


def _bar_width(value: int, max_value: int, max_px: int) -> int:
    if max_value <= 0:
        return 0
    return int((value / max_value) * max_px)


def generate_svg(data: dict) -> str:
    baseline = data["overall"]["baseline"]
    stack = data["overall"]["stack"]
    savings = data["overall"]["savings"]

    baseline_total = int(baseline["total_tokens_estimated"])
    stack_total = int(stack["total_tokens_estimated"])
    saved_total = int(savings["total_tokens_saved"])
    saved_pct = float(savings["total_percent_saved"])
    output_saved = int(savings["output_tokens_saved"])

    max_total = max(baseline_total, stack_total)
    bar_max = 720
    base_w = _bar_width(baseline_total, max_total, bar_max)
    stack_w = _bar_width(stack_total, max_total, bar_max)

    return f"""<svg width="1200" height="627" viewBox="0 0 1200 627" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1200" y2="627" gradientUnits="userSpaceOnUse">
      <stop stop-color="#081220"/>
      <stop offset="0.55" stop-color="#0E1E38"/>
      <stop offset="1" stop-color="#0A2A44"/>
    </linearGradient>
    <linearGradient id="accent" x1="160" y1="0" x2="1040" y2="627" gradientUnits="userSpaceOnUse">
      <stop stop-color="#00E5A8"/>
      <stop offset="1" stop-color="#46C2FF"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="18" flood-color="#000000" flood-opacity="0.28"/>
    </filter>
  </defs>

  <rect width="1200" height="627" fill="url(#bg)"/>
  <circle cx="1120" cy="68" r="180" fill="#48BAFF" opacity="0.10"/>
  <circle cx="1090" cy="92" r="120" fill="#00E5A8" opacity="0.10"/>

  <rect x="56" y="46" width="1088" height="535" rx="26" fill="#0B1A30" stroke="#1D375A" stroke-width="1.5" filter="url(#soft)"/>

  <text x="96" y="98" fill="#D9F6FF" font-size="22" font-weight="600" font-family="SF Pro Display, Inter, Segoe UI, Arial">
    Zero-Bloat MCP Stack
  </text>
  <text x="96" y="180" fill="url(#accent)" font-size="92" font-weight="800" font-family="SF Pro Display, Inter, Segoe UI, Arial">
    {saved_pct:.2f}%
  </text>
  <text x="438" y="178" fill="#D9F6FF" font-size="46" font-weight="700" font-family="SF Pro Display, Inter, Segoe UI, Arial">
    fewer total tokens
  </text>
  <text x="96" y="222" fill="#9FC2DA" font-size="23" font-weight="500" font-family="SF Pro Display, Inter, Segoe UI, Arial">
    { _fmt_int(saved_total) } tokens saved overall • { _fmt_int(output_saved) } output tokens saved
  </text>

  <rect x="96" y="248" width="1008" height="1" fill="#244367"/>

  <text x="96" y="304" fill="#9FC2DA" font-size="22" font-weight="600" font-family="SF Pro Display, Inter, Segoe UI, Arial">Baseline</text>
  <rect x="220" y="280" width="{base_w}" height="36" rx="12" fill="#2F557D"/>
  <text x="{220 + base_w + 16}" y="305" fill="#D9F6FF" font-size="22" font-weight="700" font-family="SF Pro Display, Inter, Segoe UI, Arial">{_fmt_int(baseline_total)}</text>

  <text x="96" y="376" fill="#9FC2DA" font-size="22" font-weight="600" font-family="SF Pro Display, Inter, Segoe UI, Arial">Stack</text>
  <rect x="220" y="352" width="{stack_w}" height="36" rx="12" fill="url(#accent)"/>
  <text x="{220 + stack_w + 16}" y="377" fill="#D9F6FF" font-size="22" font-weight="700" font-family="SF Pro Display, Inter, Segoe UI, Arial">{_fmt_int(stack_total)}</text>

  <rect x="96" y="422" width="1008" height="1" fill="#244367"/>

  <rect x="96" y="444" width="315" height="104" rx="16" fill="#10233F" stroke="#244367"/>
  <text x="118" y="474" fill="#9FC2DA" font-size="18" font-family="SF Pro Display, Inter, Segoe UI, Arial">Input tokens</text>
  <text x="118" y="514" fill="#D9F6FF" font-size="34" font-weight="700" font-family="SF Pro Display, Inter, Segoe UI, Arial">
    {_fmt_int(int(savings["input_tokens_saved"]))}
  </text>

  <rect x="442" y="444" width="315" height="104" rx="16" fill="#10233F" stroke="#244367"/>
  <text x="464" y="474" fill="#9FC2DA" font-size="18" font-family="SF Pro Display, Inter, Segoe UI, Arial">Output tokens</text>
  <text x="464" y="514" fill="#D9F6FF" font-size="34" font-weight="700" font-family="SF Pro Display, Inter, Segoe UI, Arial">
    {_fmt_int(output_saved)}
  </text>

  <rect x="788" y="444" width="315" height="104" rx="16" fill="#10233F" stroke="#244367"/>
  <text x="810" y="474" fill="#9FC2DA" font-size="18" font-family="SF Pro Display, Inter, Segoe UI, Arial">Total saved</text>
  <text x="810" y="514" fill="#D9F6FF" font-size="34" font-weight="700" font-family="SF Pro Display, Inter, Segoe UI, Arial">
    {_fmt_int(saved_total)}
  </text>

  <text x="96" y="582" fill="#6F93B5" font-size="15" font-family="SF Pro Display, Inter, Segoe UI, Arial">
    Estimated tokens • Includes RTK CLI filtering + Caveman response compression
  </text>
</svg>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SVG graphic from full-stack benchmark results.")
    parser.add_argument("--input", default="benchmarks/results/full-stack.json", help="Input full-stack benchmark JSON")
    parser.add_argument(
        "--output", default="benchmarks/reports/token-savings-graphic.svg", help="Output SVG path"
    )
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    svg = generate_svg(data)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
