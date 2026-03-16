#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Edit this list for batch tests.
OLLAMA_MODELS = [
    "qwen2.5:3b",
    "qwen2.5:7b",
    "qwen3:4b",
]


class PartialTimeoutError(RuntimeError):
    def __init__(self, message: str, partial_text: str):
        super().__init__(message)
        self.partial_text = partial_text


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run benchmark cases on a list of Ollama models.")
    p.add_argument("--cases", default="benchmark/data/model_io/note_level/sequence_cases.json")
    p.add_argument(
        "--cases-list",
        default="",
        help="Comma-separated case json paths. If set, runs each benchmark file.",
    )
    p.add_argument("--models", default=",".join(OLLAMA_MODELS), help="Comma-separated models")
    p.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    p.add_argument("--out-dir", default="benchmark/results/ollama")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--timeout", type=float, default=60.0)
    p.add_argument("--max-cases", type=int, default=0, help="0 means all")
    p.add_argument("--sleep", type=float, default=0.0, help="sleep seconds between requests")
    p.add_argument(
        "--no-save-partial-on-timeout",
        action="store_false",
        dest="save_partial_on_timeout",
        help="Disable saving partial text when timeout happens.",
    )
    p.set_defaults(save_partial_on_timeout=True)
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


def bench_name_from_path(path: str) -> str:
    p = Path(path)
    parent = p.parent.name
    stem = p.stem
    return sanitize_name(f"{parent}_{stem}")


def messages_to_prompt(messages: list[dict]) -> str:
    parts = []
    for m in messages:
        role = str(m.get("role", "user")).upper()
        content = str(m.get("content", ""))
        parts.append(f"[{role}]\n{content}")
    return "\n\n".join(parts)


def ollama_generate(
    base_url: str,
    model: str,
    messages: list[dict],
    temperature: float,
    timeout: float,
    save_partial_on_timeout: bool,
) -> str:
    url = base_url.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": messages_to_prompt(messages),
        "stream": True,
        "options": {"temperature": temperature},
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    pieces: list[str] = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise RuntimeError(str(data["error"]))
                part = data.get("response")
                if part:
                    pieces.append(str(part))
                if data.get("done") is True:
                    break
    except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
        partial = "".join(pieces).strip()
        if save_partial_on_timeout and partial:
            raise PartialTimeoutError(f"timeout with partial output: {exc}", partial) from exc
        raise
    return "".join(pieces).strip()


def run_one_model(
    args: argparse.Namespace,
    model: str,
    cases: list[dict],
    cases_path: str,
) -> tuple[Path, Path]:
    bench = bench_name_from_path(cases_path)
    out_root = Path(args.out_dir) / bench / sanitize_name(model)
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
                out = ollama_generate(
                    args.base_url,
                    model,
                    messages,
                    args.temperature,
                    args.timeout,
                    args.save_partial_on_timeout,
                )
                err = ""
            except PartialTimeoutError as exc:
                out = exc.partial_text
                err = str(exc)
                print(f"[warn] model={model} case={cid} partial_timeout saved chars={len(out)}")
            except Exception as exc:
                out = ""
                err = str(exc)
                print(f"[warn] model={model} case={cid} error={exc}")
            row = {"case_id": cid, "prediction": out}
            if err:
                row["error"] = err
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if i % 10 == 0 or i == total:
                print(f"[ollama] model={model} progress={i}/{total}")
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
    case_paths = [c.strip() for c in args.cases_list.split(",") if c.strip()] or [args.cases]

    print(f"benchmarks={case_paths}")
    print(f"models={models}")
    for cases_path in case_paths:
        cases = load_cases(cases_path)
        if args.max_cases and args.max_cases > 0:
            cases = cases[: args.max_cases]
        print("")
        print(f"=== benchmark: {cases_path} cases={len(cases)} ===")
        for m in models:
            print("")
            print(f"=== running model: {m} ===")
            try:
                pred_path, ann_path = run_one_model(args, m, cases, cases_path)
                print(f"pred: {pred_path}")
                print(f"annotated: {ann_path}")
            except urllib.error.URLError as exc:
                print(f"[fatal] ollama unreachable: {exc}")
                return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
