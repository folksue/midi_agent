from __future__ import annotations

from ..tokenizers import render_by_tokenizer

LABEL_TASKS = {
    "task1_interval_identification",
    "task2_chord_identification",
    "task3_harmonic_function",
    "task4_voice_leading",
}

SEQUENCE_TASKS = {
    "task5_transposition",
    "task6_melodic_inversion",
    "task7_retrograde",
    "task8_rhythm_scale",
}


def render_input(task: str, payload: dict, tokenizer: str) -> str:
    return compose_user_prompt_from_parts(render_user_prompt_parts(task, payload, tokenizer=tokenizer))


def render_target(task: str, target_payload: object, tokenizer: str) -> str:
    if task in {
        "task1_interval_identification",
        "task2_chord_identification",
        "task3_harmonic_function",
        "task4_voice_leading",
    }:
        return str(target_payload)

    if task in {
        "task5_transposition",
        "task6_melodic_inversion",
        "task7_retrograde",
        "task8_rhythm_scale",
    }:
        return render_by_tokenizer(tokenizer, target_payload)

    raise ValueError(f"unknown task: {task}")


def _sequence_task_rules(task: str) -> str:
    if task == "task5_transposition":
        return "Transform pitch by key shift; keep note count/order/durations unchanged."
    if task == "task6_melodic_inversion":
        return "Use inversion formula p' = 2*pivot - p; keep note count/order/durations unchanged."
    if task == "task7_retrograde":
        return "Reverse note order; each note keeps its own pitch-duration pair."
    if task == "task8_rhythm_scale":
        return "Scale every duration by factor; keep note count/order/pitches unchanged."
    return ""


def _tokenizer_grammar(tokenizer: str) -> str:
    if tokenizer == "note_level":
        return (
            "Output melody as event blocks separated by ' | '.\n"
            "Each event must be exactly: t=<DECIMAL> d=<DECIMAL> notes=[<NOTE_NAME>] v=<INT>\n"
            "Example: t=0.00 d=0.50 notes=[C4] v=80 | t=0.50 d=0.50 notes=[D4] v=80\n"
            "Use decimal numbers only (NOT fractions like 1/4)."
        )
    if tokenizer == "midilike":
        return (
            "Output melody tokens with repeating quintuplets:\n"
            "TIME_<T> NOTE_ON_<P> VEL_<V> DUR_<D> NOTE_OFF_<P>\n"
            "Example: TIME_0 NOTE_ON_60 VEL_80 DUR_0.5 NOTE_OFF_60 TIME_0.5 NOTE_ON_62 VEL_80 DUR_0.5 NOTE_OFF_62"
        )
    if tokenizer == "remilike":
        return (
            "Output melody tokens with repeating quadruplets:\n"
            "POS_<T> PITCH_<P> VEL_<V> DUR_<D>\n"
            "Example: POS_0 PITCH_60 VEL_80 DUR_0.5 POS_0.5 PITCH_62 VEL_80 DUR_0.5"
        )
    return "Return a valid tokenizer-formatted melody token sequence."


def _label_input_tokenizer_hint(tokenizer: str) -> str:
    if tokenizer == "note_level":
        return "Input notes are serialized as note_level events: t=<DECIMAL> d=<DECIMAL> notes=[<NOTE_NAME>] v=<INT>."
    if tokenizer == "midilike":
        return (
            "Input notes are serialized as midilike tokens: "
            "TIME_<T> NOTE_ON_<P> VEL_<V> DUR_<D> NOTE_OFF_<P>."
        )
    if tokenizer == "remilike":
        return "Input notes are serialized as remilike tokens: POS_<T> PITCH_<P> VEL_<V> DUR_<D>."
    return "Input notes follow tokenizer-specific serialization."


