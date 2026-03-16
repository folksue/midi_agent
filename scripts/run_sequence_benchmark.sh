#!/usr/bin/env bash
set -euo pipefail

SAMPLES_PER_TASK="${1:-100}"
PROMPT_MODE="${2:-agent_like}"

python -m benchmark.scripts.gen_zero_shot \
  --task-group sequence \
  --samples-per-task "${SAMPLES_PER_TASK}" \
  --prompt-mode "${PROMPT_MODE}" \
  --out benchmark/data/raw_note_level/zero_shot_sequence.jsonl

python -m benchmark.scripts.export_views \
  --src benchmark/data/raw_note_level/zero_shot_sequence.jsonl \
  --prompt-mode "${PROMPT_MODE}"

python -m benchmark.scripts.validate_views

python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/note_level/zero_shot.jsonl \
  --out benchmark/data/model_io/note_level/sequence_cases.json \
  --task-group sequence \
  --pretty
python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/note_level/zero_shot.jsonl \
  --out benchmark/data/model_io/note_level/sequence_cases.json \
  --task-group sequence \
  --split-by-task \
  --out-dir benchmark/data/model_io/note_level/by_task \
  --pretty

python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/midilike/zero_shot.jsonl \
  --out benchmark/data/model_io/midilike/sequence_cases.json \
  --task-group sequence \
  --pretty
python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/midilike/zero_shot.jsonl \
  --out benchmark/data/model_io/midilike/sequence_cases.json \
  --task-group sequence \
  --split-by-task \
  --out-dir benchmark/data/model_io/midilike/by_task \
  --pretty

python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/remilike/zero_shot.jsonl \
  --out benchmark/data/model_io/remilike/sequence_cases.json \
  --task-group sequence \
  --pretty
python -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/remilike/zero_shot.jsonl \
  --out benchmark/data/model_io/remilike/sequence_cases.json \
  --task-group sequence \
  --split-by-task \
  --out-dir benchmark/data/model_io/remilike/by_task \
  --pretty

echo "[ok] sequence benchmark data ready"
echo "gold view: benchmark/data/views/note_level/zero_shot.jsonl"
echo "cases json: benchmark/data/model_io/<tokenizer>/sequence_cases.json"
echo "prompt mode: ${PROMPT_MODE}"
echo "Then run: python -m benchmark.scripts.eval_sequence_predictions --gold benchmark/data/views/note_level/zero_shot.jsonl --pred <pred.jsonl>"
