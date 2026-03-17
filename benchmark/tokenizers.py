from __future__ import annotations

from .core.rules import Note


def _fmt_d(d: float) -> str:
    # Keep enough precision for common rhythmic values like 0.125 while avoiding long float tails.
    return f"{float(d):.6f}".rstrip("0").rstrip(".")


def encode_note_level_melody(melody: list[dict]) -> str:
    if melody and {"t", "p", "d", "v"}.issubset(melody[0].keys()):
        return " | ".join(
            f"t={_fmt_d(float(n['t']))} d={_fmt_d(float(n['d']))} notes=[{int(n['p'])}] v={int(n['v'])}"
            for n in melody
        )
    return " ".join(f"n{int(n['p'])}/{_fmt_d(float(n['d']))}" for n in melody)


def decode_note_level_melody(text: str) -> list[dict]:
    out: list[dict] = []
    text = text.strip()
    if not text:
        return out
    if "notes=[" in text and "t=" in text and "d=" in text:
        chunks = [c.strip() for c in text.split("|") if c.strip()]
        for c in chunks:
            # expected: t=... d=... notes=[..] v=...
            try:
                parts = c.split()
                t = float(parts[0].split("=", 1)[1])
                d = float(parts[1].split("=", 1)[1])
                notes_field = parts[2].split("=", 1)[1].strip()
                p = int(notes_field.strip("[]").split(",")[0])
                v = int(parts[3].split("=", 1)[1])
                out.append({"t": t, "p": p, "d": d, "v": v})
            except Exception:
                continue
        return out
    for tok in text.split():
        if "/" not in tok or not tok.startswith("n"):
            continue
        p_str, d_str = tok[1:].split("/", 1)
        out.append({"p": int(p_str), "d": float(d_str), "t": 0.0, "v": 80})
    return out


def encode_midilike_melody(melody: list[dict]) -> str:
    toks: list[str] = []
    for n in melody:
        p = int(n["p"])
        d = _fmt_d(float(n["d"]))
        t = _fmt_d(float(n.get("t", 0.0)))
        v = int(n.get("v", 80))
        toks.extend([f"TIME_{t}", f"NOTE_ON_{p}", f"VEL_{v}", f"DUR_{d}", f"NOTE_OFF_{p}"])
    return " ".join(toks)


def decode_midilike_melody(text: str) -> list[dict]:
    toks = text.strip().split()
    out: list[dict] = []
    i = 0
    while i + 4 < len(toks):
        a, b, c, d_tok, e = toks[i], toks[i + 1], toks[i + 2], toks[i + 3], toks[i + 4]
        if (
            a.startswith("TIME_")
            and b.startswith("NOTE_ON_")
            and c.startswith("VEL_")
            and d_tok.startswith("DUR_")
            and e.startswith("NOTE_OFF_")
        ):
            t = float(a.split("_", 1)[1])
            p = int(b.split("_")[-1])
            v = int(c.split("_")[-1])
            d = float(d_tok.split("_", 1)[1])
            out.append({"t": t, "p": p, "d": d, "v": v})
            i += 5
        else:
            i += 1
    return out


def encode_remilike_melody(melody: list[dict]) -> str:
    toks: list[str] = []
    for n in melody:
        p = int(n["p"])
        d = float(n["d"])
        t = float(n.get("t", 0.0))
        v = int(n.get("v", 80))
        toks.extend([f"POS_{_fmt_d(t)}", f"PITCH_{p}", f"VEL_{v}", f"DUR_{_fmt_d(d)}"])
    return " ".join(toks)


def decode_remilike_melody(text: str) -> list[dict]:
    toks = text.strip().split()
    out: list[dict] = []
    i = 0
    while i + 3 < len(toks):
        a, b, c, d_tok = toks[i], toks[i + 1], toks[i + 2], toks[i + 3]
        if a.startswith("POS_") and b.startswith("PITCH_") and c.startswith("VEL_") and d_tok.startswith("DUR_"):
            t = float(a.split("_", 1)[1])
            p = int(b.split("_")[-1])
            v = int(c.split("_")[-1])
            d = float(d_tok.split("_", 1)[1])
            out.append({"t": t, "p": p, "d": d, "v": v})
            i += 4
        else:
            i += 1
    return out


def encode_pitch_set_note_level(notes: list[int]) -> str:
    return "[" + ",".join(str(int(n)) for n in notes) + "]"


def encode_pitch_set_midilike(notes: list[int]) -> str:
    return " ".join(f"CHORD_NOTE_{int(n)}" for n in notes)


def encode_pitch_set_remilike(notes: list[int]) -> str:
    return " ".join(f"PitchClass_{int(n) % 12}" for n in notes)


def render_by_tokenizer(tokenizer: str, payload: object) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (int, float)):
        return str(payload)
    if isinstance(payload, list):
        if not payload:
            return ""
        if isinstance(payload[0], dict) and "p" in payload[0] and "d" in payload[0]:
            if tokenizer == "note_level":
                return encode_note_level_melody(payload)
            if tokenizer == "midilike":
                return encode_midilike_melody(payload)
            if tokenizer == "remilike":
                return encode_remilike_melody(payload)
        if isinstance(payload[0], int):
            if tokenizer == "note_level":
                return encode_pitch_set_note_level(payload)
            if tokenizer == "midilike":
                return encode_pitch_set_midilike(payload)
            if tokenizer == "remilike":
                return encode_pitch_set_remilike(payload)
    return str(payload)


def decode_melody_by_tokenizer(tokenizer: str, text: str) -> list[dict]:
    if tokenizer == "note_level":
        return decode_note_level_melody(text)
    if tokenizer == "midilike":
        return decode_midilike_melody(text)
    if tokenizer == "remilike":
        return decode_remilike_melody(text)
    raise ValueError(f"unknown tokenizer: {tokenizer}")
