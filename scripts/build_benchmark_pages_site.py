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

SITE_DIR = REPO_ROOT / "docs" / "benchmark-site"
ASSETS_DIR = SITE_DIR / "assets"


def _read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    status = benchmark_web.get_status_payload()
    (ASSETS_DIR / "status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    oracle = status.get("runs", {}).get("oracle", {})
    oracle_eval = Path(str(oracle.get("path", ""))) if oracle.get("path") else None
    oracle_overall = Path(str(oracle.get("path", ""))).with_name("overall.json") if oracle_eval else None
    oracle_by_task = Path(str(oracle.get("path", ""))).with_name("by_task.json") if oracle_eval else None
    oracle_summary = Path(str(oracle.get("path", ""))).with_name("summary.json") if oracle_eval else None
    oracle_cases = Path(str(oracle.get("path", ""))).with_name("cases_with_outputs.json") if oracle_eval else None

    copied = {
        "oracle_eval": _copy_if_exists(oracle_eval, ASSETS_DIR / "oracle_eval.json") if oracle_eval else False,
        "oracle_overall": _copy_if_exists(oracle_overall, ASSETS_DIR / "oracle_overall.json")
        if oracle_overall
        else False,
        "oracle_by_task": _copy_if_exists(oracle_by_task, ASSETS_DIR / "oracle_by_task.json")
        if oracle_by_task
        else False,
        "oracle_summary": _copy_if_exists(oracle_summary, ASSETS_DIR / "oracle_summary.json")
        if oracle_summary
        else False,
    }

    if oracle_cases and oracle_cases.exists():
        cases = _read_json(oracle_cases, [])
        if isinstance(cases, list):
            sample_cases = cases[:6]
            (ASSETS_DIR / "oracle_cases_sample.json").write_text(
                json.dumps(sample_cases, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            copied["oracle_cases_sample"] = True
        else:
            copied["oracle_cases_sample"] = False
    else:
        copied["oracle_cases_sample"] = False

    (ASSETS_DIR / "manifest.json").write_text(
        json.dumps(
            {
                "site_name": "Symbolic Music Benchmark Pages",
                "generated_from_branch": "project-dev4paper",
                "copied_assets": copied,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Wrote site assets to {ASSETS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
