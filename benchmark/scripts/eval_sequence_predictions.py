#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.core.predictions import get_prediction_notes
from benchmark.core.task_specs import SEQUENCE_TASKS
from benchmark.tokenizers import decode_melody_by_tokenizer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate Note Sequence Transformation tasks (Task 4-7).")
    p.add_argument("--gold", required=True, help="Benchmark jsonl view file (note_level/midilike/remilike).")
    p.add_argument("--pred", required=True, help="Prediction jsonl. Each line: {id, prediction}.")
    p.add_argument("--out", default="benchmark/results/sequence_eval.json")
    p.add_argument("--tokenizer", default="", help="Override tokenizer if gold.meta.tokenizer missing.")
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
    # V1: duration must be >0 and align to 1/8-beat (0.125) grid.
    step = 0.125
    for n in pred:
        d = float(n["d"])
        if d <= 0:
            return False
        q = round(d / step)
        if not _tol_eq(q * step, d, eps=1e-6):
            return False
    return True

def main() -> int:
    args = parse_args()

    gold_rows = _load_jsonl(args.gold)
    pred_rows = _load_jsonl(args.pred)

    pred_map = {str(r.get("id", "")): r for r in pred_rows if r.get("id")}

    per_task = {
        t: {
            "n": 0,
            "missing": 0,
            "exact_match": 0,
            "pitch_acc_sum": 0.0,
            "duration_acc_sum": 0.0,
            "timing_acc_sum": 0.0,
            "interval_preserve_sum": 0.0,
            "rhythm_preserve_sum": 0.0,
            "bar_valid_sum": 0.0,
        }
        for t in sorted(SEQUENCE_TASKS)
    }

    for g in gold_rows:
        task = g["task"]
        if task not in SEQUENCE_TASKS:
            continue
        rec = per_task[task]
        rec["n"] += 1

        rid = g["id"]
        p_row = pred_map.get(rid)
        if not p_row:
            rec["missing"] += 1
            continue

        tokenizer = args.tokenizer or g.get("meta", {}).get("tokenizer") or "note_level"
        pred_notes = get_prediction_notes(p_row, task, tokenizer)
        ref_notes = g["target_payload"]

        rec["exact_match"] += int(_seq_exact(pred_notes, ref_notes))
        rec["pitch_acc_sum"] += _pitch_accuracy(pred_notes, ref_notes)
        rec["duration_acc_sum"] += _duration_accuracy(pred_notes, ref_notes)
        rec["timing_acc_sum"] += _timing_accuracy(pred_notes, ref_notes)

        src = g["payload"]["melody"]
        if task == "task4_transposition":
            rec["interval_preserve_sum"] += _interval_preservation_rate(pred_notes, src)
            rec["rhythm_preserve_sum"] += _rhythm_preservation_rate(pred_notes, src)
        if task == "task7_rhythm_scale":
            rec["bar_valid_sum"] += float(_bar_valid(pred_notes))

    def finalize(x: dict) -> dict:
        n = x["n"] or 1
        out = {
            "n": x["n"],
            "missing": x["missing"],
            "exact_match": x["exact_match"] / n,
            "pitch_accuracy": x["pitch_acc_sum"] / n,
            "duration_accuracy": x["duration_acc_sum"] / n,
            "timing_accuracy": x["timing_acc_sum"] / n,
        }
        if x["interval_preserve_sum"] > 0 or x["rhythm_preserve_sum"] > 0:
            out["interval_preservation_rate"] = x["interval_preserve_sum"] / n
            out["rhythm_preservation_rate"] = x["rhythm_preserve_sum"] / n
        if x["bar_valid_sum"] > 0:
            out["bar_validity_rate"] = x["bar_valid_sum"] / n
        return out

    result = {
        "gold": args.gold,
        "pred": args.pred,
        "tasks": {t: finalize(per_task[t]) for t in sorted(SEQUENCE_TASKS)},
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote: {out_path}")
    print(json.dumps(result["tasks"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
