#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

LABEL_TASKS = {
    "task1_interval_identification",
    "task2_chord_identification",
    "task3_harmonic_function",
    "task4_voice_leading",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate Label Classification tasks (Task 1/2/3/4).")
    p.add_argument("--gold", required=True, help="Benchmark jsonl view file (note_level/midilike/remilike).")
    p.add_argument("--pred", required=True, help="Prediction jsonl. Each line: {id|case_id, prediction|output|pred|answer}.")
    p.add_argument("--out", default="benchmark/results/label_eval.json")
    return p.parse_args()


def _load_jsonl(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def _norm_label(text: str) -> str:
    return " ".join((text or "").strip().split()).lower()


def _get_prediction_text(row: dict) -> str:
    for k in ("prediction", "output", "pred", "answer"):
        if k in row:
            return str(row[k])
    return ""


def _macro_f1(preds: list[str], refs: list[str]) -> float:
    labels = sorted(set(refs) | set(preds))
    if not labels:
        return 0.0
    f1_sum = 0.0
    for lab in labels:
        tp = sum(1 for p, r in zip(preds, refs) if p == lab and r == lab)
        fp = sum(1 for p, r in zip(preds, refs) if p == lab and r != lab)
        fn = sum(1 for p, r in zip(preds, refs) if p != lab and r == lab)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 0.0 if (prec + rec) == 0 else (2 * prec * rec / (prec + rec))
        f1_sum += f1
    return f1_sum / len(labels)


def _parse_chord(label: str) -> tuple[str, str]:
    x = (label or "").strip()
    if x.endswith("7") and "_" not in x:
        return x[:-1], "dominant7"
    if "_" in x:
        root, quality = x.split("_", 1)
        return root, quality
    return x, ""


def main() -> int:
    args = parse_args()
    gold_rows = _load_jsonl(args.gold)
    pred_rows = _load_jsonl(args.pred)

    pred_map: dict[str, dict] = {}
    for r in pred_rows:
        rid = str(r.get("id") or r.get("case_id") or "")
        if rid:
            pred_map[rid] = r

    per_task: dict[str, dict] = {}
    for t in sorted(LABEL_TASKS):
        per_task[t] = {
            "n": 0,
            "missing": 0,
            "exact_match_count": 0,
            "pred_labels": [],
            "ref_labels": [],
            "task2_root_match_count": 0,
            "task2_quality_match_count": 0,
        }

    for g in gold_rows:
        task = str(g.get("task", ""))
        if task not in LABEL_TASKS:
            continue
        rec = per_task[task]
        rec["n"] += 1

        rid = str(g.get("id", ""))
        p_row = pred_map.get(rid)
        if not p_row:
            rec["missing"] += 1
            continue

        pred = _norm_label(_get_prediction_text(p_row))
        ref = _norm_label(str(g.get("ground_truth") or g.get("target") or ""))
        rec["pred_labels"].append(pred)
        rec["ref_labels"].append(ref)
        rec["exact_match_count"] += int(pred == ref)

        if task == "task2_chord_identification":
            pred_root, pred_quality = _parse_chord(pred)
            ref_root, ref_quality = _parse_chord(ref)
            rec["task2_root_match_count"] += int(pred_root == ref_root)
            rec["task2_quality_match_count"] += int(pred_quality == ref_quality)

    tasks_out: dict[str, dict] = {}
    all_preds: list[str] = []
    all_refs: list[str] = []
    total_n = 0
    total_missing = 0
    total_exact = 0
    for task, x in sorted(per_task.items()):
        n = x["n"]
        den = n if n else 1
        acc = x["exact_match_count"] / den
        mf1 = _macro_f1(x["pred_labels"], x["ref_labels"]) if x["ref_labels"] else 0.0
        out = {
            "n": n,
            "missing": x["missing"],
            "exact_match": acc,
            "macro_f1": mf1,
        }
        if task == "task2_chord_identification":
            out["root_accuracy"] = x["task2_root_match_count"] / den
            out["quality_accuracy"] = x["task2_quality_match_count"] / den
        tasks_out[task] = out

        all_preds.extend(x["pred_labels"])
        all_refs.extend(x["ref_labels"])
        total_n += n
        total_missing += x["missing"]
        total_exact += x["exact_match_count"]

    result = {
        "gold": args.gold,
        "pred": args.pred,
        "overall": {
            "n": total_n,
            "missing": total_missing,
            "exact_match": (total_exact / total_n) if total_n else 0.0,
            "macro_f1": _macro_f1(all_preds, all_refs) if all_refs else 0.0,
        },
        "tasks": tasks_out,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote: {out_path}")
    print(json.dumps(result["tasks"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
