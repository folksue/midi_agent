from __future__ import annotations

from .rules import CHORD_TEMPLATES, INTERVAL_LABELS, PITCH_CLASS_NAMES, chord_label_from_root_quality

ALL_TASKS = [
    "task1_interval_identification",
    "task2_chord_identification",
    "task3_harmonic_function",
    "task4_transposition",
    "task5_melodic_inversion",
    "task6_retrograde",
    "task7_rhythm_scale",
    "task8_voice_leading",
]

LABEL_TASKS = {
    "task1_interval_identification",
    "task2_chord_identification",
    "task3_harmonic_function",
    "task8_voice_leading",
}

SEQUENCE_TASKS = {
    "task4_transposition",
    "task5_melodic_inversion",
    "task6_retrograde",
    "task7_rhythm_scale",
}

TASK_GROUPS = {
    "all": tuple(ALL_TASKS),
    "label": tuple(t for t in ALL_TASKS if t in LABEL_TASKS),
    "sequence": tuple(t for t in ALL_TASKS if t in SEQUENCE_TASKS),
}

TASK_TITLES = {
    "task1_interval_identification": "Interval Identification",
    "task2_chord_identification": "Chord Identification",
    "task3_harmonic_function": "Harmonic Function",
    "task4_transposition": "Transposition",
    "task5_melodic_inversion": "Melodic Inversion",
    "task6_retrograde": "Retrograde",
    "task7_rhythm_scale": "Rhythm Scale",
    "task8_voice_leading": "Voice Leading Detection",
}

TASK_PREDICTION_KIND = {
    task: ("label" if task in LABEL_TASKS else "notes")
    for task in ALL_TASKS
}

TASK_PRIMARY_PREDICTION_FIELD = {
    task: ("prediction_label" if task in LABEL_TASKS else "prediction_notes")
    for task in ALL_TASKS
}


def _task2_label_space() -> list[str]:
    labels: list[str] = []
    for root_pc in range(len(PITCH_CLASS_NAMES)):
        for quality in CHORD_TEMPLATES:
            labels.append(chord_label_from_root_quality(root_pc, quality))
    return labels


TASK_LABEL_SPACES = {
    "task1_interval_identification": [INTERVAL_LABELS[i] for i in sorted(INTERVAL_LABELS)],
    "task2_chord_identification": _task2_label_space(),
    "task3_harmonic_function": ["tonic", "predominant", "dominant"],
    "task8_voice_leading": ["parallel_fifths", "voice_crossing", "none"],
}


def prediction_kind_for_task(task: str) -> str:
    try:
        return TASK_PREDICTION_KIND[task]
    except KeyError as exc:
        raise ValueError(f"unknown task: {task}") from exc


def primary_prediction_field_for_task(task: str) -> str:
    try:
        return TASK_PRIMARY_PREDICTION_FIELD[task]
    except KeyError as exc:
        raise ValueError(f"unknown task: {task}") from exc


def label_space_for_task(task: str) -> list[str]:
    return list(TASK_LABEL_SPACES.get(task, []))
