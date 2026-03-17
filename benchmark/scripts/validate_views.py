#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.core.task_specs import SEQUENCE_TASKS
from benchmark.tokenizers import decode_melody_by_tokenizer


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate tokenizer view consistency.")
    p.add_argument("--views-dir", default="benchmark/data/views")
    p.add_argument("--tokenizers", default="note_level,midilike,remilike")
    p.add_argument("--file", default="zero_shot.jsonl")
    return p.parse_args()


def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    args = parse_args()
    toks = [x.strip() for x in args.tokenizers.split(",") if x.strip()]

    tables: dict[str, list[dict]] = {}
    for t in toks:
        p = Path(args.views_dir) / t / args.file
        tables[t] = load_rows(p)

    base = toks[0]
    base_rows = tables[base]
    base_ids = [r["id"] for r in base_rows]

    for t in toks[1:]:
        ids = [r["id"] for r in tables[t]]
        if ids != base_ids:
            raise AssertionError(f"id mismatch: {base} vs {t}")

    # Spot-check semantic consistency for sequence targets via decoding.
    checked = 0
    for i, rid in enumerate(base_ids):
        task = base_rows[i]["task"]
        if task not in SEQUENCE_TASKS:
            continue
        ref = base_rows[i]["target_payload"]
        for t in toks:
            pred = decode_melody_by_tokenizer(t, tables[t][i]["target"])
            if pred != ref:
                raise AssertionError(f"decode mismatch id={rid}, tokenizer={t}")
        checked += 1

    print(f"OK: id/task alignment across {len(toks)} tokenizers")
    print(f"OK: sequence target decode consistency checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
