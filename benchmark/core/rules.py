from __future__ import annotations

import random
from dataclasses import dataclass

PITCH_CLASS_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

INTERVAL_LABELS = {
    0: "unison",
    1: "minor_second",
    2: "major_second",
    3: "minor_third",
    4: "major_third",
    5: "perfect_fourth",
    6: "tritone",
    7: "perfect_fifth",
    8: "minor_sixth",
    9: "major_sixth",
    10: "minor_seventh",
    11: "major_seventh",
    12: "octave",
}

CHORD_TEMPLATES = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    "dominant7": [0, 4, 7, 10],
}

MAJOR_SCALE_PCS = [0, 2, 4, 5, 7, 9, 11]


@dataclass
class Note:
    p: int
    d: float


def pc_name(pc: int) -> str:
    return PITCH_CLASS_NAMES[pc % 12]


def interval_label(n1: int, n2: int) -> str:
    d = abs(n2 - n1)
    return INTERVAL_LABELS.get(d, f"interval_{d}")


def chord_label_from_root_quality(root_pc: int, quality: str) -> str:
    if quality == "dominant7":
        return f"{pc_name(root_pc)}7"
    return f"{pc_name(root_pc)}_{quality}"


def harmonic_function_major(key_root_pc: int, chord_root_pc: int, quality: str) -> str:
    deg_pc = (chord_root_pc - key_root_pc) % 12
    if deg_pc in {0, 4, 9}:  # I, iii, vi
        return "tonic"
    if deg_pc in {2, 5}:  # ii, IV
        return "predominant"
    if deg_pc in {7, 11}:  # V, vii°
        return "dominant"
    # fallback for out-of-set chords
    if quality == "dominant7":
        return "dominant"
    return "tonic"


def transpose_melody(melody: list[Note], semitone_shift: int) -> list[Note]:
    return [Note(p=n.p + semitone_shift, d=n.d) for n in melody]


def invert_melody(melody: list[Note], pivot: int) -> list[Note]:
    return [Note(p=(2 * pivot - n.p), d=n.d) for n in melody]


def retrograde_melody(melody: list[Note]) -> list[Note]:
    return list(reversed([Note(p=n.p, d=n.d) for n in melody]))


def rhythm_scale_melody(melody: list[Note], factor: float) -> list[Note]:
    return [Note(p=n.p, d=round(n.d * factor, 4)) for n in melody]


def has_parallel_fifths(v1_t0: int, v2_t0: int, v1_t1: int, v2_t1: int) -> bool:
    int0 = abs(v1_t0 - v2_t0) % 12
    int1 = abs(v1_t1 - v2_t1) % 12
    if int0 != 7 or int1 != 7:
        return False
    m1 = v1_t1 - v1_t0
    m2 = v2_t1 - v2_t0
    return (m1 > 0 and m2 > 0) or (m1 < 0 and m2 < 0)


def has_voice_crossing(high: int, low: int) -> bool:
    return low > high


def make_random_melody(rng: random.Random, n_notes: int, pitch_min: int = 60, pitch_max: int = 72) -> list[Note]:
    durations = [0.25, 0.5, 1.0]
    out: list[Note] = []
    for _ in range(n_notes):
        out.append(Note(p=rng.randint(pitch_min, pitch_max), d=rng.choice(durations)))
    return out


def to_note_dicts(melody: list[Note]) -> list[dict]:
    return [{"p": n.p, "d": n.d} for n in melody]


def from_note_dicts(xs: list[dict]) -> list[Note]:
    return [Note(p=int(x["p"]), d=float(x["d"])) for x in xs]
