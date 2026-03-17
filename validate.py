from __future__ import annotations

from dataclasses import dataclass

from .config import grid_step_beats
from .dsl import Chunk, Meta, Track


@dataclass
class ValidationResult:
    fatal_errors: list[str]
    warnings: list[str]
    stats: dict
    fix_suggested: bool


EPS = 1e-6


def _on_grid(x: float, step: float, eps: float = EPS) -> bool:
    q = round(x / step)
    return abs(x - (q * step)) <= eps


def validate(chunk: Chunk, meta: Meta, track: Track) -> ValidationResult:
    del track
    fatal_errors: list[str] = []
    warnings: list[str] = []
    stats = {
        "event_count": len(chunk.events),
        "offgrid_count": 0,
        "overlap_count": 0,
    }

    step = grid_step_beats(meta.grid_str)
    bar_len = float(meta.meter_num)
    chunk_len_beats = (chunk.to_bar - chunk.from_bar + 1) * bar_len

    active_ranges: dict[int, list[tuple[float, float]]] = {}

    for i, ev in enumerate(chunk.events):
        if ev.t < -EPS:
            fatal_errors.append(f"event[{i}] t<0")
        if ev.d <= EPS:
            fatal_errors.append(f"event[{i}] d<=0")
        if ev.v < 1 or ev.v > 127:
            fatal_errors.append(f"event[{i}] velocity out of range")

        if not _on_grid(ev.t, step) or not _on_grid(ev.d, step):
            stats["offgrid_count"] += 1
            warnings.append(f"event[{i}] off-grid")

        if ev.t + ev.d > chunk_len_beats + EPS:
            fatal_errors.append(f"event[{i}] exceeds chunk end")

        for p in ev.notes:
            if p < 0 or p > 127:
                fatal_errors.append(f"event[{i}] pitch out of range: {p}")

            prev_list = active_ranges.setdefault(p, [])
            s, e = ev.t, ev.t + ev.d
            for ps, pe in prev_list:
                if s < pe - EPS and e > ps + EPS:
                    stats["overlap_count"] += 1
                    fatal_errors.append(f"event[{i}] overlap on pitch {p}")
                    break
            prev_list.append((s, e))

    fix_suggested = bool(stats["offgrid_count"] or stats["overlap_count"])
    return ValidationResult(
        fatal_errors=fatal_errors,
        warnings=warnings,
        stats=stats,
        fix_suggested=fix_suggested,
    )
