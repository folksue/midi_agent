from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import mido
except Exception:  # pragma: no cover
    mido = None

from .dsl import Chunk, Meta, Track


@dataclass
class ScheduledMessage:
    timestamp: float
    message: object


def _msg(kind: str, note: int, velocity: int, channel: int):
    if mido is None:
        return {
            "type": kind,
            "note": note,
            "velocity": velocity,
            "channel": channel,
        }
    return mido.Message(kind, note=note, velocity=velocity, channel=channel)


def compile_chunk_to_midi(
    chunk: Chunk,
    meta: Meta,
    track: Track,
    start_time_wallclock: float,
) -> list[ScheduledMessage]:
    beat_duration_sec = 60.0 / float(meta.bpm)
    bar_len_beats = float(meta.meter_num)

    out: list[ScheduledMessage] = []

    for ev in chunk.events:
        abs_t_beats = (chunk.from_bar * bar_len_beats) + ev.t
        on_ts = start_time_wallclock + (abs_t_beats * beat_duration_sec)
        off_ts = start_time_wallclock + ((abs_t_beats + ev.d) * beat_duration_sec)
        for n in ev.notes:
            out.append(
                ScheduledMessage(
                    timestamp=on_ts,
                    message=_msg("note_on", n, ev.v, track.channel),
                )
            )
            out.append(
                ScheduledMessage(
                    timestamp=off_ts,
                    message=_msg("note_off", n, 0, track.channel),
                )
            )

    out.sort(key=lambda x: x.timestamp)
    return out


def save_chunk_to_midi_file(
    chunk: Chunk,
    meta: Meta,
    track: Track,
    out_path: str,
) -> None:
    if mido is None:
        raise RuntimeError("mido unavailable; cannot export midi file")

    ticks_per_beat = 480
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.Message("program_change", program=track.program, channel=track.channel, time=0))

    events: list[tuple[int, int, object]] = []
    # Export per-chunk content using chunk-local beat positions.
    for ev in chunk.events:
        on_tick = int(round(ev.t * ticks_per_beat))
        off_tick = int(round((ev.t + ev.d) * ticks_per_beat))
        for n in ev.notes:
            events.append((on_tick, 1, mido.Message("note_on", note=n, velocity=ev.v, channel=track.channel)))
            events.append((off_tick, 0, mido.Message("note_off", note=n, velocity=0, channel=track.channel)))

    events.sort(key=lambda x: (x[0], x[1]))
    last_tick = 0
    for tick, _, msg in events:
        msg.time = max(0, tick - last_tick)
        tr.append(msg)
        last_tick = tick

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(path)
