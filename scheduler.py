from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass

from .midi_compile import ScheduledMessage


@dataclass
class SchedulerStats:
    sent_count: int = 0
    late_count: int = 0


class RealtimeScheduler:
    def __init__(self, send_func, sleep_granularity: float = 0.001):
        self._send = send_func
        self._q: queue.PriorityQueue[tuple[float, int, object]] = queue.PriorityQueue()
        self._stop = threading.Event()
        self._th: threading.Thread | None = None
        self._counter = 0
        self._sleep_granularity = sleep_granularity
        self.stats = SchedulerStats()

    @staticmethod
    def now() -> float:
        return time.perf_counter()

    def start(self) -> None:
        if self._th and self._th.is_alive():
            return
        self._stop.clear()
        self._th = threading.Thread(target=self._run, name="midi-scheduler", daemon=True)
        self._th.start()

    def stop(self) -> None:
        self._stop.set()
        if self._th:
            self._th.join(timeout=1.0)

    def schedule_messages(self, msgs: list[ScheduledMessage]) -> None:
        for sm in msgs:
            self._counter += 1
            self._q.put((sm.timestamp, self._counter, sm.message))

    def queued_count(self) -> int:
        return self._q.qsize()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                ts, _, msg = self._q.get(timeout=0.01)
            except queue.Empty:
                continue

            while True:
                now = self.now()
                dt = ts - now
                if dt <= 0:
                    if -dt > 0.005:
                        self.stats.late_count += 1
                    try:
                        self._send(msg)
                        self.stats.sent_count += 1
                    except Exception:
                        pass
                    break
                if dt > self._sleep_granularity:
                    time.sleep(min(dt / 2.0, self._sleep_granularity))
                else:
                    # final spin for better timing
                    time.sleep(0)
