#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot grouped task-accuracy bars (SVG) from task_acc_by_model CSV.")
    p.add_argument("--csv", required=True, help="Input CSV with columns: model_dir,task,acc")
    p.add_argument("--out", required=True, help="Output SVG path")
    p.add_argument("--title", default="Task Accuracy by Model")
    return p.parse_args()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main() -> int:
    args = parse_args()
    rows = []
    with open(args.csv, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    if not rows:
        raise SystemExit("empty csv")

    tasks = sorted({str(r["task"]) for r in rows})
    models = sorted({str(r["model_dir"]) for r in rows})

    by = {(str(r["task"]), str(r["model_dir"])): float(r.get("acc", 0) or 0) for r in rows}

    palette = ["#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#7c3aed", "#0f766e", "#ea580c"]
    color = {m: palette[i % len(palette)] for i, m in enumerate(models)}

    width = 1600
    height = 900
    margin_l = 90
    margin_r = 30
    margin_t = 90
    margin_b = 260
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    group_n = max(1, len(tasks))
    group_slot = plot_w / group_n
    inner_w = group_slot * 0.76
    bar_w = max(8, min(30, inner_w / max(1, len(models)) - 4))

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append('<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>')
    parts.append(f'<text x="{margin_l}" y="42" font-size="28" font-family="Arial" fill="#111">{esc(args.title)}</text>')

    # y-grid and labels 0..1
    for i in range(6):
        yv = i / 5
        y = margin_t + plot_h - yv * plot_h
        parts.append(f'<line x1="{margin_l}" y1="{y:.1f}" x2="{width - margin_r}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{margin_l - 12}" y="{y + 4:.1f}" text-anchor="end" font-size="12" font-family="Arial" fill="#4b5563">{yv:.1f}</text>')

    # axes
    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + plot_h}" stroke="#111827"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t + plot_h}" x2="{width - margin_r}" y2="{margin_t + plot_h}" stroke="#111827"/>')

    # bars
    for gi, task in enumerate(tasks):
        gx = margin_l + gi * group_slot + (group_slot - inner_w) / 2
        for mi, model in enumerate(models):
            v = max(0.0, min(1.0, by.get((task, model), 0.0)))
            h = v * plot_h
            draw_h = h if h > 0 else 1.2
            x = gx + mi * (bar_w + 4)
            y = margin_t + plot_h - draw_h
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{draw_h:.1f}" '
                f'fill="{color[model]}" stroke="#1f2937" stroke-width="0.3"/>'
            )
        # task label
        tx = margin_l + gi * group_slot + group_slot / 2
        ty = margin_t + plot_h + 18
        parts.append(f'<g transform="translate({tx:.1f},{ty:.1f}) rotate(35)"><text font-size="12" font-family="Arial" fill="#111827">{esc(task)}</text></g>')

    # legend
    lx = margin_l
    ly = height - 130
    parts.append(f'<text x="{lx}" y="{ly - 12}" font-size="14" font-family="Arial" fill="#111827">Legend</text>')
    for i, model in enumerate(models):
        x = lx + (i % 3) * 420
        y = ly + (i // 3) * 26
        parts.append(f'<rect x="{x}" y="{y - 11}" width="16" height="16" fill="{color[model]}"/>')
        parts.append(f'<text x="{x + 24}" y="{y + 2}" font-size="13" font-family="Arial" fill="#111827">{esc(model)}</text>')

    parts.append('</svg>')
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
