#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.core.render import compose_user_prompt_from_parts, render_user_prompt_parts
from benchmark.tokenizers import render_by_tokenizer

TASK_GROUPS = {
    "all": {
        "task1_interval_identification",
        "task2_chord_identification",
        "task3_harmonic_function",
        "task4_transposition",
        "task5_melodic_inversion",
        "task6_retrograde",
        "task7_rhythm_scale",
        "task8_voice_leading",
    },
    "label": {
        "task1_interval_identification",
        "task2_chord_identification",
        "task3_harmonic_function",
        "task8_voice_leading",
    },
    "sequence": {
        "task4_transposition",
        "task5_melodic_inversion",
        "task6_retrograde",
        "task7_rhythm_scale",
    },
}

LABEL_TASKS = {
    "task1_interval_identification",
    "task2_chord_identification",
    "task3_harmonic_function",
    "task8_voice_leading",
}

SEQUENCE_TASKS = {
    "task4_transposition",
    "task5_melodic_inversion",
    "task6_retrograde",
    "task7_rhythm_scale",
}


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

    selected_tasks = {t.strip() for t in args.tasks.split(",") if t.strip()} or TASK_GROUPS[args.task_group]
    rows = _load_jsonl(src)

    cases: list[dict] = []
    for r in rows:
        task = r.get("task", "")
        if task not in selected_tasks:
            continue
        system_prompt = r.get("system_prompt", "")
        ground_truth = r.get("ground_truth", r.get("target", ""))
        tokenizer = str(r.get("meta", {}).get("tokenizer", "unknown"))
        prompt_mode = str(r.get("meta", {}).get("prompt_mode", "light"))
        payload = r.get("payload", {}) or {}
        target_payload = r.get("target_payload", {})
        prompt_parts = render_user_prompt_parts(task, payload, tokenizer=tokenizer, prompt_mode=prompt_mode)
        user_prompt = compose_user_prompt_from_parts(prompt_parts)

        melody_target_tokens = ""
        if task in SEQUENCE_TASKS and isinstance(target_payload, list):
            melody_target_tokens = render_by_tokenizer(tokenizer, target_payload)

        control_params = dict(prompt_parts.get("control_params", {}))
        melody_input_tokens = str(prompt_parts.get("melody_input_tokens", ""))
        user_prompt_recomposed = user_prompt

        case = {
            "case_id": r["id"],
            "task": task,
            "tokenizer": tokenizer,
            "prompt_mode": prompt_mode,
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
            "control_params": control_params,
            "ground_truth": ground_truth,
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
