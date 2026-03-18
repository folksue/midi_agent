#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize benchmark summary_*.json and draw SVG bar charts.")
    p.add_argument("--results-root", default="benchmark/results")
    p.add_argument("--out-dir", default="")
    p.add_argument(
        "--exclude-model-regex",
        default="",
        help="Regex on model_dir to exclude, e.g. 'gemini'.",
    )
    p.add_argument(
        "--include-model-regex",
        default="",
        help="Regex on model_dir to include, e.g. 'openai_gpt-5-mini|qwen2.5_3b'.",
    )
    return p.parse_args()


def infer_run_dt(run_dir: str, path: Path) -> datetime:
    m = re.match(r"suite_(\d{8})_(\d{6})$", run_dir)
    if m:
        return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts)


def parse_summary_path(p: Path) -> dict[str, Any]:
    parts = p.parts
    # .../benchmark/results/<run_dir>/<provider>/<bench>/<model>/summary_*.json
    # legacy may be .../benchmark/results/<run_dir>/<bench>/<model>/summary_*.json
    try:
        i = parts.index("results")
    except ValueError:
        i = len(parts) - 5

    rel = list(parts[i + 1 :])
    run_dir = rel[0] if len(rel) > 0 else "unknown_run"

    provider = "unknown"
    bench = "unknown_bench"
    model_dir = "unknown_model"

    if len(rel) >= 5 and rel[1] in {"api", "ollama"}:
        provider = rel[1]
        bench = rel[2]
        model_dir = rel[3]
    elif len(rel) >= 4:
        bench = rel[1]
        model_dir = rel[2]
        # Heuristic from model folder naming.
        if model_dir.startswith("openai_") or model_dir.startswith("gemini_"):
            provider = "api"
        else:
            provider = "ollama"

    m = re.match(r"(?P<tok>.+)_(?P<group>label|sequence)_cases$", bench)
    tokenizer = m.group("tok") if m else "unknown"
    task_group = m.group("group") if m else "unknown"

    return {
        "run_dir": run_dir,
        "provider": provider,
        "bench": bench,
        "tokenizer": tokenizer,
        "task_group": task_group,
        "model_dir": model_dir,
        "path": str(p),
        "run_dt": infer_run_dt(run_dir, p),
    }


