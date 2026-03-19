from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class ParseError(ValueError):
    pass


@dataclass
class Meta:
    bpm: int
    meter_num: int
    meter_den: int
    grid_str: str
    bars: int


@dataclass
class Track:
    name: str
    program: int
    channel: int


@dataclass
class NoteEvent:
    t: float
    d: float
    notes: list[int]
    v: int


@dataclass
class Chunk:
    from_bar: int
    to_bar: int
    events: list[NoteEvent]


_CHUNK_RE = re.compile(r"^@chunk\s+from_bar=(\d+)\s+to_bar=(\d+)\s*$")
_EVENT_RE = re.compile(
    r"^t\s*=\s*([^\s]+)\s+d\s*=\s*([^\s]+)\s+notes\s*=\s*\[([^\]]*)\]\s+v\s*=\s*(\d+)\s*$"
)


def _to_float(value: str) -> float:
    try:
        return float(Decimal(value))
    except (InvalidOperation, ValueError) as exc:
        raise ParseError(f"Invalid float: {value}") from exc


def _parse_notes(raw: str) -> list[int]:
    raw = raw.strip()
    if not raw:
        return []
    out: list[int] = []
    for x in raw.split(","):
        x = x.strip()
        if not x:
            continue
        try:
            out.append(int(x))
        except ValueError as exc:
            raise ParseError(f"Invalid note integer: {x}") from exc
    return out


def parse_chunk(text: str) -> Chunk:
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith("#")]

    chunk_header = None
    chunk_footer_idx = None
    for idx, line in enumerate(lines):
        if line.startswith("@chunk") and chunk_header is None:
            chunk_header = (idx, line)
        if line == "@eochunk":
            chunk_footer_idx = idx
            break

    if chunk_header is None:
        raise ParseError("Missing @chunk header")
    if chunk_footer_idx is None:
        raise ParseError("Missing @eochunk")

    m = _CHUNK_RE.match(chunk_header[1])
    if not m:
        raise ParseError("Invalid @chunk header format")

    from_bar = int(m.group(1))
    to_bar = int(m.group(2))
    if to_bar < from_bar:
        raise ParseError("to_bar must be >= from_bar")

    events: list[NoteEvent] = []
    for line in lines[chunk_header[0] + 1 : chunk_footer_idx]:
        if line.startswith("@"):
            continue
        m_ev = _EVENT_RE.match(line)
        if not m_ev:
            raise ParseError(f"Invalid event line: {line}")
        t = _to_float(m_ev.group(1))
        d = _to_float(m_ev.group(2))
        notes = _parse_notes(m_ev.group(3))
        v = int(m_ev.group(4))
        events.append(NoteEvent(t=t, d=d, notes=notes, v=v))

    return Chunk(from_bar=from_bar, to_bar=to_bar, events=events)


def parse_chunks(text: str) -> list[Chunk]:
    """Parse one or more @chunk ... @eochunk blocks in order."""
    lines = text.splitlines()
    blocks: list[str] = []
    in_block = False
    cur: list[str] = []

    for raw in lines:
        line = raw.strip()
        if not in_block:
            if line.startswith("@chunk"):
                in_block = True
                cur = [line]
            continue
        cur.append(line)
        if line == "@eochunk":
            blocks.append("\n".join(cur))
            in_block = False
            cur = []

    if not blocks:
        raise ParseError("Missing chunk blocks")

    chunks = [parse_chunk(b) for b in blocks]
    return chunks


def strip_end_signal(text: str) -> tuple[str, bool]:
    """Remove @end lines and report whether end signal was present."""
    end = False
    kept: list[str] = []
    for raw in text.splitlines():
        if raw.strip() == "@end":
            end = True
            continue
        kept.append(raw)
    return "\n".join(kept), end
