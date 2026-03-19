#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import benchmark_web

SITE_DIR = REPO_ROOT / "visual-demo"
ASSETS_DIR = SITE_DIR / "assets"
RESULTS_DIR = REPO_ROOT / "benchmark" / "results"
TOKENIZERS = tuple(benchmark_web.TOKENIZERS)


def _read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _copy_if_exists(src: Path | None, dst: Path) -> bool:
    if src is None or not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def _rel(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _mtime_epoch(path: Path | None) -> float:
    return path.stat().st_mtime if path and path.exists() else 0.0


def _mtime_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return benchmark_web._mtime_text(path)


def _task_sort_key(task_name: str) -> tuple[int, str]:
    prefix, _, suffix = task_name.partition("_")
    if prefix.startswith("task"):
        number_text = prefix[4:]
        if number_text.isdigit():
            return (int(number_text), suffix or task_name)
    return (999, task_name)


def _task_label(task_name: str) -> str:
    _, _, suffix = task_name.partition("_")
    label = suffix or task_name
    return label.replace("_", " ")


def _run_name_from_parts(parts: tuple[str, ...], stem: str, tokenizer: str) -> str:
    if stem == "overall":
        if "oracle" in parts:
            return "oracle"
        if "custom" in parts:
            return "custom"
        return parts[-2] if tokenizer == "unknown" and len(parts) >= 2 else parts[-1]
    return stem[len("overall_") :]


def _source_from_parts(parts: tuple[str, ...], tokenizer: str) -> str:
    if tokenizer in parts:
        tokenizer_idx = parts.index(tokenizer)
        source_parts = parts[:tokenizer_idx]
        if source_parts:
            return "/".join(source_parts)
    if len(parts) > 1:
        return "/".join(parts[:-1])
    return "results"


def _scan_run_catalog() -> list[dict]:
    run_catalog: list[dict] = []
    for overall_path in sorted(RESULTS_DIR.rglob("overall*.json")):
        rel_parts = overall_path.relative_to(RESULTS_DIR).parts
        stem = overall_path.stem
        tokenizer = next((part for part in rel_parts if part in TOKENIZERS), "unknown")
        source = _source_from_parts(rel_parts, tokenizer)
        run_name = _run_name_from_parts(rel_parts, stem, tokenizer)
        run_kind = "oracle" if "oracle" in rel_parts else "custom" if "custom" in rel_parts else "external"

        if stem == "overall":
            by_task_path = overall_path.with_name("by_task.json")
            by_tokenizer_path = overall_path.with_name("by_tokenizer.json")
            eval_path = overall_path.with_name("eval_predictions.json")
            summary_path = overall_path.with_name("summary.json")
            annotated_path = overall_path.with_name("cases_with_outputs.json")
        else:
            suffix = stem[len("overall_") :]
            by_task_path = overall_path.with_name(f"by_task_{suffix}.json")
            by_tokenizer_path = overall_path.with_name(f"by_tokenizer_{suffix}.json")
            eval_path = overall_path.with_name(f"eval_{suffix}.json")
            summary_path = overall_path.with_name(f"summary_{suffix}.json")
            annotated_path = overall_path.with_name(f"cases_with_outputs_{suffix}.json")

        overall = _read_json(overall_path, {})
        by_task = _read_json(by_task_path, {})
        by_tokenizer = _read_json(by_tokenizer_path, {})

        if not isinstance(overall, dict):
            continue
        if not isinstance(by_task, dict):
            by_task = {}
        if not isinstance(by_tokenizer, dict):
            by_tokenizer = {}

        display_name = "oracle" if run_name == "oracle" else run_name
        display_label = f"{display_name} · {tokenizer}"
        family_label = f"{display_name} [{source}]" if source and source != "webui/oracle" else display_name

        run_catalog.append(
            {
                "key": f"{source}:{run_name}:{tokenizer}",
                "source": source,
                "run_kind": run_kind,
                "run_name": run_name,
                "display_name": display_name,
                "display_label": display_label,
                "family_label": family_label,
                "tokenizer": tokenizer,
                "accuracy": overall.get("accuracy"),
                "cases": overall.get("cases", 0),
                "hit": overall.get("hit", 0),
                "missing": overall.get("missing", 0),
                "updated_at": _mtime_text(eval_path if eval_path.exists() else overall_path),
                "updated_at_epoch": _mtime_epoch(eval_path if eval_path.exists() else overall_path),
                "paths": {
                    "overall": _rel(overall_path),
                    "by_task": _rel(by_task_path),
                    "by_tokenizer": _rel(by_tokenizer_path),
                    "eval": _rel(eval_path),
                    "summary": _rel(summary_path),
                    "annotated": _rel(annotated_path),
                },
                "overall": overall,
                "by_task": by_task,
                "by_tokenizer": by_tokenizer,
            }
        )

    return sorted(run_catalog, key=lambda row: (row["updated_at_epoch"], row["display_label"]), reverse=True)


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _build_chart_data(run_catalog: list[dict]) -> dict:
    tasks = sorted(
        {
            task_name
            for run in run_catalog
            for task_name in run.get("by_task", {}).keys()
        },
        key=_task_sort_key,
    )
    task_labels = [_task_label(task_name) for task_name in tasks]

    overall_runs = [
        {
            "label": run["display_label"],
            "family_label": run["family_label"],
            "tokenizer": run["tokenizer"],
            "source": run["source"],
            "accuracy": run["accuracy"],
            "cases": run["cases"],
            "updated_at": run["updated_at"],
        }
        for run in run_catalog
    ]

    task_average = []
    for task_name, task_label in zip(tasks, task_labels):
        values = [
            float(run["by_task"][task_name]["accuracy"])
            for run in run_catalog
            if task_name in run["by_task"] and isinstance(run["by_task"][task_name].get("accuracy"), (int, float))
        ]
        avg = _avg(values)
        task_average.append(
            {
                "task": task_name,
                "label": task_label,
                "accuracy": avg,
                "run_count": len(values),
            }
        )

    latest_runs = run_catalog[: min(6, len(run_catalog))]
    task_by_run = {
        "labels": task_labels,
        "datasets": [
            {
                "label": run["display_label"],
                "tokenizer": run["tokenizer"],
                "source": run["source"],
                "data": [
                    (
                        run["by_task"].get(task_name, {}).get("accuracy")
                        if isinstance(run["by_task"].get(task_name, {}).get("accuracy"), (int, float))
                        else None
                    )
                    for task_name in tasks
                ],
            }
            for run in latest_runs
        ],
    }

    tokenizer_groups: dict[str, dict[str, float | None]] = {}
    tokenizer_sources: dict[str, str] = {}
    for run in run_catalog:
        family_label = run["family_label"]
        tokenizer_groups.setdefault(family_label, {tokenizer: None for tokenizer in TOKENIZERS})
        tokenizer_sources[family_label] = run["source"]
        if run["tokenizer"] in TOKENIZERS and isinstance(run["accuracy"], (int, float)):
            tokenizer_groups[family_label][run["tokenizer"]] = float(run["accuracy"])

    tokenizer_comparison = {
        "labels": list(TOKENIZERS),
        "datasets": [
            {
                "label": family_label,
                "source": tokenizer_sources.get(family_label, ""),
                "data": [tokenizer_groups[family_label].get(tokenizer) for tokenizer in TOKENIZERS],
            }
            for family_label in sorted(tokenizer_groups.keys())
        ],
    }

    heatmap = {
        "rows": [run["display_label"] for run in latest_runs],
        "cols": task_labels,
        "values": [
            [
                (
                    run["by_task"].get(task_name, {}).get("accuracy")
                    if isinstance(run["by_task"].get(task_name, {}).get("accuracy"), (int, float))
                    else None
                )
                for task_name in tasks
            ]
            for run in latest_runs
        ],
    }

    source_counts: dict[str, int] = {}
    for run in run_catalog:
        source_counts[run["source"]] = source_counts.get(run["source"], 0) + 1

    return {
        "overall_runs": overall_runs,
        "task_average": task_average,
        "task_by_run": task_by_run,
        "tokenizer_comparison": tokenizer_comparison,
        "heatmap": heatmap,
        "source_counts": {
            "labels": list(source_counts.keys()),
            "data": [source_counts[label] for label in source_counts.keys()],
        },
    }


def _copy_latest_oracle_assets(status: dict) -> dict:
    oracle = status.get("runs", {}).get("oracle", {})
    oracle_eval = Path(str(oracle.get("path", ""))) if oracle.get("path") else None
    oracle_overall = Path(str(oracle.get("path", ""))).with_name("overall.json") if oracle_eval else None
    oracle_by_task = Path(str(oracle.get("path", ""))).with_name("by_task.json") if oracle_eval else None
    oracle_summary = Path(str(oracle.get("path", ""))).with_name("summary.json") if oracle_eval else None
    oracle_cases = Path(str(oracle.get("path", ""))).with_name("cases_with_outputs.json") if oracle_eval else None

    copied = {
        "oracle_eval": _copy_if_exists(oracle_eval, ASSETS_DIR / "oracle_eval.json"),
        "oracle_overall": _copy_if_exists(oracle_overall, ASSETS_DIR / "oracle_overall.json"),
        "oracle_by_task": _copy_if_exists(oracle_by_task, ASSETS_DIR / "oracle_by_task.json"),
        "oracle_summary": _copy_if_exists(oracle_summary, ASSETS_DIR / "oracle_summary.json"),
    }

    if oracle_cases and oracle_cases.exists():
        cases = _read_json(oracle_cases, [])
        sample_cases = cases[:6] if isinstance(cases, list) else []
        _write_json(ASSETS_DIR / "oracle_cases_sample.json", sample_cases)
        copied["oracle_cases_sample"] = True
    else:
        copied["oracle_cases_sample"] = False

    return copied


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    status = benchmark_web.get_status_payload()
    _write_json(ASSETS_DIR / "status.json", status)

    copied = _copy_latest_oracle_assets(status)
    run_catalog = _scan_run_catalog()
    chart_data = _build_chart_data(run_catalog)

    _write_json(ASSETS_DIR / "run_catalog.json", run_catalog)
    _write_json(ASSETS_DIR / "chart_data.json", chart_data)
    _write_json(
        ASSETS_DIR / "manifest.json",
        {
            "site_name": "Symbolic Music Benchmark Visual Demo",
            "site_kind": "visual-demo",
            "generated_from_branch": "project-dev4paper",
            "run_count": len(run_catalog),
            "copied_assets": copied,
        },
    )

    print(f"Wrote site assets to {ASSETS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
