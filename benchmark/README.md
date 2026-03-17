# Benchmark README

This folder contains a zero-shot music reasoning benchmark with tokenizer views.

Related docs:

- `docs/benchmark-user-guide.md`
- `docs/diagrams/benchmark-usage-flow.md`
- `docs/diagrams/benchmark-architecture.md`

## Scope

The benchmark currently covers 8 tasks grouped into two output families.

### Label classification tasks

- `task1_interval_identification`
- `task2_chord_identification`
- `task3_harmonic_function`
- `task8_voice_leading`

### Note-sequence transformation tasks

- `task4_transposition`
- `task5_melodic_inversion`
- `task6_retrograde`
- `task7_rhythm_scale`

No train/dev/test split is used. The benchmark is designed for zero-shot evaluation.

## Data products

1. Canonical raw set:
- `benchmark/data/raw_note_level/zero_shot.jsonl`

2. Tokenizer views:
- `benchmark/data/views/note_level/zero_shot.jsonl`
- `benchmark/data/views/midilike/zero_shot.jsonl`
- `benchmark/data/views/remilike/zero_shot.jsonl`

3. Model-ready case JSON:
- `benchmark/data/model_io/note_level/sequence_cases.json`
- `benchmark/data/model_io/midilike/sequence_cases.json`
- `benchmark/data/model_io/remilike/sequence_cases.json`
- split-by-task exports are also supported

## Canonical prediction schema

The benchmark now supports a canonical prediction schema while keeping backward compatibility with the legacy `prediction` field.

### Label tasks

Required canonical field:

- `prediction_label`

Optional field:

- `prediction_explanation`

Compatibility fallback:

- `prediction`

Example JSONL row:

```json
{"id": "task3_harmonic_function-000001", "prediction_type": "label", "prediction_label": "dominant", "prediction_explanation": "In C major, G functions as V and creates tension toward the tonic.", "prediction": "dominant"}
```

### Sequence tasks

Required canonical field:

- `prediction_notes`

Optional field:

- `prediction_structured`

Compatibility fallback:

- `prediction`

Example JSONL row:

```json
{"id": "task4_transposition-000001", "prediction_type": "notes", "prediction_notes": "t=0 d=1 notes=[62] v=80 | t=1 d=1 notes=[64] v=80", "prediction_structured": [{"t": 0.0, "p": 62, "d": 1.0, "v": 80}, {"t": 1.0, "p": 64, "d": 1.0, "v": 80}], "prediction": "t=0 d=1 notes=[62] v=80 | t=1 d=1 notes=[64] v=80"}
```

## Prompt composition rules

Prompt fields are generated in `benchmark/core/render.py` and exported by:

- `benchmark/scripts/gen_zero_shot.py`
- `benchmark/scripts/export_views.py`

Each case stores full model input as:

- `model_input.system_prompt`
- `model_input.user_prompt`

### Prompt modes

- `light`: concise prompt style
- `agent_like`: strict style aligned with the MIDI-agent philosophy

### Current `agent_like` policy

- Put hard constraints in `system_prompt`:
  - output-only rule
  - no explanation / no markdown rule
  - tokenizer grammar
  - task rule
- Keep `user_prompt` as instance data only:
  - task body
  - agent context (`bpm`, `meter`, `grid`, `bar_beats`)
  - control params (`source_key`, `target_key`, `pivot`, `factor`)
  - input sequence when relevant

## Musicology layer

The benchmark now includes an explicit musicology-facing layer for label tasks.

- `target_explanation` is generated rule-based in model-ready case exports
- `prediction_explanation` is supported as an optional model output field
- the current policy is hybrid:
  - rule-based reference explanations
  - optional model-generated prediction explanations

This allows the benchmark to keep a strict evaluable output while also supporting analytical interpretation in the paper.

## Theoretical simplifications

The benchmark intentionally uses a constrained symbolic-theory scope in V1.

- Harmonic function:
  - major mode only
  - three coarse classes: `tonic`, `predominant`, `dominant`
- Voice-leading:
  - two-voice simplification
  - labels limited to `parallel_fifths`, `voice_crossing`, and `none`
- Harmony:
  - reduced chord vocabulary
  - templates limited to `major`, `minor`, `diminished`, `augmented`, and `dominant7`
- Representation:
  - symbolic music only, not audio

These simplifications should be stated explicitly in the paper.

## Current V1 scope

The current benchmark should be presented as a V1 scope definition rather than as final theoretical coverage.

