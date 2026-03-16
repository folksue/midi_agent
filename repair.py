from __future__ import annotations

from dataclasses import dataclass

from .config import grid_step_beats
from .dsl import Chunk, Meta, NoteEvent, Track


@dataclass
class RepairReport:
    quantize_total_abs_delta: float
    num_truncated: int
    num_overlap_fixed: int
    num_dropped: int
    too_much_fix: bool


EPS = 1e-6


def _quantize(x: float, step: float) -> tuple[float, float]:
    q = round(x / step) * step
    return q, abs(x - q)


def repair(chunk: Chunk, meta: Meta, track: Track) -> tuple[Chunk, RepairReport]:
    del track
    step = grid_step_beats(meta.grid_str)
    bar_len = float(meta.meter_num)
    chunk_end = (chunk.to_bar - chunk.from_bar + 1) * bar_len

    q_delta = 0.0
    num_truncated = 0
    num_overlap_fixed = 0
    num_dropped = 0

    repaired_events: list[NoteEvent] = []
    for ev in chunk.events:
        t, dt = _quantize(ev.t, step)
        d, dd = _quantize(ev.d, step)
        q_delta += dt + dd

        if d <= 0:
            d = step

        if t < 0:
            t = 0.0

        pitches = [min(127, max(0, int(p))) for p in ev.notes]
        v = min(127, max(1, int(ev.v)))

        if t + d > chunk_end:
            d = max(step, chunk_end - t)
            if d <= EPS:
                num_dropped += 1
                continue
            num_truncated += 1

        repaired_events.append(NoteEvent(t=t, d=d, notes=pitches, v=v))

    repaired_events.sort(key=lambda e: (e.t, e.d))

    # overlap fix policy: shorten earlier note to next note's start for same pitch.
    by_pitch: dict[int, list[tuple[int, float, float]]] = {}
    for idx, ev in enumerate(repaired_events):
        for p in ev.notes:
            by_pitch.setdefault(p, []).append((idx, ev.t, ev.t + ev.d))

    to_drop: set[int] = set()
    for p, seq in by_pitch.items():
        seq.sort(key=lambda x: (x[1], x[2]))
        for i in range(1, len(seq)):
            prev_idx, prev_s, prev_e = seq[i - 1]
            cur_idx, cur_s, _ = seq[i]
            if cur_s < prev_e - EPS:
                prev_ev = repaired_events[prev_idx]
                new_d = cur_s - prev_ev.t
                if new_d > EPS:
                    repaired_events[prev_idx] = NoteEvent(
                        t=prev_ev.t,
                        d=new_d,
                        notes=prev_ev.notes,
                        v=prev_ev.v,
                    )
                    num_overlap_fixed += 1
                else:
                    to_drop.add(cur_idx)
                    num_dropped += 1

    final_events = [ev for i, ev in enumerate(repaired_events) if i not in to_drop]

    evt_count = max(1, len(chunk.events))
    too_much_fix = q_delta > (0.5 * step * evt_count)

    report = RepairReport(
        quantize_total_abs_delta=q_delta,
        num_truncated=num_truncated,
        num_overlap_fixed=num_overlap_fixed,
        num_dropped=num_dropped,
        too_much_fix=too_much_fix,
    )
    return Chunk(chunk.from_bar, chunk.to_bar, final_events), report