def load_rows(results_root: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fp in sorted(glob.glob(f"{results_root}/**/summary_*.json", recursive=True)):
        p = Path(fp)
        meta = parse_summary_path(p)
        d = json.loads(p.read_text(encoding="utf-8"))
        ov = d.get("overall", {})
        by_task_raw = d.get("by_task", {}) or {}
        by_task: dict[str, dict[str, Any]] = {}
        for task, st in by_task_raw.items():
            if not isinstance(st, dict):
                continue
            by_task[str(task)] = {
                "cases": int(st.get("cases", 0) or 0),
                "hit": int(st.get("hit", 0) or 0),
                "miss": int(st.get("miss", 0) or 0),
                "acc": float(st.get("acc", 0.0) or 0.0),
            }
        rows.append(
            {
                **meta,
                "cases": int(ov.get("cases", 0) or 0),
                "hit": int(ov.get("hit", 0) or 0),
                "miss": int(ov.get("miss", 0) or 0),
                "acc": float(ov.get("acc", 0.0) or 0.0),
                "by_task": by_task,
            }
        )
    return rows


def latest_by_key(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for r in rows:
        key = (r["provider"], r["model_dir"], r["tokenizer"], r["task_group"])
        old = by_key.get(key)
        if old is None or r["run_dt"] > old["run_dt"]:
            by_key[key] = r
    out = list(by_key.values())
    out.sort(key=lambda x: (x["provider"], x["model_dir"], x["task_group"], x["tokenizer"]))
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "run_dir",
        "provider",
        "model_dir",
        "tokenizer",
        "task_group",
        "bench",
        "cases",
        "hit",
        "miss",
        "acc",
        "path",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            rr = dict(r)
            rr.pop("run_dt", None)
            rr.pop("by_task", None)
            w.writerow(rr)


def draw_svg_bar_chart(path: Path, title: str, labels: list[str], values: list[float]) -> None:
    width = 1400
    height = 720
    margin_l = 80
    margin_r = 40
    margin_t = 80
    margin_b = 220
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    n = max(1, len(values))
    slot = plot_w / n
    bar_w = min(52, slot * 0.62)
    max_v = max(1.0, max(values) if values else 1.0)

    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append('<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>')
    parts.append(f'<text x="{margin_l}" y="40" font-size="24" font-family="Arial" fill="#111">{esc(title)}</text>')

    # grid + y ticks
    for i in range(6):
        yv = i * (max_v / 5)
        y = margin_t + plot_h - (yv / max_v) * plot_h
        parts.append(f'<line x1="{margin_l}" y1="{y:.1f}" x2="{width - margin_r}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        parts.append(f'<text x="{margin_l - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="12" font-family="Arial" fill="#555">{yv:.2f}</text>')

    # axes
    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + plot_h}" stroke="#333"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t + plot_h}" x2="{width - margin_r}" y2="{margin_t + plot_h}" stroke="#333"/>')

    for i, (label, v) in enumerate(zip(labels, values)):
        x_center = margin_l + slot * (i + 0.5)
        h = 0 if max_v <= 0 else (v / max_v) * plot_h
        y = margin_t + plot_h - h
        x = x_center - bar_w / 2
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="#2b7fff"/>')
        parts.append(f'<text x="{x_center:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-size="11" font-family="Arial" fill="#222">{v:.3f}</text>')
        # rotated x labels
        lx = x_center
        ly = margin_t + plot_h + 14
        parts.append(
            f'<g transform="translate({lx:.1f},{ly:.1f}) rotate(45)">'
            f'<text font-size="11" font-family="Arial" fill="#333">{esc(label)}</text></g>'
        )

    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def write_markdown(path: Path, latest_rows: list[dict[str, Any]], model_avg: list[dict[str, Any]]) -> None:
    lines = [
        "# Benchmark Summary",
        "",
        "## Latest per (provider, model, tokenizer, task_group)",
        "",
        "| provider | model | tokenizer | task_group | cases | hit | miss | acc | run_dir |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in latest_rows:
        lines.append(
            f"| {r['provider']} | {r['model_dir']} | {r['tokenizer']} | {r['task_group']} | {r['cases']} | {r['hit']} | {r['miss']} | {r['acc']:.3f} | {r['run_dir']} |"
        )
    lines.extend(
        [
            "",
            "## Model Weighted Mean Accuracy (latest rows)",
            "",
            "| model | provider | total_cases | total_hit | weighted_acc |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for r in model_avg:
        lines.append(
            f"| {r['model_dir']} | {r['provider']} | {r['total_cases']} | {r['total_hit']} | {r['weighted_acc']:.3f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_task_model_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["model_dir", "provider", "task", "cases", "hit", "miss", "acc"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    args = parse_args()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir) if args.out_dir else Path(args.results_root) / f"analysis_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(args.results_root)
    if not rows:
        print("No summary_*.json found.")
        return 1

    if args.exclude_model_regex:
        rx = re.compile(args.exclude_model_regex)
        rows = [r for r in rows if not rx.search(str(r.get("model_dir", "")))]
        if not rows:
            print("No rows left after model exclusion filter.")
            return 1
    if args.include_model_regex:
        rx = re.compile(args.include_model_regex)
        rows = [r for r in rows if rx.search(str(r.get("model_dir", "")))]
        if not rows:
            print("No rows left after model inclusion filter.")
            return 1

    latest_rows = latest_by_key(rows)

    write_csv(out_dir / "summary_all_rows.csv", rows)
    write_csv(out_dir / "summary_latest_rows.csv", latest_rows)

    # Chart 1: latest rows by benchmark key
    latest_rows_sorted = sorted(latest_rows, key=lambda x: x["acc"], reverse=True)
    labels = [f"{r['model_dir']} | {r['tokenizer']}_{r['task_group']}" for r in latest_rows_sorted]
    values = [r["acc"] for r in latest_rows_sorted]
    draw_svg_bar_chart(
        out_dir / "bar_acc_latest_rows.svg",
        "Accuracy by model/tokenizer/task_group (latest rows)",
        labels,
        values,
    )

    # Chart 2: weighted mean acc by model across latest rows
    bucket: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"total_cases": 0, "total_hit": 0})
    for r in latest_rows:
        k = (r["provider"], r["model_dir"])
        bucket[k]["total_cases"] += r["cases"]
        bucket[k]["total_hit"] += r["hit"]

    model_avg: list[dict[str, Any]] = []
    for (provider, model_dir), s in bucket.items():
        tc = int(s["total_cases"])
        th = int(s["total_hit"])
        wa = (th / tc) if tc > 0 else 0.0
        model_avg.append(
            {
                "provider": provider,
                "model_dir": model_dir,
                "total_cases": tc,
                "total_hit": th,
                "weighted_acc": wa,
            }
        )
    model_avg.sort(key=lambda x: x["weighted_acc"], reverse=True)

    draw_svg_bar_chart(
        out_dir / "bar_acc_model_weighted.svg",
        "Weighted mean accuracy by model (latest rows)",
        [f"{r['provider']}:{r['model_dir']}" for r in model_avg],
        [r["weighted_acc"] for r in model_avg],
    )

    # Chart 3: weighted mean acc by task across latest rows
    task_bucket: dict[str, dict[str, int]] = defaultdict(lambda: {"cases": 0, "hit": 0})
    for r in latest_rows:
        by_task = r.get("by_task", {}) or {}
        for task, st in by_task.items():
            task_bucket[task]["cases"] += int(st.get("cases", 0) or 0)
            task_bucket[task]["hit"] += int(st.get("hit", 0) or 0)
    task_rows: list[dict[str, Any]] = []
    for task, s in sorted(task_bucket.items()):
        tc = int(s["cases"])
        th = int(s["hit"])
        task_rows.append({"task": task, "cases": tc, "hit": th, "acc": (th / tc) if tc > 0 else 0.0})
    draw_svg_bar_chart(
        out_dir / "bar_acc_by_task.svg",
        "Weighted mean accuracy by task (latest rows)",
        [x["task"] for x in task_rows],
        [x["acc"] for x in task_rows],
    )

    # Chart 4 + CSV: direct task accuracy per model (no cross-task averaging)
    task_model_bucket: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: {"cases": 0, "hit": 0})
    for r in latest_rows:
        model = str(r.get("model_dir", "unknown"))
        provider = str(r.get("provider", "unknown"))
        for task, st in (r.get("by_task", {}) or {}).items():
            k = (provider, model, str(task))
            task_model_bucket[k]["cases"] += int(st.get("cases", 0) or 0)
            task_model_bucket[k]["hit"] += int(st.get("hit", 0) or 0)
    task_model_rows: list[dict[str, Any]] = []
    for (provider, model, task), s in sorted(task_model_bucket.items(), key=lambda x: (x[0][1], x[0][2])):
        tc = int(s["cases"])
        th = int(s["hit"])
        task_model_rows.append(
            {
                "model_dir": model,
                "provider": provider,
                "task": task,
                "cases": tc,
                "hit": th,
                "miss": tc - th,
                "acc": (th / tc) if tc > 0 else 0.0,
            }
        )
    write_task_model_csv(out_dir / "task_acc_by_model.csv", task_model_rows)
    draw_svg_bar_chart(
        out_dir / "bar_acc_task_model.svg",
        "Task accuracy by model (latest rows)",
        [f"{x['model_dir']} | {x['task']}" for x in task_model_rows],
        [float(x["acc"]) for x in task_model_rows],
    )

    write_markdown(out_dir / "SUMMARY.md", latest_rows_sorted, model_avg)

    print(f"wrote: {out_dir / 'summary_all_rows.csv'}")
    print(f"wrote: {out_dir / 'summary_latest_rows.csv'}")
    print(f"wrote: {out_dir / 'bar_acc_latest_rows.svg'}")
    print(f"wrote: {out_dir / 'bar_acc_model_weighted.svg'}")
    print(f"wrote: {out_dir / 'bar_acc_by_task.svg'}")
    print(f"wrote: {out_dir / 'task_acc_by_model.csv'}")
    print(f"wrote: {out_dir / 'bar_acc_task_model.svg'}")
    print(f"wrote: {out_dir / 'SUMMARY.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
