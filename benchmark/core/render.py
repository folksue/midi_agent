from __future__ import annotations

from ..tokenizers import render_by_tokenizer


def render_input(task: str, payload: dict, tokenizer: str) -> str:
    if task == "task1_interval_identification":
        notes = render_by_tokenizer(tokenizer, payload["notes"])
        return f"Interval Identification\nnotes={notes}"

    if task == "task2_chord_identification":
        notes = render_by_tokenizer(tokenizer, payload["notes"])
        return f"Chord Identification\nnotes={notes}"

    if task == "task3_harmonic_function":
        return f"Harmonic Function\nkey={payload['key']} chord={payload['chord']}"

    if task == "task4_transposition":
        melody = render_by_tokenizer(tokenizer, payload["melody"])
        return (
            "Transposition\n"
            f"bpm={payload['bpm']} meter={payload['meter']} grid={payload['grid']} bar_beats={payload['bar_beats']}\n"
            f"source_key={payload['source_key']} target_key={payload['target_key']}\n"
            f"melody={melody}"
        )

    if task == "task5_melodic_inversion":
        melody = render_by_tokenizer(tokenizer, payload["melody"])
        return (
            "Melodic Inversion\n"
            f"bpm={payload['bpm']} meter={payload['meter']} grid={payload['grid']} bar_beats={payload['bar_beats']}\n"
            f"pivot={payload['pivot']} melody={melody}"
        )

    if task == "task6_retrograde":
        melody = render_by_tokenizer(tokenizer, payload["melody"])
        return (
            "Retrograde\n"
            f"bpm={payload['bpm']} meter={payload['meter']} grid={payload['grid']} bar_beats={payload['bar_beats']}\n"
            f"melody={melody}"
        )

    if task == "task7_rhythm_scale":
        melody = render_by_tokenizer(tokenizer, payload["melody"])
        return (
            "Rhythm Scale\n"
            f"bpm={payload['bpm']} meter={payload['meter']} grid={payload['grid']} bar_beats={payload['bar_beats']}\n"
            f"factor={payload['factor']} melody={melody}"
        )

    if task == "task8_voice_leading":
        v0 = render_by_tokenizer(tokenizer, payload["voices_t0"])
        v1 = render_by_tokenizer(tokenizer, payload["voices_t1"])
        return f"Voice Leading Detection\nt0={v0}\nt1={v1}"

    raise ValueError(f"unknown task: {task}")


def render_target(task: str, target_payload: object, tokenizer: str) -> str:
    if task in {
        "task1_interval_identification",
        "task2_chord_identification",
        "task3_harmonic_function",
        "task8_voice_leading",
    }:
        return str(target_payload)

    if task in {
        "task4_transposition",
        "task5_melodic_inversion",
        "task6_retrograde",
        "task7_rhythm_scale",
    }:
        return render_by_tokenizer(tokenizer, target_payload)

    raise ValueError(f"unknown task: {task}")


def _sequence_task_rules(task: str) -> str:
    if task == "task4_transposition":
        return "Transform pitch by key shift; keep note count/order/durations unchanged."
    if task == "task5_melodic_inversion":
        return "Use inversion formula p' = 2*pivot - p; keep note count/order/durations unchanged."
    if task == "task6_retrograde":
        return "Reverse note order; each note keeps its own pitch-duration pair."
    if task == "task7_rhythm_scale":
        return "Scale every duration by factor; keep note count/order/pitches unchanged."
    return ""


def _tokenizer_grammar(tokenizer: str) -> str:
    if tokenizer == "note_level":
        return (
            "Output melody as event blocks separated by ' | '.\n"
            "Each event must be exactly: t=<DECIMAL> d=<DECIMAL> notes=[<INT>] v=<INT>\n"
            "Example: t=0.00 d=0.50 notes=[60] v=80 | t=0.50 d=0.50 notes=[62] v=80\n"
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


def render_system_prompt(task: str, tokenizer: str, prompt_mode: str = "light") -> str:
    if prompt_mode == "agent_like" and task in {
        "task4_transposition",
        "task5_melodic_inversion",
        "task6_retrograde",
        "task7_rhythm_scale",
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
        "task4_transposition",
        "task5_melodic_inversion",
        "task6_retrograde",
        "task7_rhythm_scale",
    }:
        return "You are a music transformation solver. Return only the transformed melody tokens. No explanation."
    return "You are a music reasoning solver. Return only the final answer token string. No explanation."


def render_user_prompt(task: str, payload: dict, tokenizer: str, prompt_mode: str = "light") -> str:
    problem = render_input(task, payload, tokenizer=tokenizer)
    if prompt_mode == "agent_like" and task in {
        "task4_transposition",
        "task5_melodic_inversion",
        "task6_retrograde",
        "task7_rhythm_scale",
    }:
        # Clean agent-like mode: all hard constraints live in system prompt; user prompt carries only instance data.
        return problem
    return (
        f"Task={task}\n"
        f"Tokenizer={tokenizer}\n"
        "Answer with only one line final output.\n"
        "Question:\n"
        f"{problem}"
    )
