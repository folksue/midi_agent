# MIDI Agent (Realtime + Benchmark)

This repo contains:
- A realtime MIDI agent CLI (`python -m midi_agent`)
- A benchmark toolkit for zero-shot music transformation testing

## Realtime Agent

Core runtime entry:
- `python -m midi_agent`

CLI commands:
- `/play <style>`
- `/continue`
- `/stop`
- `/quit`

### Agent Modes

Configured by env var `MIDI_AGENT_PLAY_MODE`:

- `realtime_window` (default)
  - Requests multiple bars per call (`MIDI_AGENT_REQUEST_BARS_PER_CALL`, default `4`)
  - Schedules chunks bar-by-bar
  - Supports optional LLM end signal `@end` when `MIDI_AGENT_ENABLE_LLM_END_SIGNAL=1`

- `single_shot_full`
  - Requests one large batch once (`MIDI_AGENT_SINGLE_SHOT_MAX_BARS`, default `64`)
  - Plays returned chunks and auto-stops when queue drains

### Protocol Notes

- Chunk format stays explicit:
  - `@chunk from_bar=K to_bar=K`
  - `t=... d=... notes=[...] v=...`
  - `@eochunk`
- Recommended to keep `@chunk/@eochunk` delimiters for robust parsing/recovery.
- Optional end marker after final chunk:
  - `@end`

## Benchmark

See:
- `benchmark/README.md`

Quick run:
- `bash scripts/run_sequence_benchmark.sh 200 agent_like`

Batch inference:
- Ollama list runner:
  - `python -m benchmark.scripts.run_ollama_model_list ...`
- Ollama suite shell wrapper:
  - `bash benchmark/scripts/run_ollama_bench_suite.sh`
- API list runner:
  - `python -m benchmark.scripts.run_api_model_list ...`

