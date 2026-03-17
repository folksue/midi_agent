#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from benchmark.core.render import render_input, render_system_prompt, render_target, render_user_prompt
from benchmark.core.task_specs import TASK_GROUPS
from benchmark.core.rules import (
    CHORD_TEMPLATES,
    chord_label_from_root_quality,
    harmonic_function_major,
    has_parallel_fifths,
    has_voice_crossing,
    interval_label,
    invert_melody,
    make_random_melody,
    pc_name,
    retrograde_melody,
    rhythm_scale_melody,
    to_note_dicts,
    transpose_melody,
)

DEFAULT_AGENT_CTX = {
    "bpm": 120,
    "meter": "4/4",
    "grid": "1/16",
    "bar_beats": 4.0,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate zero-shot benchmark (note_level canonical).")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--samples-per-task", type=int, default=200)
    p.add_argument(
        "--task-group",
        choices=sorted(TASK_GROUPS.keys()),
        default="all",
        help="Generate only a task group.",
    )
    p.add_argument(
        "--tasks",
        default="",
        help="Comma-separated task ids. If set, overrides --task-group.",
    )
    p.add_argument(
        "--out",
        default="benchmark/data/raw_note_level/zero_shot.jsonl",
    )
    p.add_argument(
        "--prompt-mode",
        choices=["light", "agent_like"],
        default="light",
        help="Prompt strictness profile for model-facing fields.",
    )
    return p.parse_args()


def _with_agent_time_context(payload: dict) -> dict:
    out = dict(payload)
    for k, v in DEFAULT_AGENT_CTX.items():
        out.setdefault(k, v)
    return out


def _make_bar_melody(
    rng: random.Random,
    *,
    total_beats: float,
    min_notes: int,
    max_notes: int,
    duration_pool: tuple[float, ...],
) -> list[dict]:
    # Build monophonic melody whose durations sum to total_beats exactly.
    for _ in range(200):
        n_notes = rng.randint(min_notes, max_notes)
        ds: list[float] = []
        remain = total_beats
        ok = True
        for i in range(n_notes):
            slots_left = n_notes - i - 1
            candidates = []
            for d in duration_pool:
                if d > remain + 1e-9:
                    continue
                # Ensure the remaining beats can still be filled by min duration.
                min_possible = slots_left * min(duration_pool)
                max_possible = slots_left * max(duration_pool)
                rem_after = remain - d
                if min_possible - 1e-9 <= rem_after <= max_possible + 1e-9:
                    candidates.append(d)
            if not candidates:
                ok = False
                break
            d = rng.choice(candidates)
            ds.append(d)
            remain -= d
        if not ok or abs(remain) > 1e-9:
            continue
        melody = [{"p": rng.randint(60, 72), "d": float(d)} for d in ds]
        return melody
    raise RuntimeError("failed to generate bar melody")


def _notes_to_events(melody: list[dict], velocity: int = 80) -> list[dict]:
    t = 0.0
    out: list[dict] = []
    for n in melody:
        d = float(n["d"])
        out.append({"t": round(t, 6), "p": int(n["p"]), "d": round(d, 6), "v": int(velocity)})
        t += d
    return out


def gen_task1(rng: random.Random) -> tuple[dict, str]:
    n1 = rng.randint(48, 72)
    semis = rng.choice([1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12])
    n2 = n1 + semis
    payload = {"notes": [n1, n2]}
    target = interval_label(n1, n2)
    return payload, target


def gen_task2(rng: random.Random) -> tuple[dict, str]:
    quality = rng.choice(["major", "minor", "diminished", "augmented", "dominant7"])
    root_pc = rng.randint(0, 11)
    root_midi = 60 + root_pc
    notes = [root_midi + x for x in CHORD_TEMPLATES[quality]]
    payload = {"notes": notes}
    target = chord_label_from_root_quality(root_pc, quality)
    return payload, target


def gen_task3(rng: random.Random) -> tuple[dict, str]:
    key_root_pc = rng.choice([0, 2, 4, 5, 7, 9, 11])
    degree = rng.choice([0, 2, 4, 5, 7, 9, 11])
    chord_root_pc = (key_root_pc + degree) % 12
    if degree == 11:
        quality = "diminished"
    elif degree in {0, 5, 7}:
        quality = "major"
    else:
        quality = "minor"
    payload = {
        "key": f"{pc_name(key_root_pc)}_major",
        "chord": chord_label_from_root_quality(chord_root_pc, quality),
    }
    target = harmonic_function_major(key_root_pc, chord_root_pc, quality)
    return payload, target


def gen_task4(rng: random.Random) -> tuple[dict, list[dict]]:
    melody = _make_bar_melody(
        rng,
        total_beats=4.0,
        min_notes=4,
        max_notes=8,
        duration_pool=(0.25, 0.5, 1.0),
    )
    src_key = rng.choice([0, 2, 4, 5, 7, 9, 11])
    tgt_key = rng.choice([0, 2, 4, 5, 7, 9, 11])
    shift = tgt_key - src_key
    src_events = _notes_to_events(melody)
    tgt_events = _notes_to_events([{"p": int(n["p"]) + shift, "d": float(n["d"])} for n in melody])
    payload = {
        "source_key": f"{pc_name(src_key)}_major",
        "target_key": f"{pc_name(tgt_key)}_major",
        "melody": src_events,
    }
    return _with_agent_time_context(payload), tgt_events


