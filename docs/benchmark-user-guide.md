# Benchmark User Guide

This guide is the simplest end-to-end path for running, testing, and understanding the symbolic music benchmark.

Related notebook:

- `symbolic-music-benchmark-review.ipynb`

## Who this is for

This guide is intended for users who are not experts in the internal codebase.

The benchmark has two usage modes:

- `standard`: the default mode, simple and fully automatically evaluable
- `explanatory`: an optional mode for qualitative analysis and paper-oriented interpretation

## Standard workflow

If you want the simplest wrapper for non-expert users, you can start with:

```bash
bash scripts/run_standard_benchmark.sh 200 agent_like none
```

That prepares the full benchmark and prints the next commands for running a model.

### 1. Generate benchmark data

```bash
python3 -m benchmark.scripts.gen_zero_shot \
  --task-group all \
  --samples-per-task 200 \
  --prompt-mode agent_like \
  --out benchmark/data/raw_note_level/zero_shot.jsonl
```

### 2. Export tokenizer views

```bash
python3 -m benchmark.scripts.export_views \
  --src benchmark/data/raw_note_level/zero_shot.jsonl \
  --prompt-mode agent_like
```

### 3. Validate tokenizer consistency

```bash
python3 -m benchmark.scripts.validate_views
```

### 4. Build model-ready cases

```bash
python3 -m benchmark.scripts.build_model_io_json \
  --src benchmark/data/views/note_level/zero_shot.jsonl \
  --out benchmark/data/model_io/note_level/all_cases.json \
  --task-group all \
  --pretty
```

### 5. Run a model

#### OpenAI-compatible API

```bash
python3 -m benchmark.scripts.run_api_model_list \
  --cases benchmark/data/model_io/note_level/all_cases.json \
  --models gpt-4o-mini \
  --out-dir benchmark/results/api
```

#### Ollama

```bash
python3 -m benchmark.scripts.run_ollama_model_list \
  --cases benchmark/data/model_io/note_level/all_cases.json \
  --models qwen2.5:7b \
  --out-dir benchmark/results/ollama
```

### 6. Evaluate predictions

```bash
python3 -m benchmark.scripts.eval_predictions \
  --gold benchmark/data/views/note_level/zero_shot.jsonl \
  --pred benchmark/results/api/pred_gpt-4o-mini.jsonl \
  --out benchmark/results/eval_predictions.json \
  --overall-out benchmark/results/overall.json \
  --by-task-out benchmark/results/by_task.json \
  --by-tokenizer-out benchmark/results/by_tokenizer.json
```

### 7. Attach outputs and review examples

```bash
python3 -m benchmark.scripts.annotate_model_outputs \
  --cases benchmark/data/model_io/note_level/all_cases.json \
  --pred benchmark/results/api/pred_gpt-4o-mini.jsonl \
  --out benchmark/results/cases_with_outputs.json \
  --summary-out benchmark/results/summary.json \
  --pretty
```

## Prediction file format

### Standard mode

For label tasks:

```json
{"id": "task3_harmonic_function-000001", "prediction_type": "label", "prediction_label": "dominant", "prediction": "dominant"}
```

For sequence tasks:

```json
{"id": "task4_transposition-000001", "prediction_type": "notes", "prediction_notes": "t=0 d=1 notes=[62] v=80 | t=1 d=1 notes=[64] v=80", "prediction_structured": [{"t": 0.0, "p": 62, "d": 1.0, "v": 80}, {"t": 1.0, "p": 64, "d": 1.0, "v": 80}], "prediction": "t=0 d=1 notes=[62] v=80 | t=1 d=1 notes=[64] v=80"}
```

### Explanatory mode

The explanatory mode keeps the same main output but may add:

```json
{"id": "task3_harmonic_function-000001", "prediction_type": "label", "prediction_label": "dominant", "prediction_explanation": "In C major, G functions as V and creates tension toward the tonic.", "prediction": "dominant"}
```

Important:

- the standard evaluator scores the main prediction
- `prediction_explanation` is supplementary
- `prediction_explanation` is preserved in annotated outputs for qualitative analysis

## What files to inspect

After a normal run, the most useful files are:

- `benchmark/data/model_io/note_level/all_cases.json`
- `benchmark/results/eval_predictions.json`
- `benchmark/results/overall.json`
- `benchmark/results/by_task.json`
- `benchmark/results/by_tokenizer.json`
- `benchmark/results/cases_with_outputs.json`
- `benchmark/results/summary.json`

## What standard users should do

If the user only wants a reliable benchmark run:

- generate cases
- run a model
- evaluate with `eval_predictions.py`

They do not need to provide explanations.

## What paper-oriented users should do

If the user wants qualitative material for a paper:

- run the same benchmark
- optionally include `prediction_explanation` for label tasks
- inspect `cases_with_outputs.json`
- compare structural correctness against analytical explanation quality
