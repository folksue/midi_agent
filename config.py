from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class RuntimeConfig:
    bpm: int = 120
    meter_num: int = 4
    meter_den: int = 4
    grid_str: str = "1/16"
    total_bars: int = 8
    lookahead_bars: int = 2
    request_bars_per_call: int = int(os.getenv("MIDI_AGENT_REQUEST_BARS_PER_CALL", "4"))
    play_mode: str = os.getenv("MIDI_AGENT_PLAY_MODE", "realtime_window")
    single_shot_max_bars: int = int(os.getenv("MIDI_AGENT_SINGLE_SHOT_MAX_BARS", "64"))
    enable_llm_end_signal: bool = _env_bool("MIDI_AGENT_ENABLE_LLM_END_SIGNAL", True)
    warmup_sec: float = 0.2
    max_regen_attempts: int = 3
    events_per_bar_limit: int = 32
    midi_port_name: str = "MidiAgentOut"
    midi_virtual: bool = True
    metrics_path: str = os.getenv("MIDI_AGENT_METRICS_PATH", "metrics.jsonl")
    save_success_midi: bool = _env_bool("MIDI_AGENT_SAVE_SUCCESS_MIDI", True)
    success_midi_dir: str = os.getenv("MIDI_AGENT_SUCCESS_MIDI_DIR", "/tmp/midi_agent_success_midi")


DEFAULT_CONFIG = RuntimeConfig()


def grid_step_beats(grid_str: str) -> float:
    # In this DSL, time unit is beats where quarter note = 1 beat.
    # 1/16 note therefore equals 0.25 beats.
    if grid_str == "1/16":
        return 0.25
    if grid_str == "1/8":
        return 0.5
    if grid_str == "1/4":
        return 1.0
    raise ValueError(f"Unsupported grid: {grid_str}")