def gen_task5(rng: random.Random) -> tuple[dict, list[dict]]:
    melody = _make_bar_melody(
        rng,
        total_beats=4.0,
        min_notes=4,
        max_notes=8,
        duration_pool=(0.25, 0.5, 1.0),
    )
    pivot = rng.randint(58, 72)
    src_events = _notes_to_events(melody)
    tgt_events = _notes_to_events([{"p": 2 * pivot - int(n["p"]), "d": float(n["d"])} for n in melody])
    payload = {"pivot": pivot, "melody": src_events}
    return _with_agent_time_context(payload), tgt_events


def gen_task6(rng: random.Random) -> tuple[dict, list[dict]]:
    melody = _make_bar_melody(
        rng,
        total_beats=4.0,
        min_notes=4,
        max_notes=8,
        duration_pool=(0.25, 0.5, 1.0),
    )
    src_events = _notes_to_events(melody)
    tgt_events = _notes_to_events(list(reversed(melody)))
    payload = {"melody": src_events}
    return _with_agent_time_context(payload), tgt_events


def gen_task7(rng: random.Random) -> tuple[dict, list[dict]]:
    factor = rng.choice([0.5, 2.0])
    # Keep scaled output on 0.25 beat grid to stay aligned with agent constraints.
    if factor == 0.5:
        melody = _make_bar_melody(
            rng,
            total_beats=4.0,
            min_notes=4,
            max_notes=8,
            duration_pool=(0.5, 1.0),
        )
    else:
        melody = _make_bar_melody(
            rng,
            total_beats=2.0,
            min_notes=4,
            max_notes=8,
            duration_pool=(0.25, 0.5),
        )
    src_events = _notes_to_events(melody)
    scaled = [{"p": int(n["p"]), "d": round(float(n["d"]) * factor, 6)} for n in melody]
    tgt_events = _notes_to_events(scaled)
    payload = {"factor": factor, "melody": src_events}
    return _with_agent_time_context(payload), tgt_events


def gen_task8(rng: random.Random) -> tuple[dict, str]:
    label = rng.choice(["parallel_fifths", "voice_crossing", "none"])

    if label == "parallel_fifths":
        v1_t0 = rng.randint(60, 67)
        v2_t0 = v1_t0 + 7
        step = rng.choice([1, 2])
        v1_t1 = v1_t0 + step
        v2_t1 = v2_t0 + step
    elif label == "voice_crossing":
        high_t0 = rng.randint(67, 74)
        low_t0 = high_t0 - rng.randint(5, 12)
        high_t1 = rng.randint(60, 66)
        low_t1 = high_t1 + rng.randint(1, 5)
        v1_t0, v2_t0, v1_t1, v2_t1 = high_t0, low_t0, high_t1, low_t1
    else:
        v1_t0 = rng.randint(64, 72)
        v2_t0 = v1_t0 - rng.randint(5, 12)
        v1_t1 = v1_t0 + rng.choice([-2, -1, 1, 2])
        v2_t1 = v2_t0 + rng.choice([-2, -1, 1, 2])
        if has_parallel_fifths(v1_t0, v2_t0, v1_t1, v2_t1) or has_voice_crossing(v1_t1, v2_t1):
            v2_t1 = min(v1_t1 - 1, v2_t0)

    payload = {"voices_t0": [v1_t0, v2_t0], "voices_t1": [v1_t1, v2_t1]}

    if has_parallel_fifths(v1_t0, v2_t0, v1_t1, v2_t1):
        target = "parallel_fifths"
    elif has_voice_crossing(v1_t1, v2_t1):
        target = "voice_crossing"
    else:
        target = "none"
    return payload, target


def gen_one(task: str, rng: random.Random):
    if task == "task1_interval_identification":
        return gen_task1(rng)
    if task == "task2_chord_identification":
        return gen_task2(rng)
    if task == "task3_harmonic_function":
        return gen_task3(rng)
    if task == "task4_transposition":
        return gen_task4(rng)
    if task == "task5_melodic_inversion":
        return gen_task5(rng)
    if task == "task6_retrograde":
        return gen_task6(rng)
    if task == "task7_rhythm_scale":
        return gen_task7(rng)
    if task == "task8_voice_leading":
        return gen_task8(rng)
    raise ValueError(task)


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)
    selected_tasks = [t.strip() for t in args.tasks.split(",") if t.strip()] or list(TASK_GROUPS[args.task_group])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        idx = 0
        for task in selected_tasks:
            for _ in range(args.samples_per_task):
                payload, target_payload = gen_one(task, rng)
                input_text = render_input(task, payload, tokenizer="note_level")
                target_text = render_target(task, target_payload, tokenizer="note_level")
                system_prompt = render_system_prompt(task, tokenizer="note_level", prompt_mode=args.prompt_mode)
                user_prompt = render_user_prompt(task, payload, tokenizer="note_level", prompt_mode=args.prompt_mode)
                rec = {
                    "id": f"{task}-{idx:06d}",
                    "task": task,
                    "input": input_text,
                    "target": target_text,
                    "input_tokenized": input_text,
                    "output_tokenized": target_text,
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "ground_truth": target_text,
                    "payload": payload,
                    "target_payload": target_payload,
                    "meta": {
                        "tokenizer": "note_level",
                        "zero_shot": True,
                        "prompt_mode": args.prompt_mode,
                    },
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                idx += 1

    print(f"generated: {out_path}")
    print(
        f"tasks: {len(selected_tasks)}, samples/task: {args.samples_per_task}, total: {len(selected_tasks) * args.samples_per_task}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
