#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.core.predictions import make_prediction_row
from benchmark.core.task_specs import LABEL_TASKS, SEQUENCE_TASKS, TASK_GROUPS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create oracle predictions from benchmark cases by copying ground truth."
    )
    parser.add_argument("--cases", required=True, help="Path to benchmark cases JSON array.")
    parser.add_argument("--out", required=True, help="Output JSONL path.")
    parser.add_argument(
        "--task-group",
        choices=sorted(TASK_GROUPS.keys()),
        default="all",
        help="Limit output to a task family.",
    )
    parser.add_argument("--tasks", default="", help="Comma-separated task ids; overrides --task-group.")
    parser.add_argument(
        "--include-explanations",
        action="store_true",
        help="Attach target_explanation for label tasks.",
    )
    return parser.parse_args()


def _load_cases(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("cases file must be a JSON array")
    return data


def main() -> int:
    args = parse_args()
    cases_path = Path(args.cases)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    selected_tasks = {task.strip() for task in args.tasks.split(",") if task.strip()} or set(
        TASK_GROUPS[args.task_group]
    )

    rows: list[str] = []
    for case in _load_cases(cases_path):
        task = str(case.get("task", ""))
        if task not in selected_tasks:
            continue

        prediction_text = str(case.get("ground_truth", "")).strip()
        explanation = ""
        if args.include_explanations and task in LABEL_TASKS:
            explanation = str(case.get("target_explanation", "")).strip()

        pred_row = make_prediction_row(
            case=case,
            prediction_text=prediction_text,
            prediction_explanation=explanation,
        )

        if task in SEQUENCE_TASKS and isinstance(case.get("target_payload"), list):
            pred_row["prediction_structured"] = case["target_payload"]

        rows.append(json.dumps(pred_row, ensure_ascii=False))

    out_path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    print(f"wrote: {out_path}")
    print(f"rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
