# Benchmark README

This folder contains a zero-shot music reasoning benchmark with tokenizer views.

## Scope
Current benchmark supports:
- Label tasks:
  - `task1_interval_identification`
  - `task2_chord_identification`
  - `task3_harmonic_function`
  - `task8_voice_leading`
- Sequence transformation tasks:
- `task4_transposition`
- `task5_melodic_inversion`
- `task6_retrograde`
- `task7_rhythm_scale`

No train/dev/test split is used.

## Data Products
1. Canonical raw set (note-level):
- `benchmark/data/raw_note_level/zero_shot_sequence.jsonl`

2. Tokenizer views:
- `benchmark/data/views/note_level/zero_shot.jsonl`
- `benchmark/data/views/midilike/zero_shot.jsonl`
- `benchmark/data/views/remilike/zero_shot.jsonl`

3. Model-ready case JSON (prompt + GT):
- `benchmark/data/model_io/note_level/sequence_cases.json`
- `benchmark/data/model_io/midilike/sequence_cases.json`
- `benchmark/data/model_io/remilike/sequence_cases.json`
- By-task split files are also supported (one file per task):
  - `benchmark/data/model_io/<tokenizer>/by_task/task4_transposition.json`
  - `benchmark/data/model_io/<tokenizer>/by_task/task5_melodic_inversion.json`
  - `benchmark/data/model_io/<tokenizer>/by_task/task6_retrograde.json`
  - `benchmark/data/model_io/<tokenizer>/by_task/task7_rhythm_scale.json`

## Prompt Composition Rules
Prompt fields are generated in `benchmark/core/render.py` and exported by `benchmark/scripts/gen_zero_shot.py` + `benchmark/scripts/export_views.py`.

Each case stores full model input as:
- `model_input.system_prompt`
- `model_input.user_prompt`

### Prompt modes
- `light`: concise prompt style.
- `agent_like`: strict style (recommended), aligned with MIDI-agent philosophy.

### Current `agent_like` policy (clean version)
- Put **all hard constraints** in `system_prompt`:
  - output-only rule
  - no explanation/markdown rule
  - tokenizer grammar
  - task rule (what to transform / what to preserve)
- Keep `user_prompt` as **instance data only**:
  - task question body
  - agent context (`bpm/meter/grid/bar_beats`)
  - control params (`source_key/target_key/pivot/factor`)
  - `melody=...`

## Prompt Example (agent_like, note_level, Task4)

### System prompt
```text
You are a strict music token transformation generator.
Rules:
1) Output ONLY the transformed melody tokens.
2) No explanations, no markdown, no extra text.
3) Output melody tokens with grammar: n<PITCH>/<DURATION> separated by single spaces.
Example: t=0.00 d=0.50 notes=[60] v=80 | t=0.50 d=0.50 notes=[62] v=80
Use decimal numbers only (NOT fraction like 1/4).
4) Transform pitch by key shift; keep note count/order/durations unchanged.
5) If unsure, output fewer valid tokens over invalid format.
```

### User prompt
```text
Transposition
bpm=120 meter=4/4 grid=1/16 bar_beats=4.0
source_key=C_major target_key=G_major
melody=t=0 d=0.5 notes=[62] v=80 | t=0.5 d=0.25 notes=[70] v=80 | ...
```

## How To Regenerate

### Label tasks (Task 1/2/3/8)
```bash
bash scripts/run_label_benchmark.sh 200 agent_like
```

### Recommended one-command flow
```bash
bash scripts/run_sequence_benchmark.sh 200 agent_like
```

### Manual flow
```bash
python -m benchmark.scripts.gen_zero_shot \
  --task-group sequence \
  --samples-per-task 200 \
  --prompt-mode agent_like \
  --out benchmark/data/raw_note_level/zero_shot_sequence.jsonl

python -m benchmark.scripts.export_views \
  --src benchmark/data/raw_note_level/zero_shot_sequence.jsonl \
  --prompt-mode agent_like

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
```

## Evaluation
Label tasks:
```bash
python -m benchmark.scripts.eval_label_predictions \
  --gold benchmark/data/views/note_level/zero_shot.jsonl \
  --pred <predictions.jsonl> \
  --out benchmark/results/label_eval.json
```

Sequence tasks:
```bash
python -m benchmark.scripts.eval_sequence_predictions \
  --gold benchmark/data/views/note_level/zero_shot.jsonl \
  --pred <predictions.jsonl> \
  --out benchmark/results/sequence_eval.json
```

## Annotated Outputs And Accuracy

Attach model outputs to case JSON and compute:
- `hit_ground_truth`
- `match_status` / `match_detail`
- text-level TER/CER
- note-event error rate (sequence tasks)
- overall and by-task summary

```bash
python -m benchmark.scripts.annotate_model_outputs \
  --cases benchmark/data/model_io/note_level/sequence_cases.json \
  --pred <predictions.jsonl> \
  --out benchmark/results/cases_with_outputs.json \
  --summary-out benchmark/results/summary.json \
  --pretty
```

## Batch Testing (Model Lists)

Ollama:
```bash
python -m benchmark.scripts.run_ollama_model_list \
  --cases-list benchmark/data/model_io/note_level/sequence_cases.json,benchmark/data/model_io/midilike/sequence_cases.json \
  --models qwen2.5:3b,qwen2.5:7b \
  --out-dir benchmark/results/ollama_multi
```

Ollama suite wrapper:
```bash
bash benchmark/scripts/run_ollama_bench_suite.sh
```

API models:
```bash
python -m benchmark.scripts.run_api_model_list \
  --cases benchmark/data/model_io/note_level/sequence_cases.json \
  --models gpt-4o-mini \
  --out-dir benchmark/results/api
```

## Change Rule (for future prompt updates)
When prompt composition logic changes, update **this README** in the same commit:
1. Update `Prompt Composition Rules` section.
2. Update `Prompt Example` with one current real example.
3. Mention affected files.

## Files That Define Behavior
- `benchmark/core/render.py` (prompt rules)
- `benchmark/tokenizers.py` (token grammar rendering)
- `benchmark/scripts/gen_zero_shot.py` (raw generation)
- `benchmark/scripts/export_views.py` (tokenizer view export)
- `benchmark/scripts/build_model_io_json.py` (model-ready JSON export)
- `benchmark/scripts/annotate_model_outputs.py` (hit + error metrics + by-task summary)
- `benchmark/scripts/run_ollama_model_list.py` (Ollama model-list batch runner)
- `benchmark/scripts/run_api_model_list.py` (API model-list batch runner)
