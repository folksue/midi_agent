# Project TODO

This file is the project's working memory.

## Immediate goal

We are going to implement and close the following points:

- canonical prediction interface:
  - `prediction_label` for Tasks 1, 2, 3, and 8
  - `prediction_notes` for Tasks 4, 5, 6, and 7
  - `prediction_structured` as an optional field for Tasks 4, 5, 6, and 7
- unified evaluator for all 8 tasks
- adaptation of `build_model_io_json.py` for classification tasks
- explicit musicology layer
- clear documentation of the theoretical simplifications

## Current repository state

- The benchmark already generates all 8 tasks with rules in `benchmark/scripts/gen_zero_shot.py`.
- The most mature part of the current pipeline is centered on Tasks 4-7.
- Tasks 1-3 and 8 already exist at the generation level, but they still do not have an equally complete evaluation and documentation pipeline.
- The current output interface relies too much on a generic `prediction` field and melody-oriented fields.

## Pending work

### 1. Canonical prediction interface

- [x] Add `prediction_type` with the following values:
  - `label`
  - `notes`
- [x] Add `prediction_label` for Tasks 1, 2, 3, and 8
- [x] Add `prediction_notes` for Tasks 4, 5, 6, and 7
- [x] Add `prediction_structured` as an optional structured output for sequence tasks
- [x] Keep backward compatibility with the current `prediction` field

Compatibility rule:

- For classification tasks, the evaluator should read `prediction_label` first and fall back to `prediction` if needed.
- For sequence tasks, the evaluator should read `prediction_notes` first and fall back to `prediction` if needed.

### 2. Unified evaluator for all 8 tasks

- [x] Create `benchmark/scripts/eval_predictions.py`
- [x] Unify evaluation for Tasks 1-8
- [x] Keep `eval_sequence_predictions.py` if it remains useful as a task-specific script

Minimum metrics:

- Task 1: exact match accuracy
- Task 2: exact match accuracy
- Task 3: accuracy and macro F1
- Task 4: exact match, pitch accuracy, interval preservation, rhythm preservation
- Task 5: exact match and pitch accuracy
- Task 6: exact match
- Task 7: exact match, duration accuracy, bar validity
- Task 8: accuracy and macro F1

Minimum outputs:

- [ ] `overall.json`
- [ ] `by_task.json`
- [ ] `by_tokenizer.json`

### 3. Adapt `build_model_io_json.py`

Current problem:

- it is currently too melody-oriented
- it uses fields such as `melody_input_tokens` and `melody_target_tokens`

Work needed:

- [x] add clean support for classification tasks
- [x] add prediction-type metadata
- [x] add task-aware packaging

Suggested fields:

- `prediction_kind`
- `input_label_context`
- `expected_label_space`

### 4. Explicit musicology layer

Current problem:

- the repository already encodes music theory
- but it still does not respond in analytical or musicological language

Work needed:

- [x] define an explanation layer for classification tasks
- [x] decide whether that explanation will be:
  - rule-based
  - model-generated
  - hybrid
- [x] clearly separate:
  - evaluable output
  - optional musicological explanation

Suggested fields:

- `prediction_explanation`
- `target_explanation` for references or paper examples

Current decision:

- explanation policy is hybrid
- V1 provides rule-based reference explanations
- model outputs may optionally include `prediction_explanation`

### 5. Document theoretical simplifications

- [x] document that harmonic function is limited to major mode in this version
- [x] document that voice-leading is simplified to two voices
- [x] document that the current harmonic vocabulary is reduced
- [ ] indicate whether these decisions are temporary or part of the paper's intended scope

### 6. Update benchmark documentation

- [x] document the new prediction schema
- [x] document the use of `eval_predictions.py`
- [x] add a JSONL prediction example
- [x] add a non-expert user guide and diagrams
- [ ] add secondary documentation so the project is more paper-ready and easier to hand off to other users
- [ ] update any remaining secondary benchmark docs if needed

### 7. Add benchmark-specific tests

- [x] add tests for `task_specs.py`
- [x] add tests for `predictions.py`
- [x] add tests for `eval_predictions.py`
- [x] add tests for the musicology explanation layer

## What to reuse without changing too much

These parts can be reused directly:

- `benchmark/scripts/gen_zero_shot.py`
- `benchmark/core/rules.py`
- `benchmark/core/render.py`
- `benchmark/tokenizers.py`
- `benchmark/scripts/export_views.py`
- `benchmark/scripts/validate_views.py`
- `benchmark/scripts/run_api_model_list.py`
- `benchmark/scripts/run_ollama_model_list.py`
- `benchmark/scripts/annotate_model_outputs.py`

## Recommended implementation order

- [x] Step 1: standardize the prediction interface
- [x] Step 2: adapt `build_model_io_json.py`
- [x] Step 3: implement a unified evaluator for all 8 tasks
- [x] Step 4: add the musicological explanation layer
- [ ] Step 5: update benchmark and paper documentation

## Useful notes

- The current benchmark already provides a strong foundation for symbolic music and operationalized music theory.
- What is missing is not a full rewrite of the repository, but a more complete interface, evaluation layer, and musicological framing.
