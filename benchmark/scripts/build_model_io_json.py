#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.core.musicology import EXPLANATION_POLICY, THEORETICAL_SIMPLIFICATIONS, label_task_explanation
from benchmark.core.task_specs import (
    LABEL_TASKS,
    SEQUENCE_TASKS,
    TASK_GROUPS,
    TASK_TITLES,
    label_space_for_task,
    prediction_kind_for_task,
    primary_prediction_field_for_task,
)
from benchmark.tokenizers import render_by_tokenizer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build model-ready benchmark cases (JSON array).")
    p.add_argument("--src", required=True, help="Source jsonl file from benchmark/data/views/<tokenizer>/zero_shot.jsonl")
    p.add_argument("--out", required=True, help="Output .json path")
    p.add_argument("--task-group", choices=sorted(TASK_GROUPS.keys()), default="all")
    p.add_argument("--tasks", default="", help="Comma-separated task ids; overrides --task-group")
    p.add_argument("--split-by-task", action="store_true", help="Write one JSON file per task.")
    p.add_argument(
        "--out-dir",
        default="",
        help="Output directory used with --split-by-task (default: parent of --out).",
    )
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    args = parse_args()
    src = Path(args.src)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    selected_tasks = {t.strip() for t in args.tasks.split(",") if t.strip()} or set(TASK_GROUPS[args.task_group])
    rows = _load_jsonl(src)

    cases: list[dict] = []
    for r in rows:
        task = r.get("task", "")
        if task not in selected_tasks:
            continue
        system_prompt = r.get("system_prompt", "")
        user_prompt = r.get("user_prompt", r.get("input", ""))
        ground_truth = r.get("ground_truth", r.get("target", ""))
        tokenizer = str(r.get("meta", {}).get("tokenizer", "unknown"))
        prompt_mode = str(r.get("meta", {}).get("prompt_mode", "light"))
        payload = r.get("payload", {}) or {}
        target_payload = r.get("target_payload", {})
        prediction_kind = prediction_kind_for_task(task)
        primary_prediction_field = primary_prediction_field_for_task(task)
        target_explanation = label_task_explanation(task, payload, ground_truth) if task in LABEL_TASKS else ""

        melody_input_tokens = ""
        melody_target_tokens = ""
        if isinstance(payload, dict) and isinstance(payload.get("melody"), list):
            melody_input_tokens = render_by_tokenizer(tokenizer, payload["melody"])
        if isinstance(target_payload, list):
            melody_target_tokens = render_by_tokenizer(tokenizer, target_payload)

        control_params = {}
        for k in ("source_key", "target_key", "pivot", "factor"):
            if k in payload:
                control_params[k] = payload[k]

        question_prefix = f"Task={task}\nTokenizer={tokenizer}\nAnswer with only one line final output."
        question_body = TASK_TITLES.get(task, "")

        expected_label_space = label_space_for_task(task) if task in LABEL_TASKS else []
        input_label_context = r.get("input_tokenized", r.get("input", "")) if task in LABEL_TASKS else ""

        prompt_parts = {
            "question_prefix": question_prefix,
            "question_body": question_body,
            "control_params": control_params,
            "melody_input_tokens": melody_input_tokens,
            "input_label_context": input_label_context,
            "expected_label_space": expected_label_space,
            "answer_constraint": (
                "Return only the final label token, one line."
                if task in LABEL_TASKS
                else "Return only transformed melody tokens, one line."
            ),
        }

        # Build an optional recomposed prompt from prompt_parts for ablation experiments.
        param_line = " ".join(f"{k}={v}" for k, v in control_params.items())
        if input_label_context and task in LABEL_TASKS:
            composed_lines = [question_prefix, "Question:", input_label_context]
        else:
            composed_lines = [question_prefix, "Question:", question_body]
            if param_line:
                composed_lines.append(param_line)
            if melody_input_tokens:
                composed_lines.append(f"melody={melody_input_tokens}")
        user_prompt_recomposed = "\n".join(composed_lines)

        case = {
            "case_id": r["id"],
            "task": task,
            "tokenizer": tokenizer,
            "prompt_mode": prompt_mode,
            "prediction_type": prediction_kind,
            "prediction_kind": prediction_kind,
            "prediction_schema": {
                "prediction_type": prediction_kind,
                "primary_field": primary_prediction_field,
                "optional_fields": (
                    ["prediction_explanation"]
                    if task in LABEL_TASKS
                    else ["prediction_structured"]
                ),
                "fallback_fields": ["prediction"],
            },
            "usage_modes": {
                "standard": {
                    "required_prediction_fields": [primary_prediction_field],
                    "optional_prediction_fields": [],
                    "description": (
                        "Default benchmark mode for non-expert users. "
                        "Focus on strict, automatically evaluable outputs."
                    ),
                },
                "explanatory": {
                    "required_prediction_fields": [primary_prediction_field],
                    "optional_prediction_fields": (
                        ["prediction_explanation"] if task in LABEL_TASKS else []
                    ),
                    "description": (
                        "Optional analysis mode for paper-oriented qualitative work. "
                        "The main label or note prediction remains primary; "
                        "prediction_explanation is supplementary."
                    ),
                },
            },
            "musicology_schema": {
                "explanation_policy": EXPLANATION_POLICY,
                "prediction_explanation_supported": task in LABEL_TASKS,
                "target_explanation_available": bool(target_explanation),
                "theoretical_simplifications": THEORETICAL_SIMPLIFICATIONS,
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "model_input": {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
            },
            "prompt_parts": prompt_parts,
            "user_prompt_recomposed": user_prompt_recomposed,
            "melody_input_tokens": melody_input_tokens,
            "melody_target_tokens": melody_target_tokens,
            "input_label_context": input_label_context,
            "expected_label_space": expected_label_space,
            "control_params": control_params,
            "ground_truth": ground_truth,
            "target_explanation": target_explanation,
            "input_tokenized": r.get("input_tokenized", r.get("input", "")),
            "output_tokenized": r.get("output_tokenized", r.get("target", "")),
            "payload": payload,
            "target_payload": target_payload,
        }
        cases.append(case)

    if args.split_by_task:
        out_dir = Path(args.out_dir) if args.out_dir else out.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        by_task: dict[str, list[dict]] = {}
        for c in cases:
            t = str(c.get("task", "unknown"))
            by_task.setdefault(t, []).append(c)
        for task, arr in sorted(by_task.items()):
            fp = out_dir / f"{task}.json"
            fp.write_text(json.dumps(arr, ensure_ascii=False, indent=2 if args.pretty else None), encoding="utf-8")
            print(f"wrote: {fp} cases={len(arr)}")
        print(f"tasks: {len(by_task)} total_cases: {len(cases)}")
        return 0

    dump = json.dumps(cases, ensure_ascii=False, indent=2 if args.pretty else None)
    out.write_text(dump, encoding="utf-8")

    print(f"wrote: {out}")
    print(f"cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