- V1 is intentionally constrained so that generation, prompting, prediction formatting, and evaluation remain reproducible
- V1 is also meant to stay understandable for non-expert users who only need a clean benchmark workflow
- the benchmark therefore focuses on a tractable symbolic subset of tonal reasoning instead of full analytical coverage

## Planned extensions

The current implementation is compatible with future expansion in at least the following directions.

- harmonic-function coverage beyond major mode
- richer voice-leading scenarios beyond two voices
- broader harmonic vocabularies and sonority types
- more analytical explanation studies built around `prediction_explanation`
- stronger paper-oriented comparisons between structural correctness and interpretive quality

## Not yet final theoretical coverage

The benchmark should not be described as exhaustive musicological coverage.

- it is a reproducible V1 benchmark slice
- it supports formal evaluation now
- it leaves room for future modal, contrapuntal, and harmonic expansion in later versions of the paper

## How to regenerate

### Sequence-only shortcut

```bash
bash scripts/run_sequence_benchmark.sh 200 agent_like
```

### Full manual flow

```bash
python3 -m benchmark.scripts.gen_zero_shot \
  --task-group all \
  --samples-per-task 200 \
  --prompt-mode agent_like \
  --out benchmark/data/raw_note_level/zero_shot.jsonl

python3 -m benchmark.scripts.export_views \
  --src benchmark/data/raw_note_level/zero_shot.jsonl \
  --prompt-mode agent_like

python3 -m benchmark.scripts.validate_views

python3 -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/note_level/zero_shot.jsonl \
  --out benchmark/data/model_io/note_level/all_cases.json \
  --task-group all \
  --pretty
```

## Evaluation

### Unified evaluator for Tasks 1-8

```bash
python3 -m benchmark.scripts.eval_predictions \
  --gold benchmark/data/views/note_level/zero_shot.jsonl \
  --pred <predictions.jsonl> \
  --out benchmark/results/eval_predictions.json \
  --overall-out benchmark/results/overall.json \
  --by-task-out benchmark/results/by_task.json \
  --by-tokenizer-out benchmark/results/by_tokenizer.json
```

### Sequence-only evaluator

```bash
python3 -m benchmark.scripts.eval_sequence_predictions \
  --gold benchmark/data/views/note_level/zero_shot.jsonl \
  --pred <predictions.jsonl> \
  --out benchmark/results/sequence_eval.json
```

## Annotated outputs and summaries

Attach model outputs to case JSON and compute:

- `hit_ground_truth`
- `match_status` / `match_detail`
- text-level TER / CER
- note-event error rate for sequence tasks
- overall and by-task summaries
- optional `prediction_explanation` preservation in annotated outputs

```bash
python3 -m benchmark.scripts.annotate_model_outputs \
  --cases benchmark/data/model_io/note_level/all_cases.json \
  --pred <predictions.jsonl> \
  --out benchmark/results/cases_with_outputs.json \
  --summary-out benchmark/results/summary.json \
  --pretty
```

## Batch testing

### Ollama

```bash
python3 -m benchmark.scripts.run_ollama_model_list \
  --cases-list benchmark/data/model_io/note_level/all_cases.json,benchmark/data/model_io/midilike/all_cases.json \
  --models qwen2.5:3b,qwen2.5:7b \
  --out-dir benchmark/results/ollama_multi
```

### Ollama suite wrapper

```bash
bash benchmark/scripts/run_ollama_bench_suite.sh
```

### API models

```bash
python3 -m benchmark.scripts.run_api_model_list \
  --cases benchmark/data/model_io/note_level/all_cases.json \
  --models gpt-4o-mini \
  --out-dir benchmark/results/api
```

## Change rule

When prompt composition logic, prediction schema, or evaluation logic changes, update this README in the same commit.

## Files that define behavior

- `benchmark/core/render.py`
- `benchmark/core/rules.py`
- `benchmark/core/task_specs.py`
- `benchmark/core/predictions.py`
- `benchmark/core/musicology.py`
- `benchmark/tokenizers.py`
- `benchmark/scripts/gen_zero_shot.py`
- `benchmark/scripts/export_views.py`
- `benchmark/scripts/validate_views.py`
- `benchmark/scripts/build_model_io_json.py`
- `benchmark/scripts/eval_predictions.py`
- `benchmark/scripts/eval_sequence_predictions.py`
- `benchmark/scripts/annotate_model_outputs.py`
- `benchmark/scripts/run_ollama_model_list.py`
- `benchmark/scripts/run_api_model_list.py`
