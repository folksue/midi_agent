#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# Mixed provider list example:
#   openai:gpt-4o-mini,gemini:gemini-2.5-flash
API_MODELS = [
    "openai:gpt-4o-mini",
]

SUPPORTED_PROVIDERS = {"openai", "gemini"}


@dataclass
class ModelSpec:
    provider: str
    model: str

    @property
    def display_name(self) -> str:
        return f"{self.provider}:{self.model}"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run benchmark cases on mixed API model list (OpenAI + Gemini).")
    p.add_argument("--cases", default="benchmark/data/model_io/note_level/sequence_cases.json")
    p.add_argument(
        "--cases-list",
        default="",
        help="Comma-separated case json paths. If set, runs each benchmark file.",
    )
    p.add_argument("--models", default=",".join(API_MODELS), help="Comma-separated models, e.g. openai:gpt-4o-mini,gemini:gemini-2.5-flash")
    p.add_argument("--default-provider", default=os.getenv("BENCHMARK_API_DEFAULT_PROVIDER", "openai"))
    p.add_argument("--out-dir", default="benchmark/results/api")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--timeout", type=float, default=60.0)
    p.add_argument("--max-cases", type=int, default=0, help="0 means all")
    p.add_argument("--sleep", type=float, default=0.0)
    p.add_argument(
        "--api-key",
        default=os.getenv("BENCHMARK_OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        help="OpenAI key (BENCHMARK_OPENAI_API_KEY > OPENAI_API_KEY).",
    )
    p.add_argument(
        "--base-url",
        default=os.getenv("BENCHMARK_OPENAI_BASE_URL", os.getenv("OPENAI_BASE_URL", "")),
        help="OpenAI base URL (BENCHMARK_OPENAI_BASE_URL > OPENAI_BASE_URL).",
    )
    p.add_argument(
        "--gemini-api-key",
        default=os.getenv("BENCHMARK_GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")),
        help="Gemini key (BENCHMARK_GEMINI_API_KEY > GEMINI_API_KEY).",
    )
    p.add_argument(
        "--gemini-endpoint",
        default=os.getenv("BENCHMARK_GEMINI_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta"),
        help="Gemini REST endpoint root.",
    )
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


def parse_model_specs(raw: str, default_provider: str) -> list[ModelSpec]:
    default_provider = (default_provider or "openai").strip().lower()
    if default_provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"unsupported default provider: {default_provider}")

    specs: list[ModelSpec] = []
    for tok in [x.strip() for x in raw.split(",") if x.strip()]:
        if ":" in tok:
            provider, model = tok.split(":", 1)
            provider = provider.strip().lower()
            model = model.strip()
        else:
            provider = default_provider
            model = tok
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"unsupported provider in models list: {provider}")
        if not model:
            raise ValueError(f"empty model in models list token: {tok}")
        specs.append(ModelSpec(provider=provider, model=model))
    return specs


def get_openai_client(api_key: str, base_url: str):
    if not api_key:
        raise RuntimeError("missing OpenAI API key: set --api-key or BENCHMARK_OPENAI_API_KEY or OPENAI_API_KEY")
    from openai import OpenAI

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def _to_gemini_payload(messages: list[dict], temperature: float) -> dict:
    system_parts: list[str] = []
    user_parts: list[str] = []
    for m in messages:
        role = str(m.get("role", "user")).strip().lower()
        content = str(m.get("content", "")).strip()
        if not content:
            continue
        if role == "system":
            system_parts.append(content)
        else:
            user_parts.append(content)
    return {
        "system_instruction": {"parts": [{"text": "\n\n".join(system_parts)}]} if system_parts else None,
        "contents": [{"role": "user", "parts": [{"text": "\n\n".join(user_parts)}]}],
        "generationConfig": {"temperature": temperature},
    }


def openai_generate(client, model: str, messages: list[dict], temperature: float, timeout: float) -> str:
    resp = client.responses.create(
        model=model,
        input=messages,
        temperature=temperature,
        timeout=timeout,
    )
    return str(getattr(resp, "output_text", "") or "").strip()


