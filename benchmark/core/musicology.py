from __future__ import annotations

from .rules import PITCH_CLASS_NAMES
from .task_specs import LABEL_TASKS

EXPLANATION_POLICY = {
    "mode": "hybrid",
    "summary": (
        "V1 uses rule-based reference explanations and allows optional "
        "model-generated prediction_explanation fields at inference time."
    ),
}

THEORETICAL_SIMPLIFICATIONS = {
    "harmonic_function": [
        "major mode only in V1",
        "three coarse function classes: tonic, predominant, dominant",
    ],
    "voice_leading": [
        "two-voice simplification in V1",
        "labels limited to parallel_fifths, voice_crossing, and none",
    ],
    "harmony": [
        "reduced harmonic vocabulary in V1",
        "chord templates limited to major, minor, diminished, augmented, and dominant7",
    ],
    "modality": [
        "symbolic music focus, not audio",
    ],
}


def midi_to_note_name(pitch: int) -> str:
    pc = pitch % 12
    octave = (pitch // 12) - 1
    return f"{PITCH_CLASS_NAMES[pc]}{octave}"


def label_task_explanation(task: str, payload: dict, target_label: str) -> str:
    if task not in LABEL_TASKS:
        return ""

    if task == "task1_interval_identification":
        notes = payload.get("notes", [])
        if len(notes) >= 2:
            n1 = int(notes[0])
            n2 = int(notes[1])
            semitones = abs(n2 - n1)
            return (
                f"{midi_to_note_name(n1)} to {midi_to_note_name(n2)} spans {semitones} semitones, "
                f"which corresponds to a {target_label.replace('_', ' ')}."
            )
        return f"The interval is classified as {target_label.replace('_', ' ')}."

    if task == "task2_chord_identification":
        notes = [int(x) for x in payload.get("notes", [])]
        pcs = sorted({PITCH_CLASS_NAMES[n % 12] for n in notes})
        pc_text = ", ".join(pcs)
        return (
            f"The pitch-class content {{{pc_text}}} matches the template for {target_label}, "
            "so the sonority is classified accordingly."
        )

    if task == "task3_harmonic_function":
        key = str(payload.get("key", "")).replace("_", " ")
        chord = str(payload.get("chord", ""))
        if target_label == "dominant":
            reason = "it projects dominant tension toward the tonic"
        elif target_label == "predominant":
            reason = "it prepares dominant motion"
        else:
            reason = "it belongs to the tonic area"
        return f"In {key}, the chord {chord} is labeled {target_label} because {reason}."

    if task == "task4_voice_leading":
        t0 = payload.get("voices_t0", [])
        t1 = payload.get("voices_t1", [])
        if len(t0) >= 2 and len(t1) >= 2:
            v0a = midi_to_note_name(int(t0[0]))
            v0b = midi_to_note_name(int(t0[1]))
            v1a = midi_to_note_name(int(t1[0]))
            v1b = midi_to_note_name(int(t1[1]))
            if target_label == "parallel_fifths":
                return (
                    f"The voices move from {v0a}/{v0b} to {v1a}/{v1b} in the same direction "
                    "while preserving a perfect-fifth span, so this is a parallel fifths violation."
                )
            if target_label == "voice_crossing":
                return (
                    f"The voices move from {v0a}/{v0b} to {v1a}/{v1b}, and the lower voice ends above "
                    "the upper voice, so this is a voice crossing."
                )
            return (
                f"The voices move from {v0a}/{v0b} to {v1a}/{v1b} without triggering the benchmark's "
                "voice-leading violation labels."
            )
        return f"The voice-leading label is {target_label}."

    return ""
