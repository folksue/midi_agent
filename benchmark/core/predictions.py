from __future__ import annotations

import json

from ..tokenizers import decode_melody_by_tokenizer
from .task_specs import LABEL_TASKS, SEQUENCE_TASKS, prediction_kind_for_task


def get_prediction_text(row: dict, task: str) -> str:
    if task in LABEL_TASKS:
        keys = ("prediction_label", "prediction", "output", "pred", "answer")
    elif task in SEQUENCE_TASKS:
        keys = ("prediction_notes", "prediction", "output", "pred", "answer")
    else:
        keys = ("prediction", "output", "pred", "answer")
    for key in keys:
        if key in row:
            return str(row[key])
    return ""


def get_prediction_label(row: dict, task: str) -> str:
    return get_prediction_text(row, task).strip()


def get_prediction_explanation(row: dict) -> str:
    return str(row.get("prediction_explanation", "")).strip()


def _parse_structured_prediction(value: object) -> list[dict] | None:
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and isinstance(value.get("notes"), list):
        return value["notes"]
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except Exception:
        return None
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict) and isinstance(parsed.get("notes"), list):
        return parsed["notes"]
    return None


def get_prediction_notes(row: dict, task: str, tokenizer: str) -> list[dict]:
    structured = _parse_structured_prediction(row.get("prediction_structured"))
    if structured is not None:
        return structured
    text = get_prediction_text(row, task)
    return decode_melody_by_tokenizer(tokenizer, text)


def make_prediction_row(
    case: dict,
    prediction_text: str,
    error: str = "",
    prediction_explanation: str = "",
) -> dict:
    task = str(case.get("task", ""))
    kind = prediction_kind_for_task(task)
    row = {
        "case_id": case["case_id"],
        "prediction_type": kind,
        "prediction": prediction_text,
    }
    if kind == "label":
        row["prediction_label"] = prediction_text
    else:
        row["prediction_notes"] = prediction_text
    if prediction_explanation:
        row["prediction_explanation"] = prediction_explanation
    if error:
        row["error"] = error
    return row
