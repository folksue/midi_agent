from __future__ import annotations

from collections import deque
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .config import DEFAULT_CONFIG, RuntimeConfig
from .dsl import Chunk, Meta, ParseError, Track, parse_chunks, strip_end_signal
from .llm_client import LLMClient, LLMContext
from .metrics import ChunkMetric, MetricsLogger
from .midi_compile import compile_chunk_to_midi, save_chunk_to_midi_file
from .midi_io import open_output
from .repair import repair
from .scheduler import RealtimeScheduler
from .validate import validate


@dataclass
class SharedState:
    mode: str = "CHAT"
    style: str = "simple piano"
    force_continue: bool = False


class MidiAgentApp:
    def __init__(self, cfg: RuntimeConfig | None = None):
        self.cfg = cfg or DEFAULT_CONFIG
        self.state = SharedState()
        self.lock = threading.Lock()

        self.meta = Meta(
            bpm=self.cfg.bpm,
            meter_num=self.cfg.meter_num,
            meter_den=self.cfg.meter_den,
            grid_str=self.cfg.grid_str,
            bars=self.cfg.total_bars,
        )
        self.track = Track(name="piano", program=0, channel=0)

        self.llm = LLMClient()
        self.metrics = MetricsLogger(self.cfg.metrics_path)

        self.midi_out = None
        self.scheduler = None
        self.play_thread: threading.Thread | None = None
        self.play_stop_evt = threading.Event()
        self.playhead_wallclock = 0.0
        self.next_bar_to_schedule = 0
        self.saved_chunk_index = 0
        self.pending_chunks: deque[Chunk] = deque()
        self.llm_signaled_end = False
        self.single_shot_requested = False

    def run_cli(self) -> None:
        print("MidiAgent CLI started. Commands: /play [style], /continue, /stop, /quit")
        while True:
            try:
                text = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                text = "/quit"

            if text == "/quit":
                self._stop_playback()
                print("bye")
                return

            if text.startswith("/play"):
                style = text[len("/play") :].strip() or "simple piano"
                self._start_playback(style)
                continue

            if text == "/continue":
                with self.lock:
                    self.state.force_continue = True
                print("[midi] continue requested")
                continue

            if text == "/stop":
                self._stop_playback()
                continue

            mode = self.state.mode
            if mode == "CHAT":
                print(self.llm.chat(text))
            else:
                self._update_controls(text)

    def _start_playback(self, style: str) -> None:
        self._stop_playback()
        with self.lock:
            self.state.mode = "MIDI_AGENT"
            self.state.style = style
            self.state.force_continue = False

        self.midi_out = open_output(
            port_name=self.cfg.midi_port_name,
            virtual=self.cfg.midi_virtual,
        )
        self.scheduler = RealtimeScheduler(self.midi_out.send)
        self.scheduler.start()

        self.play_stop_evt.clear()
        self.playhead_wallclock = time.perf_counter() + self.cfg.warmup_sec
        self.next_bar_to_schedule = 0
        self.saved_chunk_index = 0
        self.pending_chunks.clear()
        self.llm_signaled_end = False
        self.single_shot_requested = False

        self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.play_thread.start()
        print(f"[midi] started. style={style}, mode={self.cfg.play_mode}")

    def _stop_playback(self) -> None:
        with self.lock:
            was_midi = self.state.mode == "MIDI_AGENT"
            self.state.mode = "CHAT"

        if not was_midi:
            return

        self.play_stop_evt.set()
        if self.play_thread:
            self.play_thread.join(timeout=1.5)
        if self.scheduler:
            self.scheduler.stop()
        if self.midi_out:
            self.midi_out.close()

        print("[midi] stopped; back to CHAT")

    def _update_controls(self, text: str) -> None:
        with self.lock:
            if "更快" in text or "faster" in text.lower():
                self.meta.bpm = min(220, self.meta.bpm + 10)
            elif "更慢" in text or "slower" in text.lower():
                self.meta.bpm = max(40, self.meta.bpm - 10)
            else:
                self.state.style = text
        print(f"[midi] control updated. bpm={self.meta.bpm}, style={self.state.style}")

    def _current_playhead_bar(self) -> float:
        now = time.perf_counter()
        beat_sec = 60.0 / self.meta.bpm
        bar_sec = self.meta.meter_num * beat_sec
        return max(0.0, (now - self.playhead_wallclock) / bar_sec)

    def _play_loop(self) -> None:
        regen_hint = ""

        while not self.play_stop_evt.is_set():
            with self.lock:
                mode = self.state.mode
                force_continue = self.state.force_continue
                style = self.state.style
                if force_continue:
                    self.state.force_continue = False

            if mode != "MIDI_AGENT":
                return

            current_bar = self._current_playhead_bar()
            buffer_bars = self.next_bar_to_schedule - current_bar
            need_more = buffer_bars < self.cfg.lookahead_bars or force_continue
            if not need_more:
                time.sleep(0.03)
                continue

            if not self.pending_chunks:
                if self.cfg.play_mode == "single_shot_full":
                    if not self.single_shot_requested:
                        batch, regen_hint, got_end = self._generate_chunk_batch(
                            start_bar=self.next_bar_to_schedule,
                            style=style,
                            regen_hint=regen_hint,
                            bars_to_generate=max(1, self.cfg.single_shot_max_bars),
                            allow_end_signal=True,
                            fill_missing=False,
                        )
                        self.single_shot_requested = True
                        self.llm_signaled_end = self.llm_signaled_end or got_end
                        for ch in batch:
                            self.pending_chunks.append(ch)
                    else:
                        self._finish_playback_from_thread("single_shot drained")
                        return
                else:
                    if self.llm_signaled_end:
                        self._finish_playback_from_thread("llm signaled end")
                        return
                    batch, regen_hint, got_end = self._generate_chunk_batch(
                        start_bar=self.next_bar_to_schedule,
                        style=style,
                        regen_hint=regen_hint,
                        bars_to_generate=max(1, self.cfg.request_bars_per_call),
                        allow_end_signal=self.cfg.enable_llm_end_signal,
                        fill_missing=True,
                    )
                    self.llm_signaled_end = self.llm_signaled_end or got_end
                    for ch in batch:
                        self.pending_chunks.append(ch)

            if not self.pending_chunks:
                # absolute fallback safety
                chunk = self._fallback_chunk(self.next_bar_to_schedule)
                self._schedule_and_log_chunk(
                    chunk=chunk,
                    parse_ok=False,
                    fatal_count=1,
                    repair_applied=False,
                    quant_delta=0.0,
                    regen_count=self.cfg.max_regen_attempts,
                )
                continue

            chunk = self.pending_chunks.popleft()
            if chunk.from_bar != self.next_bar_to_schedule:
                chunk = self._fallback_chunk(self.next_bar_to_schedule)
                self._schedule_and_log_chunk(
                    chunk=chunk,
                    parse_ok=False,
                    fatal_count=1,
                    repair_applied=False,
                    quant_delta=0.0,
                    regen_count=0,
                )
                continue

            self._save_success_chunk(chunk)
            self._schedule_and_log_chunk(
                chunk=chunk,
                parse_ok=True,
                fatal_count=0,
                repair_applied=False,
                quant_delta=0.0,
                regen_count=0,
            )

    def _save_success_chunk(self, chunk: Chunk) -> None:
        if not self.cfg.save_success_midi:
            return
        self.saved_chunk_index += 1
        run_id = getattr(self.llm, "run_id", "unknown")
        out_dir = Path(self.cfg.success_midi_dir) / run_id
        stem = f"chunk_{self.saved_chunk_index:04d}_bar_{chunk.from_bar:04d}"
        midi_path = out_dir / f"{stem}.mid"
        dsl_path = out_dir / f"{stem}.dsl.txt"
        try:
            save_chunk_to_midi_file(chunk, self.meta, self.track, str(midi_path))
            dsl_path.parent.mkdir(parents=True, exist_ok=True)
            dsl_path.write_text(self._chunk_to_text(chunk), encoding="utf-8")
            print(f"[midi] saved success chunk: {midi_path}")
        except Exception as exc:
            print(f"[midi] save success chunk failed: {exc}")

    @staticmethod
    def _chunk_to_text(chunk: Chunk) -> str:
        lines = [f"@chunk from_bar={chunk.from_bar} to_bar={chunk.to_bar}"]
        for ev in chunk.events:
            notes = ",".join(str(n) for n in ev.notes)
            lines.append(f"t={ev.t:.2f} d={ev.d:.2f} notes=[{notes}] v={ev.v}")
        lines.append("@eochunk")
        return "\n".join(lines) + "\n"

    def _schedule_and_log_chunk(
        self,
        chunk: Chunk,
        parse_ok: bool,
        fatal_count: int,
        repair_applied: bool,
        quant_delta: float,
        regen_count: int,
    ) -> None:
        msgs = compile_chunk_to_midi(
            chunk=chunk,
            meta=self.meta,
            track=self.track,
            start_time_wallclock=self.playhead_wallclock,
        )
        self.scheduler.schedule_messages(msgs)
        self.metrics.log_chunk(
            ChunkMetric(
                run_id=getattr(self.llm, "run_id", "unknown"),
                timestamp=self.metrics.now(),
                parse_ok=parse_ok,
                fatal_error_count=fatal_count,
                repair_applied=repair_applied,
                quantize_delta=quant_delta,
                chunk_regen_count=regen_count,
                scheduler_late_count=self.scheduler.stats.late_count,
                event_count=len(chunk.events),
            )
        )
        self.next_bar_to_schedule += 1

    def _finish_playback_from_thread(self, reason: str) -> None:
        with self.lock:
            self.state.mode = "CHAT"
        self.play_stop_evt.set()
        if self.scheduler:
            self.scheduler.stop()
        if self.midi_out:
            self.midi_out.close()
        print(f"[midi] auto-stopped ({reason}); back to CHAT")

    def _generate_chunk_batch(
        self,
        start_bar: int,
        style: str,
        regen_hint: str,
        bars_to_generate: int,
        allow_end_signal: bool,
        fill_missing: bool,
    ) -> tuple[list[Chunk], str, bool]:
        attempts = 0

        while attempts < self.cfg.max_regen_attempts:
            ctx = LLMContext(
                bar=start_bar,
                bpm=self.meta.bpm,
                meter_num=self.meta.meter_num,
                style=style,
                regen_hint=regen_hint,
                attempt=attempts + 1,
                bars_to_generate=bars_to_generate,
                allow_end_signal=allow_end_signal,
            )
            try:
                raw = self.llm.generate_chunks(ctx)
            except Exception as exc:
                attempts += 1
                regen_hint = f"Rewrite: llm error: {exc}"
                print(f"[midi] llm generate failed attempt={attempts}: {exc}")
                continue
            body, got_end = strip_end_signal(raw)
            if got_end and "@chunk" not in body:
                return [], "", True
            try:
                chunks = parse_chunks(body)
            except ParseError as exc:
                attempts += 1
                regen_hint = f"Rewrite: parse error: {exc}"
                continue

            out_by_bar: dict[int, Chunk] = {}
            for ch in chunks:
                if ch.from_bar != ch.to_bar:
                    continue
                v0 = validate(ch, self.meta, self.track)
                repaired, rep = repair(ch, self.meta, self.track)
                v1 = validate(repaired, self.meta, self.track)
                if v1.fatal_errors or rep.too_much_fix:
                    continue
                out_by_bar[repaired.from_bar] = repaired

            if fill_missing:
                ordered: list[Chunk] = []
                for bar in range(start_bar, start_bar + bars_to_generate):
                    ordered.append(out_by_bar.get(bar, self._fallback_chunk(bar)))
                return ordered, "", got_end

            # non-fill mode: keep contiguous generated bars only
            ordered = []
            bar = start_bar
            while bar in out_by_bar:
                ordered.append(out_by_bar[bar])
                bar += 1
            if not ordered and start_bar in out_by_bar:
                ordered = [out_by_bar[start_bar]]
            return ordered, "", got_end

        # hard fail -> at least return fallback for first bar
        return [self._fallback_chunk(start_bar)], regen_hint, False

    def _fallback_chunk(self, bar: int) -> Chunk:
        return Chunk(
            from_bar=bar,
            to_bar=bar,
            events=[
                # simple C major dyad pad, one bar
                self._ev(0.0, 4.0, [60, 67], 70),
            ],
        )

    @staticmethod
    def _ev(t: float, d: float, notes: list[int], v: int):
        from .dsl import NoteEvent

        return NoteEvent(t=t, d=d, notes=notes, v=v)


def main() -> None:
    app = MidiAgentApp()
    app.run_cli()


if __name__ == "__main__":
    main()
