# Note Sequence Transformation Benchmark (Task 4-7)

## Scope
Only these 4 tasks:
- `task4_transposition`
- `task5_melodic_inversion`
- `task6_retrograde`
- `task7_rhythm_scale`

No train/dev/test split. This is for zero-shot evaluation.

## 1) Generate canonical note-level set
```bash
python -m benchmark.scripts.gen_zero_shot \
  --task-group sequence \
  --samples-per-task 200 \
  --prompt-mode agent_like \
  --out benchmark/data/raw_note_level/zero_shot_sequence.jsonl
```

## 2) Export tokenizer views
```bash
python -m benchmark.scripts.export_views \
  --src benchmark/data/raw_note_level/zero_shot_sequence.jsonl \
  --prompt-mode agent_like
```

Generated files:
- `benchmark/data/views/note_level/zero_shot.jsonl`
- `benchmark/data/views/midilike/zero_shot.jsonl`
- `benchmark/data/views/remilike/zero_shot.jsonl`

The sequence payload is agent-aligned event format (`t,d,p,v`) and includes:
- `bpm`
- `meter`
- `grid`
- `bar_beats`

## 3) Run model and save predictions
Prediction file format (jsonl):
```json
{"id": "task4_transposition-000001", "prediction": "..."}
```

## 4) Evaluate (sequence-only metrics)
```bash
python -m benchmark.scripts.eval_sequence_predictions \
  --gold benchmark/data/views/note_level/zero_shot.jsonl \
  --pred /path/to/your_predictions.jsonl \
  --out benchmark/results/sequence_eval.json
```

## Metrics
- Common (Task 4-7):
  - `exact_match`
  - `pitch_accuracy`
  - `duration_accuracy`
- Task 4 extra:
  - `interval_preservation_rate`
  - `rhythm_preservation_rate`
- Task 7 extra:
  - `bar_validity_rate`
