#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _fmt_int(value: int) -> str:
    return f"{value:,}"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Allow explicit override for reproducible rendering in CI or non-standard hosts.
    env_key = "GRAPHIC_BOLD_FONT_PATH" if bold else "GRAPHIC_FONT_PATH"
    candidates = [os.environ[env_key]] if os.environ.get(env_key) else []

    # Common macOS + Linux font paths.
    if bold:
        candidates += [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ]
    candidates += [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient_bg(width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height))
    px = img.load()
    top = (8, 18, 32)
    mid = (14, 30, 56)
    bot = (10, 42, 68)
    for y in range(height):
        t = y / max(height - 1, 1)
        if t < 0.55:
            k = t / 0.55
            r = int(top[0] + (mid[0] - top[0]) * k)
            g = int(top[1] + (mid[1] - top[1]) * k)
            b = int(top[2] + (mid[2] - top[2]) * k)
        else:
            k = (t - 0.55) / 0.45
            r = int(mid[0] + (bot[0] - mid[0]) * k)
            g = int(mid[1] + (bot[1] - mid[1]) * k)
            b = int(mid[2] + (bot[2] - mid[2]) * k)
        for x in range(width):
            px[x, y] = (r, g, b)
    return img


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], r: int, fill, outline=None, w=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


def generate_png(data: dict, out_path: Path) -> None:
    width, height = 1200, 627
    baseline = data["overall"]["baseline"]
    stack = data["overall"]["stack"]
    savings = data["overall"]["savings"]

    baseline_total = int(baseline["total_tokens_estimated"])
    stack_total = int(stack["total_tokens_estimated"])
    saved_total = int(savings["total_tokens_saved"])
    saved_pct = float(savings["total_percent_saved"])
    output_saved = int(savings["output_tokens_saved"])
    input_saved = int(savings["input_tokens_saved"])

    img = _gradient_bg(width, height)
    draw = ImageDraw.Draw(img)

    panel = (56, 46, 1144, 581)
    _rounded_rect(draw, panel, r=26, fill=(11, 26, 48), outline=(29, 55, 90), w=2)

    font_title = _load_font(22, bold=True)
    font_big = _load_font(92, bold=True)
    font_label = _load_font(46, bold=True)
    font_sub = _load_font(23, bold=False)
    font_mid = _load_font(22, bold=True)
    font_card_label = _load_font(18, bold=False)
    font_card_value = _load_font(34, bold=True)
    font_foot = _load_font(15, bold=False)

    draw.text((96, 76), "Zero-Bloat MCP Stack", fill=(217, 246, 255), font=font_title)
    draw.text((96, 112), f"{saved_pct:.2f}%", fill=(70, 194, 255), font=font_big)
    draw.text((460, 128), "fewer total tokens", fill=(217, 246, 255), font=font_label)
    draw.text(
        (96, 206),
        f"{_fmt_int(saved_total)} tokens saved overall • {_fmt_int(output_saved)} output tokens saved",
        fill=(159, 194, 218),
        font=font_sub,
    )

    draw.line((96, 248, 1104, 248), fill=(36, 67, 103), width=1)

    max_total = max(baseline_total, stack_total, 1)
    bar_max = 720
    base_w = int((baseline_total / max_total) * bar_max)
    stack_w = int((stack_total / max_total) * bar_max)

    draw.text((96, 282), "Baseline", fill=(159, 194, 218), font=font_mid)
    _rounded_rect(draw, (220, 280, 220 + base_w, 316), r=12, fill=(47, 85, 125))
    draw.text((220 + base_w + 16, 282), _fmt_int(baseline_total), fill=(217, 246, 255), font=font_mid)

    draw.text((96, 354), "Stack", fill=(159, 194, 218), font=font_mid)
    _rounded_rect(draw, (220, 352, 220 + stack_w, 388), r=12, fill=(0, 229, 168))
    draw.text((220 + stack_w + 16, 354), _fmt_int(stack_total), fill=(217, 246, 255), font=font_mid)

    draw.line((96, 422, 1104, 422), fill=(36, 67, 103), width=1)

    cards = [
        (96, 444, 411, 548, "Input tokens", _fmt_int(input_saved)),
        (442, 444, 757, 548, "Output tokens", _fmt_int(output_saved)),
        (788, 444, 1103, 548, "Total saved", _fmt_int(saved_total)),
    ]
    for x1, y1, x2, y2, label, value in cards:
        _rounded_rect(draw, (x1, y1, x2, y2), r=16, fill=(16, 35, 63), outline=(36, 67, 103), w=1)
        draw.text((x1 + 22, y1 + 20), label, fill=(159, 194, 218), font=font_card_label)
        draw.text((x1 + 22, y1 + 52), value, fill=(217, 246, 255), font=font_card_value)

    draw.text(
        (96, 582),
        "Estimated tokens • Includes RTK CLI filtering + Caveman response compression",
        fill=(111, 147, 181),
        font=font_foot,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate PNG graphic directly from full-stack benchmark results.")
    parser.add_argument("--input", default="benchmarks/results/full-stack.json")
    parser.add_argument("--output", default="benchmarks/reports/token-savings-graphic.png")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    generate_png(data, Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
