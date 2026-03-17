#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.core.predictions import get_prediction_label, get_prediction_notes
from benchmark.core.task_specs import LABEL_TASKS, SEQUENCE_TASKS, TASK_GROUPS, label_space_for_task
from benchmark.tokenizers import decode_melody_by_tokenizer

MISSING_LABEL = "__missing_prediction__"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate benchmark predictions for Tasks 1-8.")
    p.add_argument("--gold", required=True, help="Benchmark jsonl view file.")
    p.add_argument("--pred", required=True, help="Prediction jsonl file.")
    p.add_argument("--out", default="benchmark/results/eval_predictions.json")
    p.add_argument("--overall-out", default="", help="Optional output path for overall-only JSON.")
    p.add_argument("--by-task-out", default="", help="Optional output path for task summary JSON.")
    p.add_argument("--by-tokenizer-out", default="", help="Optional output path for tokenizer summary JSON.")
    p.add_argument("--tokenizer", default="", help="Override tokenizer if gold.meta.tokenizer is missing.")
    p.add_argument("--task-group", choices=sorted(TASK_GROUPS.keys()), default="all")
    p.add_argument("--tasks", default="", help="Comma-separated task ids; overrides --task-group.")
    return p.parse_args()


def _load_jsonl(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def _tol_eq(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) <= eps


def _seq_exact(a: list[dict], b: list[dict]) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if int(x["p"]) != int(y["p"]):
            return False
        if not _tol_eq(float(x.get("t", 0.0)), float(y.get("t", 0.0))):
            return False
        if not _tol_eq(float(x["d"]), float(y["d"])):
            return False
    return True


def _pitch_accuracy(pred: list[dict], ref: list[dict]) -> float:
    if not ref:
        return 1.0 if not pred else 0.0
    ok = 0
    for i, r in enumerate(ref):
        if i < len(pred) and int(pred[i]["p"]) == int(r["p"]):
            ok += 1
    return ok / len(ref)


def _duration_accuracy(pred: list[dict], ref: list[dict]) -> float:
    if not ref:
        return 1.0 if not pred else 0.0
    ok = 0
    for i, r in enumerate(ref):
        if i < len(pred) and _tol_eq(float(pred[i]["d"]), float(r["d"])):
            ok += 1
    return ok / len(ref)


def _timing_accuracy(pred: list[dict], ref: list[dict]) -> float:
    if not ref:
        return 1.0 if not pred else 0.0
    ok = 0
    for i, r in enumerate(ref):
        if i < len(pred) and _tol_eq(float(pred[i].get("t", 0.0)), float(r.get("t", 0.0))):
            ok += 1
    return ok / len(ref)


def _intervals(seq: list[dict]) -> list[int]:
    return [int(seq[i + 1]["p"]) - int(seq[i]["p"]) for i in range(len(seq) - 1)]


def _interval_preservation_rate(pred: list[dict], src: list[dict]) -> float:
    src_i = _intervals(src)
    if not src_i:
        return 1.0
    pred_i = _intervals(pred)
    ok = 0
    for i, x in enumerate(src_i):
        if i < len(pred_i) and pred_i[i] == x:
            ok += 1
    return ok / len(src_i)


def _rhythm_preservation_rate(pred: list[dict], src: list[dict]) -> float:
    if not src:
        return 1.0 if not pred else 0.0
    ok = 0
    for i, s in enumerate(src):
        if i < len(pred) and _tol_eq(float(pred[i]["d"]), float(s["d"])):
            ok += 1
    return ok / len(src)


def _bar_valid(pred: list[dict]) -> bool:
    step = 0.125
    for n in pred:
        d = float(n["d"])
        if d <= 0:
            return False
        q = round(d / step)
        if not _tol_eq(q * step, d, eps=1e-6):
            return False
    return True


def _macro_f1(refs: list[str], preds: list[str], labels: list[str]) -> float:
    if not refs:
        return 0.0
    scores: list[float] = []
    for label in labels:
        tp = fp = fn = 0
        for ref, pred in zip(refs, preds):
            if pred == label and ref == label:
                tp += 1
            elif pred == label and ref != label:
                fp += 1
            elif pred != label and ref == label:
                fn += 1
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        if precision + recall == 0:
            scores.append(0.0)
        else:
            scores.append((2 * precision * recall) / (precision + recall))
    return sum(scores) / len(scores) if scores else 0.0


def _target_label(gold_row: dict) -> str:
    target_payload = gold_row.get("target_payload")
    if isinstance(target_payload, dict) and "label" in target_payload:
        return str(target_payload["label"]).strip()
    if isinstance(target_payload, str):
        return target_payload.strip()
    return str(gold_row.get("ground_truth", gold_row.get("target", ""))).strip()


def _target_notes(gold_row: dict, tokenizer: str) -> list[dict]:
    target_payload = gold_row.get("target_payload")
    if isinstance(target_payload, list):
        return target_payload
    if isinstance(target_payload, dict) and isinstance(target_payload.get("notes"), list):
        return target_payload["notes"]
    target_text = str(gold_row.get("ground_truth", gold_row.get("target", "")))
    return decode_melody_by_tokenizer(tokenizer, target_text)


def _init_task_stats(task: str) -> dict:
    base = {
        "n": 0,
        "missing": 0,
        "hit": 0,
    }
    if task in LABEL_TASKS:
        base["ref_labels"] = []
        base["pred_labels"] = []
    else:
        base.update(
            {
                "pitch_acc_sum": 0.0,
                "duration_acc_sum": 0.0,
                "timing_acc_sum": 0.0,
                "interval_preserve_sum": 0.0,
                "rhythm_preserve_sum": 0.0,
                "bar_valid_sum": 0.0,
                "decode_error_count": 0,
            }
        )
    return base


def _finalize_task(task: str, stats: dict) -> dict:
    n = stats["n"] or 1
    out = {
        "n": stats["n"],
        "missing": stats["missing"],
        "accuracy": stats["hit"] / n,
        "exact_match": stats["hit"] / n,
    }
    if task in LABEL_TASKS:
        labels = label_space_for_task(task)
        observed = set(stats["ref_labels"])
        observed.update(x for x in stats["pred_labels"] if x != MISSING_LABEL)
        if not labels:
            labels = sorted(observed)
        if task in {"task3_harmonic_function", "task8_voice_leading"}:
            out["macro_f1"] = _macro_f1(stats["ref_labels"], stats["pred_labels"], labels)
        out["label_space"] = labels
        return out

    out.update(
        {
            "pitch_accuracy": stats["pitch_acc_sum"] / n,
            "duration_accuracy": stats["duration_acc_sum"] / n,
            "timing_accuracy": stats["timing_acc_sum"] / n,
            "decode_error_count": stats["decode_error_count"],
        }
    )
    if task == "task4_transposition":
        out["interval_preservation_rate"] = stats["interval_preserve_sum"] / n
        out["rhythm_preservation_rate"] = stats["rhythm_preserve_sum"] / n
    if task == "task7_rhythm_scale":
        out["bar_validity_rate"] = stats["bar_valid_sum"] / n
    return out


def main() -> int:
    args = parse_args()

    gold_rows = _load_jsonl(args.gold)
    pred_rows = _load_jsonl(args.pred)
    selected_tasks = {t.strip() for t in args.tasks.split(",") if t.strip()} or set(TASK_GROUPS[args.task_group])

    pred_map = {
        str(r.get("case_id") or r.get("id") or ""): r
        for r in pred_rows
        if (r.get("case_id") or r.get("id"))
    }

    per_task = {task: _init_task_stats(task) for task in sorted(selected_tasks)}
    per_tokenizer: dict[str, dict] = {}

    total = 0
    total_missing = 0
    total_hit = 0

    for gold_row in gold_rows:
        task = str(gold_row.get("task", ""))
        if task not in selected_tasks:
            continue
        total += 1
        tokenizer = args.tokenizer or gold_row.get("meta", {}).get("tokenizer") or "note_level"
        tok_stats = per_tokenizer.setdefault(tokenizer, {"n": 0, "missing": 0, "hit": 0})
        tok_stats["n"] += 1

        task_stats = per_task[task]
        task_stats["n"] += 1

        rid = str(gold_row.get("id", ""))
        pred_row = pred_map.get(rid)
        if not pred_row:
            task_stats["missing"] += 1
            tok_stats["missing"] += 1
            total_missing += 1
            if task in LABEL_TASKS:
                task_stats["ref_labels"].append(_target_label(gold_row))
                task_stats["pred_labels"].append(MISSING_LABEL)
            continue

        if task in LABEL_TASKS:
            ref_label = _target_label(gold_row)
            pred_label = get_prediction_label(pred_row, task) or MISSING_LABEL
            task_stats["ref_labels"].append(ref_label)
            task_stats["pred_labels"].append(pred_label)
            hit = int(pred_label == ref_label)
            task_stats["hit"] += hit
            tok_stats["hit"] += hit
            total_hit += hit
            continue

        ref_notes = _target_notes(gold_row, tokenizer)
        try:
            pred_notes = get_prediction_notes(pred_row, task, tokenizer)
        except Exception:
            pred_notes = []
            task_stats["decode_error_count"] += 1

        hit = int(_seq_exact(pred_notes, ref_notes))
        task_stats["hit"] += hit
        task_stats["pitch_acc_sum"] += _pitch_accuracy(pred_notes, ref_notes)
        task_stats["duration_acc_sum"] += _duration_accuracy(pred_notes, ref_notes)
        task_stats["timing_acc_sum"] += _timing_accuracy(pred_notes, ref_notes)

        src_notes = gold_row.get("payload", {}).get("melody", [])
        if task == "task4_transposition":
            task_stats["interval_preserve_sum"] += _interval_preservation_rate(pred_notes, src_notes)
            task_stats["rhythm_preserve_sum"] += _rhythm_preservation_rate(pred_notes, src_notes)
        if task == "task7_rhythm_scale":
            task_stats["bar_valid_sum"] += float(_bar_valid(pred_notes))

        tok_stats["hit"] += hit
        total_hit += hit

    overall = {
        "cases": total,
        "missing": total_missing,
        "hit": total_hit,
        "accuracy": (total_hit / total) if total else 0.0,
    }
    by_task = {task: _finalize_task(task, per_task[task]) for task in sorted(per_task)}
    by_tokenizer = {
        tokenizer: {
            "cases": stats["n"],
            "missing": stats["missing"],
            "hit": stats["hit"],
            "accuracy": (stats["hit"] / stats["n"]) if stats["n"] else 0.0,
        }
        for tokenizer, stats in sorted(per_tokenizer.items())
    }

    result = {
        "gold": args.gold,
        "pred": args.pred,
        "overall": overall,
        "by_task": by_task,
        "by_tokenizer": by_tokenizer,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.overall_out:
        p = Path(args.overall_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(overall, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.by_task_out:
        p = Path(args.by_task_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(by_task, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.by_tokenizer_out:
        p = Path(args.by_tokenizer_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(by_tokenizer, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote: {out_path}")
    print(json.dumps(overall, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