def _label_task_rules(task: str) -> str:
    if task == "task1_interval_identification":
        return (
            "Identify the interval between the two given notes by semitone distance.\n"
            "Output exactly one label from:\n"
            "unison, minor_second, major_second, minor_third, major_third, "
            "perfect_fourth, tritone, perfect_fifth, minor_sixth, major_sixth, "
            "minor_seventh, major_seventh, octave."
        )
    if task == "task2_chord_identification":
        return (
            "Identify chord root and quality from the given simultaneity of notes.\n"
            "Output exactly one chord label string in one of these forms:\n"
            "<ROOT>_major | <ROOT>_minor | <ROOT>_diminished | <ROOT>_augmented | <ROOT>7\n"
            "ROOT must be one of: C, C#, D, D#, E, F, F#, G, G#, A, A#, B."
        )
    if task == "task3_harmonic_function":
        return (
            "Classify the chord's harmonic function in C major context.\n"
            "Output exactly one label from: tonic, predominant, dominant."
        )
    if task == "task4_voice_leading":
        return (
            "Detect voice-leading violation type between t0 and t1 voice states.\n"
            "Output exactly one label from: parallel_fifths, voice_crossing, none."
        )
    return "Output exactly one valid label token."


def render_system_prompt(task: str, tokenizer: str, prompt_mode: str = "light") -> str:
    if prompt_mode == "agent_like" and task in {
        "task5_transposition",
        "task6_melodic_inversion",
        "task7_retrograde",
        "task8_rhythm_scale",
    }:
        return (
            "You are a strict music token transformation generator.\n"
            "Rules:\n"
            "1) Output ONLY the transformed melody tokens.\n"
            "2) No explanations, no markdown, no extra text.\n"
            f"3) {_tokenizer_grammar(tokenizer)}\n"
            f"4) {_sequence_task_rules(task)}\n"
            "5) If unsure, output fewer valid tokens over invalid format."
        )
    if task in {
        "task5_transposition",
        "task6_melodic_inversion",
        "task7_retrograde",
        "task8_rhythm_scale",
    }:
        return "You are a music transformation solver. Return only the transformed melody tokens. No explanation."
    if task in {
        "task1_interval_identification",
        "task2_chord_identification",
        "task3_harmonic_function",
        "task4_voice_leading",
    }:
        return (
            "You are a strict music label classifier.\n"
            "Rules:\n"
            "1) Output ONLY one final label token string.\n"
            "2) No explanations, no markdown, no extra text.\n"
            f"3) {_label_task_rules(task)}\n"
            f"4) {_label_input_tokenizer_hint(tokenizer)}"
        )
    return "You are a music reasoning solver. Return only the final answer token string. No explanation."


def render_user_prompt(task: str, payload: dict, tokenizer: str, prompt_mode: str = "light") -> str:
    # Keep user prompt as pure task instance data in all modes.
    # Any output-format constraints should live in system prompt.
    return compose_user_prompt_from_parts(
        render_user_prompt_parts(task, payload, tokenizer=tokenizer, prompt_mode=prompt_mode)
    )


