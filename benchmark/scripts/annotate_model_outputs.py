#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.core.predictions import get_prediction_explanation, get_prediction_label, get_prediction_notes
from benchmark.core.task_specs import SEQUENCE_TASKS


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Attach model outputs to benchmark cases and mark hit_ground_truth.")
    p.add_argument("--cases", required=True, help="Input cases json (array).")
    p.add_argument(
        "--pred",
        required=True,
        help="Prediction jsonl. One line per case. Need id/case_id plus one of prediction/output/pred/answer.",
    )
    p.add_argument("--out", required=True, help="Output json (same case format + model_output + hit_ground_truth).")
    p.add_argument("--model-name", default="", help="Optional model name; saved into each case as model_name.")
    p.add_argument(
        "--match-mode",
        choices=["auto", "text", "semantic"],
        default="auto",
        help="How to compute hit_ground_truth. auto=semantic for sequence tasks, text for others.",
    )
    p.add_argument("--summary-out", default="", help="Optional summary json output path (overall + by_task).")
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def _load_cases(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("cases file must be a JSON array")
    return data


def _load_pred_map(path: Path) -> dict[str, dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    out: dict[str, dict] = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        row = json.loads(ln)
        rid = str(row.get("case_id") or row.get("id") or "")
        if not rid:
            continue
        out[rid] = row
    return out


def _tol_eq(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) <= eps


def _levenshtein(a: list[str], b: list[str]) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    dp = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev = dp[0]
        dp[0] = i
        for j, y in enumerate(b, 1):
            old = dp[j]
            cost = 0 if x == y else 1
            dp[j] = min(
                dp[j] + 1,      # delete
                dp[j - 1] + 1,  # insert
                prev + cost,    # replace / keep
            )
            prev = old
    return dp[-1]


def _events_equal(pred: list[dict], ref: list[dict]) -> bool:
    if len(pred) != len(ref):
        return False
    for a, b in zip(pred, ref):
        if int(a.get("p", -999)) != int(b.get("p", -998)):
            return False
        if not _tol_eq(float(a.get("d", -1)), float(b.get("d", -2))):
            return False
        if not _tol_eq(float(a.get("t", 0.0)), float(b.get("t", 0.0))):
            return False
        if "v" in b and int(a.get("v", int(b["v"]))) != int(b["v"]):
            return False
    return True


def _text_norm(s: str) -> str:
    return " ".join((s or "").strip().split())


def _text_token_error_rate(pred_text: str, ref_text: str) -> float:
    ref_tokens = _text_norm(ref_text).split()
    pred_tokens = _text_norm(pred_text).split()
    if not ref_tokens:
        return 0.0 if not pred_tokens else 1.0
    dist = _levenshtein(ref_tokens, pred_tokens)
    return dist / len(ref_tokens)


def _text_char_error_rate(pred_text: str, ref_text: str) -> float:
    ref_chars = list((ref_text or "").strip())
    pred_chars = list((pred_text or "").strip())
    if not ref_chars:
        return 0.0 if not pred_chars else 1.0
    dist = _levenshtein(ref_chars, pred_chars)
    return dist / len(ref_chars)


def _event_token(n: dict) -> str:
    return (
        f"t={float(n.get('t', 0.0)):.6f}|"
        f"p={int(n.get('p', -1))}|"
        f"d={float(n.get('d', 0.0)):.6f}|"
        f"v={int(n.get('v', 80))}"
    )


def _note_event_error_rate(pred_events: list[dict], ref_events: list[dict]) -> float:
    ref_tokens = [_event_token(x) for x in ref_events]
    pred_tokens = [_event_token(x) for x in pred_events]
    if not ref_tokens:
        return 0.0 if not pred_tokens else 1.0
    dist = _levenshtein(ref_tokens, pred_tokens)
    return dist / len(ref_tokens)


def _hit_with_reason(case: dict, pred_row: dict, match_mode: str) -> tuple[bool, str, str]:
    task = str(case.get("task", ""))
    model_output = (
        get_prediction_label(pred_row, task)
        if task not in SEQUENCE_TASKS
        else str(pred_row.get("prediction_notes") or pred_row.get("prediction") or "").strip()
    )
    if not str(model_output).strip():
        return False, "missing_output", "model_output is empty"

    if match_mode == "text":
        ok = _text_norm(model_output) == _text_norm(str(case.get("ground_truth", "")))
        return (True, "hit", "text_equal") if ok else (False, "mismatch", "text_not_equal")

    if match_mode == "semantic" or (match_mode == "auto" and task in SEQUENCE_TASKS):
        tokenizer = str(case.get("tokenizer", "note_level"))
        ref = case.get("target_payload")
        if isinstance(ref, list):
            try:
                pred = get_prediction_notes(pred_row, task, tokenizer)
            except Exception as exc:
                return False, "decode_error", f"{type(exc).__name__}: {exc}"
            ok = _events_equal(pred, ref)
            return (True, "hit", "semantic_equal") if ok else (False, "mismatch", "semantic_not_equal")
        return False, "invalid_target_payload", "target_payload is not a list"

    # auto fallback for non-sequence tasks
    ok = _text_norm(model_output) == _text_norm(str(case.get("ground_truth", "")))
    return (True, "hit", "text_equal") if ok else (False, "mismatch", "text_not_equal")


def main() -> int:
    args = parse_args()
    cases_path = Path(args.cases)
    pred_path = Path(args.pred)
    out_path = Path(args.out)

    cases = _load_cases(cases_path)
    pred_map = _load_pred_map(pred_path)

    hit_count = 0
    miss_count = 0
    reason_counter: dict[str, int] = {}
    by_task: dict[str, dict] = {}
    text_ter_sum = 0.0
    text_cer_sum = 0.0
    note_event_ter_sum = 0.0
    note_event_ter_count = 0
    for c in cases:
        task = str(c.get("task", "unknown"))
        if task not in by_task:
            by_task[task] = {
                "cases": 0,
                "hit": 0,
                "miss": 0,
                "text_ter_sum": 0.0,
                "text_cer_sum": 0.0,
                "note_event_ter_sum": 0.0,
                "note_event_ter_count": 0,
                "match_status_counts": {},
            }
        tstat = by_task[task]
        tstat["cases"] += 1

        rid = str(c.get("case_id") or c.get("id") or "")
        pred_row = pred_map.get(rid, {})
        model_output = (
            get_prediction_label(pred_row, str(c.get("task", "")))
            if str(c.get("task", "")) not in SEQUENCE_TASKS
            else str(pred_row.get("prediction_notes") or pred_row.get("prediction") or "")
        )
        ok, status, detail = _hit_with_reason(c, pred_row, args.match_mode)
        c["model_output"] = model_output
        if get_prediction_explanation(pred_row):
            c["prediction_explanation"] = get_prediction_explanation(pred_row)
        c["hit_ground_truth"] = bool(ok)
        c["match_status"] = status
        c["match_detail"] = detail
        gt = str(c.get("ground_truth", ""))
        c["text_token_error_rate"] = _text_token_error_rate(model_output, gt)
        c["text_char_error_rate"] = _text_char_error_rate(model_output, gt)
        text_ter_sum += c["text_token_error_rate"]
        text_cer_sum += c["text_char_error_rate"]
        tstat["text_ter_sum"] += c["text_token_error_rate"]
        tstat["text_cer_sum"] += c["text_char_error_rate"]

        # Sequence-task note-specialized TER (event-level).
        if str(c.get("task", "")) in SEQUENCE_TASKS and isinstance(c.get("target_payload"), list):
            tokenizer = str(c.get("tokenizer", "note_level"))
            try:
                pred_ev = get_prediction_notes(pred_row, str(c.get("task", "")), tokenizer)
                ref_ev = c["target_payload"]
                c["note_event_error_rate"] = _note_event_error_rate(pred_ev, ref_ev)
                note_event_ter_sum += c["note_event_error_rate"]
                note_event_ter_count += 1
                tstat["note_event_ter_sum"] += c["note_event_error_rate"]
                tstat["note_event_ter_count"] += 1
            except Exception as exc:
                c["note_event_error_rate"] = 1.0
                c["note_event_error_rate_detail"] = f"decode_error: {type(exc).__name__}: {exc}"
                note_event_ter_sum += 1.0
                note_event_ter_count += 1
                tstat["note_event_ter_sum"] += 1.0
                tstat["note_event_ter_count"] += 1

        if args.model_name:
            c["model_name"] = args.model_name
        reason_counter[status] = reason_counter.get(status, 0) + 1
        tmsc = tstat["match_status_counts"]
        tmsc[status] = tmsc.get(status, 0) + 1
        if ok:
            hit_count += 1
            tstat["hit"] += 1
        else:
            miss_count += 1
            tstat["miss"] += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cases, ensure_ascii=False, indent=2 if args.pretty else None), encoding="utf-8")

    total = len(cases)
    acc = hit_count / total if total else 0.0
    text_ter_avg = text_ter_sum / total if total else 0.0
    text_cer_avg = text_cer_sum / total if total else 0.0
    note_event_ter_avg = note_event_ter_sum / note_event_ter_count if note_event_ter_count else 0.0
    print(f"wrote: {out_path}")
    print(f"cases={total} hit={hit_count} miss={miss_count} acc={acc:.4f}")
    print(
        f"text_token_error_rate_avg={text_ter_avg:.4f} "
        f"text_char_error_rate_avg={text_cer_avg:.4f} "
        f"note_event_error_rate_avg={note_event_ter_avg:.4f}"
    )
    print("match_status_counts=", json.dumps(reason_counter, ensure_ascii=False))

    by_task_out: dict[str, dict] = {}
    for task, s in sorted(by_task.items()):
        n = s["cases"] or 1
        ne_n = s["note_event_ter_count"] or 1
        by_task_out[task] = {
            "cases": s["cases"],
            "hit": s["hit"],
            "miss": s["miss"],
            "acc": s["hit"] / n,
            "text_token_error_rate_avg": s["text_ter_sum"] / n,
            "text_char_error_rate_avg": s["text_cer_sum"] / n,
            "note_event_error_rate_avg": (
                s["note_event_ter_sum"] / ne_n if s["note_event_ter_count"] > 0 else None
            ),
            "match_status_counts": s["match_status_counts"],
        }
    print("by_task=", json.dumps(by_task_out, ensure_ascii=False))

    if args.summary_out:
        summary = {
            "overall": {
                "cases": total,
                "hit": hit_count,
                "miss": miss_count,
                "acc": acc,
                "text_token_error_rate_avg": text_ter_avg,
                "text_char_error_rate_avg": text_cer_avg,
                "note_event_error_rate_avg": note_event_ter_avg,
                "match_status_counts": reason_counter,
            },
            "by_task": by_task_out,
        }
        sp = Path(args.summary_out)
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote summary: {sp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
