#!/usr/bin/env bash
set -euo pipefail

SAMPLES_PER_TASK="${1:-100}"
PROMPT_MODE="${2:-agent_like}"

python -m benchmark.scripts.gen_zero_shot \
  --task-group label \
  --samples-per-task "${SAMPLES_PER_TASK}" \
  --prompt-mode "${PROMPT_MODE}" \
  --out benchmark/data/raw_note_level/zero_shot_label.jsonl

python -m benchmark.scripts.export_views \
  --src benchmark/data/raw_note_level/zero_shot_label.jsonl \
  --prompt-mode "${PROMPT_MODE}"

python -m benchmark.scripts.validate_views

python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/note_level/zero_shot.jsonl \
  --out benchmark/data/model_io/note_level/label_cases.json \
  --task-group label \
  --pretty

python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/midilike/zero_shot.jsonl \
  --out benchmark/data/model_io/midilike/label_cases.json \
  --task-group label \
  --pretty

python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/remilike/zero_shot.jsonl \
  --out benchmark/data/model_io/remilike/label_cases.json \
  --task-group label \
  --pretty

echo "[ok] label benchmark data ready"
echo "gold view: benchmark/data/views/note_level/zero_shot.jsonl"
echo "cases json: benchmark/data/model_io/<tokenizer>/label_cases.json"
echo "prompt mode: ${PROMPT_MODE}"
echo "Then run: python -m benchmark.scripts.eval_label_predictions --gold benchmark/data/views/note_level/zero_shot.jsonl --pred <pred.jsonl>"
