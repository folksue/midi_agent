#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from benchmark.core.predictions import make_prediction_row

# Edit this list for batch tests.
API_MODELS = [
    "gpt-4o-mini",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run benchmark cases on a list of API models (OpenAI-compatible).")
    p.add_argument("--cases", default="benchmark/data/model_io/note_level/sequence_cases.json")
    p.add_argument("--models", default=",".join(API_MODELS), help="Comma-separated models")
    p.add_argument("--out-dir", default="benchmark/results/api")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--timeout", type=float, default=60.0)
    p.add_argument("--max-cases", type=int, default=0, help="0 means all")
    p.add_argument("--sleep", type=float, default=0.0)
    p.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", ""), help="Optional OpenAI-compatible base URL")
    p.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY", ""), help="API key (or use OPENAI_API_KEY)")
    return p.parse_args()


def sanitize_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s)


def load_cases(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("cases json must be an array")
    return data


def get_client(api_key: str, base_url: str):
    if not api_key:
        raise RuntimeError("missing API key: set --api-key or OPENAI_API_KEY")
    from openai import OpenAI

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def api_generate(client, model: str, messages: list[dict], temperature: float, timeout: float) -> str:
    resp = client.responses.create(
        model=model,
        input=messages,
        temperature=temperature,
        timeout=timeout,
    )
    return str(getattr(resp, "output_text", "") or "").strip()


def run_one_model(args: argparse.Namespace, client, model: str, cases: list[dict]) -> tuple[Path, Path]:
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    safe_model = sanitize_name(model)

    pred_path = out_root / f"pred_{safe_model}.jsonl"
    cases_used_path = out_root / f"cases_used_{safe_model}.json"
    cases_used_path.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    with pred_path.open("w", encoding="utf-8") as f:
        total = len(cases)
        for i, c in enumerate(cases, 1):
            cid = c["case_id"]
            messages = c.get("messages") or [
                {"role": "system", "content": c.get("model_input", {}).get("system_prompt", "")},
                {"role": "user", "content": c.get("model_input", {}).get("user_prompt", "")},
            ]
            try:
                out = api_generate(client, model, messages, args.temperature, args.timeout)
                err = ""
            except Exception as exc:
                out = ""
                err = str(exc)
                print(f"[warn] model={model} case={cid} error={exc}")
            row = make_prediction_row(c, out, error=err)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if i % 10 == 0 or i == total:
                print(f"[api] model={model} progress={i}/{total}")
            if args.sleep > 0:
                time.sleep(args.sleep)

    annotated_path = out_root / f"cases_with_outputs_{safe_model}.json"
    summary_path = out_root / f"summary_{safe_model}.json"
    cmd = [
        sys.executable,
        "-m",
        "benchmark.scripts.annotate_model_outputs",
        "--cases",
        str(cases_used_path),
        "--pred",
        str(pred_path),
        "--out",
        str(annotated_path),
        "--summary-out",
        str(summary_path),
        "--model-name",
        model,
        "--pretty",
    ]
    subprocess.run(cmd, check=True)
    return pred_path, annotated_path


def main() -> int:
    args = parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    cases = load_cases(args.cases)
    if args.max_cases and args.max_cases > 0:
        cases = cases[: args.max_cases]

    client = get_client(args.api_key, args.base_url)

    print(f"cases={len(cases)} models={models}")
    for m in models:
        print("")
        print(f"=== running model: {m} ===")
        pred_path, ann_path = run_one_model(args, client, m, cases)
        print(f"pred: {pred_path}")
        print(f"annotated: {ann_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
