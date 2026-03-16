#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.core.render import render_input, render_system_prompt, render_target, render_user_prompt

TOKENIZERS = ["note_level", "midilike", "remilike"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export benchmark views for multiple tokenizers.")
    p.add_argument("--src", default="benchmark/data/raw_note_level/zero_shot.jsonl")
    p.add_argument("--out-dir", default="benchmark/data/views")
    p.add_argument("--tokenizers", default=",".join(TOKENIZERS))
    p.add_argument(
        "--prompt-mode",
        choices=["light", "agent_like"],
        default="",
        help="Override prompt mode for exported views. Empty means inherit from source meta.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    src = Path(args.src)
    if not src.exists():
        raise FileNotFoundError(src)

    tokenizers = [t.strip() for t in args.tokenizers.split(",") if t.strip()]
    rows = [json.loads(x) for x in src.read_text(encoding="utf-8").splitlines() if x.strip()]

    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    for tok in tokenizers:
        out_path = out_root / tok / "zero_shot.jsonl"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for r in rows:
                task = r["task"]
                payload = r["payload"]
                target_payload = r["target_payload"]
                input_text = render_input(task, payload, tokenizer=tok)
                target_text = render_target(task, target_payload, tokenizer=tok)
                out = {
                    "id": r["id"],
                    "task": task,
                    "input": input_text,
                    "target": target_text,
                    "input_tokenized": input_text,
                    "output_tokenized": target_text,
                    "system_prompt": render_system_prompt(
                        task,
                        tokenizer=tok,
                        prompt_mode=args.prompt_mode or r.get("meta", {}).get("prompt_mode", "light"),
                    ),
                    "user_prompt": render_user_prompt(
                        task,
                        payload,
                        tokenizer=tok,
                        prompt_mode=args.prompt_mode or r.get("meta", {}).get("prompt_mode", "light"),
                    ),
                    "ground_truth": target_text,
                    "payload": payload,
                    "target_payload": target_payload,
                    "meta": {
                        **r.get("meta", {}),
                        "tokenizer": tok,
                        "prompt_mode": args.prompt_mode or r.get("meta", {}).get("prompt_mode", "light"),
                    },
                }
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
        print(f"exported: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
