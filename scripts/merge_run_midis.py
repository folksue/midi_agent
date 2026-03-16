#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge saved chunk MIDI files for one run_id.")
    p.add_argument("--run-id", default="latest", help="run id like run-1773097036, or 'latest'")
    p.add_argument(
        "--base-dir",
        default="/media/folksue/Windows/midi_agent/logs/success_midi",
        help="base directory where per-run chunk midi folders are stored",
    )
    p.add_argument("--out", default="", help="output midi path (default: <run_dir>/merged.mid)")
    p.add_argument("--ticks-per-beat", type=int, default=480)
    return p.parse_args()


def run_ts(run_id: str) -> int:
    m = re.match(r"^run-(\d+)$", run_id)
    return int(m.group(1)) if m else -1


def pick_run_dir(base_dir: Path, run_id: str) -> Path:
    if not base_dir.exists():
        raise FileNotFoundError(f"base dir not found: {base_dir}")
    runs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("run-")]
    if not runs:
        # Backward compatibility: old layout stored chunk_*.mid directly under base_dir.
        flat_chunks = list(base_dir.glob("chunk_*.mid"))
        if flat_chunks:
            return base_dir
        raise FileNotFoundError(f"no run directories under: {base_dir}")
    runs_sorted = sorted(runs, key=lambda d: run_ts(d.name))
    if run_id == "latest":
        return runs_sorted[-1]
    target = base_dir / run_id
    if not target.exists() or not target.is_dir():
        raise FileNotFoundError(f"run dir not found: {target}")
    return target


def main() -> int:
    args = parse_args()

    try:
        import mido
    except Exception as exc:
        print(f"[merge] mido unavailable: {exc}")
        return 2

    base_dir = Path(args.base_dir)
    run_dir = pick_run_dir(base_dir, args.run_id)
    out_path = Path(args.out) if args.out else (run_dir / "merged.mid")

    chunk_files = sorted(run_dir.glob("chunk_*.mid"))
    if not chunk_files:
        print(f"[merge] no chunk midi files in: {run_dir}")
        return 3

    tpq = args.ticks_per_beat
    merged = mido.MidiFile(ticks_per_beat=tpq)
    out_track = mido.MidiTrack()
    merged.tracks.append(out_track)

    # Accumulate absolute events from all chunk files with per-chunk offset.
    abs_events: list[tuple[int, int, object]] = []
    offset = 0
    kept_program_change = False

    for f in chunk_files:
        mf = mido.MidiFile(f)
        track = mf.tracks[0] if mf.tracks else mido.MidiTrack()
        abs_tick = 0
        local_events: list[tuple[int, int, object]] = []
        for msg in track:
            abs_tick += int(msg.time)
            if msg.is_meta:
                continue
            m = msg.copy(time=0)
            # Keep only first program_change across all chunks.
            if m.type == "program_change":
                if kept_program_change:
                    continue
                kept_program_change = True
            # Sort note_off before note_on at same tick.
            prio = 0 if m.type == "note_off" else 1
            local_events.append((abs_tick, prio, m))

        if local_events:
            last_tick = max(t for t, _, _ in local_events)
        else:
            last_tick = 0

        for t, prio, m in local_events:
            abs_events.append((offset + t, prio, m))

        # Ensure each chunk advances at least one 4/4 bar at current tpq.
        min_chunk_ticks = 4 * tpq
        offset += max(last_tick, min_chunk_ticks)

    abs_events.sort(key=lambda x: (x[0], x[1]))

    last = 0
    for t, _, m in abs_events:
        m.time = max(0, t - last)
        out_track.append(m)
        last = t

    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(out_path)
    print(f"[merge] run_dir: {run_dir}")
    print(f"[merge] chunks: {len(chunk_files)}")
    print(f"[merge] output: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