def gemini_generate(
    gemini_api_key: str,
    gemini_endpoint: str,
    model: str,
    messages: list[dict],
    temperature: float,
    timeout: float,
) -> str:
    if not gemini_api_key:
        raise RuntimeError("missing Gemini API key: set --gemini-api-key or BENCHMARK_GEMINI_API_KEY or GEMINI_API_KEY")
    endpoint = gemini_endpoint.rstrip("/")
    url = f"{endpoint}/models/{model}:generateContent"
    payload = _to_gemini_payload(messages, temperature)
    # Remove nullable field for strict servers.
    if payload.get("system_instruction") is None:
        payload.pop("system_instruction", None)
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    data = json.loads(body)
    cands = data.get("candidates", [])
    if not cands:
        raise RuntimeError(f"Gemini empty response: {body[:300]}")
    parts = cands[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not text:
        raise RuntimeError(f"Gemini no text content: {body[:300]}")
    return text


def generate_one(
    spec: ModelSpec,
    messages: list[dict],
    args: argparse.Namespace,
    openai_client,
) -> str:
    if spec.provider == "openai":
        return openai_generate(openai_client, spec.model, messages, args.temperature, args.timeout)
    return gemini_generate(
        gemini_api_key=args.gemini_api_key,
        gemini_endpoint=args.gemini_endpoint,
        model=spec.model,
        messages=messages,
        temperature=args.temperature,
        timeout=args.timeout,
    )


def run_one_model(
    args: argparse.Namespace,
    spec: ModelSpec,
    cases: list[dict],
    openai_client,
    cases_path: str,
) -> tuple[Path, Path]:
    bench = bench_name_from_path(cases_path)
    out_root = Path(args.out_dir) / bench / sanitize_name(spec.display_name)
    out_root.mkdir(parents=True, exist_ok=True)
    safe_model = sanitize_name(spec.display_name)

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
                out = generate_one(spec, messages, args, openai_client)
            except urllib.error.HTTPError as exc:
                out = ""
                body = exc.read().decode("utf-8", errors="replace")
                print(f"[warn] model={spec.display_name} case={cid} http={exc.code} body={body[:160]}")
            except Exception as exc:
                out = ""
                print(f"[warn] model={spec.display_name} case={cid} error={exc}")
            f.write(json.dumps({"case_id": cid, "prediction": out}, ensure_ascii=False) + "\n")
            if i % 10 == 0 or i == total:
                print(f"[api] model={spec.display_name} progress={i}/{total}")
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
        spec.display_name,
        "--pretty",
    ]
    subprocess.run(cmd, check=True)
    return pred_path, annotated_path


def main() -> int:
    args = parse_args()
    model_specs = parse_model_specs(args.models, args.default_provider)
    case_paths = [c.strip() for c in args.cases_list.split(",") if c.strip()] or [args.cases]

    openai_client = None
    if any(x.provider == "openai" for x in model_specs):
        openai_client = get_openai_client(args.api_key, args.base_url)
    if any(x.provider == "gemini" for x in model_specs) and not args.gemini_api_key:
        raise RuntimeError(
            "missing Gemini API key: set --gemini-api-key or BENCHMARK_GEMINI_API_KEY or GEMINI_API_KEY"
        )

    names = [x.display_name for x in model_specs]
    print(f"benchmarks={case_paths}")
    print(f"models={names}")
    for cases_path in case_paths:
        cases = load_cases(cases_path)
        if args.max_cases and args.max_cases > 0:
            cases = cases[: args.max_cases]
        print("")
        print(f"=== benchmark: {cases_path} cases={len(cases)} ===")
        for spec in model_specs:
            print("")
            print(f"=== running model: {spec.display_name} ===")
            pred_path, ann_path = run_one_model(args, spec, cases, openai_client, cases_path)
            print(f"pred: {pred_path}")
            print(f"annotated: {ann_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