def render_user_prompt_parts(task: str, payload: dict, tokenizer: str, prompt_mode: str = "light") -> dict:
    del prompt_mode  # reserved for future mode-specific part composition
    parts: dict = {
        "question_body": "",
        "task_description": "",
        "instance_lines": [],
        "control_params": {},
        "answer_constraint": (
            "Return only one label token string."
            if task in LABEL_TASKS
            else "Return only transformed melody tokens, one line."
        ),
        "melody_input_tokens": "",
    }

    if task == "task1_interval_identification":
        notes = render_by_tokenizer(tokenizer, payload["notes"])
        parts["question_body"] = "Interval Identification"
        parts["task_description"] = "Determine the interval class between the two notes."
        parts["instance_lines"] = [f"notes: {notes}"]
        parts["melody_input_tokens"] = notes
        return parts

    if task == "task2_chord_identification":
        notes = render_by_tokenizer(tokenizer, payload["notes"])
        parts["question_body"] = "Chord Identification"
        parts["task_description"] = "Infer chord root and quality from the simultaneous notes."
        parts["instance_lines"] = [f"notes: {notes}"]
        parts["melody_input_tokens"] = notes
        return parts

    if task == "task3_harmonic_function":
        parts["question_body"] = "Harmonic Function"
        parts["task_description"] = "Classify the chord function in C major from the chord-note tokens."
        chord_notes = payload.get("chord_notes")
        if isinstance(chord_notes, list):
            chord_tok = render_by_tokenizer(tokenizer, chord_notes)
            parts["instance_lines"] = [f"chord_notes: {chord_tok}"]
            parts["melody_input_tokens"] = chord_tok
            parts["control_params"] = {"key_context": "C_major"}
            return parts
        # Backward compatibility for old payloads without chord_notes.
        kc = f"chord: {payload['chord']}"
        parts["instance_lines"] = [kc]
        parts["melody_input_tokens"] = kc
        parts["control_params"] = {"key_context": str(payload.get("key", "C_major"))}
        return parts

    if task == "task5_transposition":
        melody = render_by_tokenizer(tokenizer, payload["melody"])
        parts["question_body"] = "Transposition"
        parts["task_description"] = "Transpose the melody from source key to target key while preserving rhythm and note order."
        parts["instance_lines"] = [
            f"bpm: {payload['bpm']} meter: {payload['meter']} grid: {payload['grid']} bar_beats: {payload['bar_beats']}",
            f"source_key: {payload['source_key']} target_key: {payload['target_key']}",
            f"melody: {melody}",
        ]
        parts["control_params"] = {
            "source_key": payload["source_key"],
            "target_key": payload["target_key"],
        }
        parts["melody_input_tokens"] = melody
        return parts

    if task == "task6_melodic_inversion":
        melody = render_by_tokenizer(tokenizer, payload["melody"])
        parts["question_body"] = "Melodic Inversion"
        parts["task_description"] = "Invert each melody pitch around the given pivot while preserving timing/order."
        parts["instance_lines"] = [
            f"bpm: {payload['bpm']} meter: {payload['meter']} grid: {payload['grid']} bar_beats: {payload['bar_beats']}",
            f"pivot: {payload['pivot']} melody: {melody}",
        ]
        parts["control_params"] = {"pivot": payload["pivot"]}
        parts["melody_input_tokens"] = melody
        return parts

    if task == "task7_retrograde":
        melody = render_by_tokenizer(tokenizer, payload["melody"])
        parts["question_body"] = "Retrograde"
        parts["task_description"] = "Reverse the melodic note order while keeping each note's pitch-duration identity."
        parts["instance_lines"] = [
            f"bpm: {payload['bpm']} meter: {payload['meter']} grid: {payload['grid']} bar_beats: {payload['bar_beats']}",
            f"melody: {melody}",
        ]
        parts["melody_input_tokens"] = melody
        return parts

    if task == "task8_rhythm_scale":
        melody = render_by_tokenizer(tokenizer, payload["melody"])
        parts["question_body"] = "Rhythm Scale"
        parts["task_description"] = "Scale all note durations by the given factor while preserving pitch order."
        parts["instance_lines"] = [
            f"bpm: {payload['bpm']} meter: {payload['meter']} grid: {payload['grid']} bar_beats: {payload['bar_beats']}",
            f"factor: {payload['factor']} melody: {melody}",
        ]
        parts["control_params"] = {"factor": payload["factor"]}
        parts["melody_input_tokens"] = melody
        return parts

    if task == "task4_voice_leading":
        v0 = render_by_tokenizer(tokenizer, payload["voices_t0"])
        v1 = render_by_tokenizer(tokenizer, payload["voices_t1"])
        parts["question_body"] = "Voice Leading Detection"
        parts["task_description"] = "Detect whether the two-state voice motion contains a violation."
        parts["instance_lines"] = [f"t0: {v0}", f"t1: {v1}"]
        parts["melody_input_tokens"] = f"t0: {v0} t1: {v1}"
        return parts

    raise ValueError(f"unknown task: {task}")


def compose_user_prompt_from_parts(parts: dict) -> str:
    lines: list[str] = []
    d = str(parts.get("task_description", "")).strip()
    if d:
        lines.append(d)
    else:
        # Backward-compatible fallback for tasks that have not set task_description.
        q = str(parts.get("question_body", "")).strip()
        if q:
            lines.append(q)
    for ln in parts.get("instance_lines", []) or []:
        s = str(ln).strip()
        if s:
            lines.append(s)
    return "\n".join(lines)
