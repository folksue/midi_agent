from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict


@dataclass
class ChunkMetric:
    run_id: str
    timestamp: float
    parse_ok: bool
    fatal_error_count: int
    repair_applied: bool
    quantize_delta: float
    chunk_regen_count: int
    scheduler_late_count: int
    event_count: int


class MetricsLogger:
    def __init__(self, path: str):
        self.path = path

    def log_chunk(self, metric: ChunkMetric) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metric), ensure_ascii=False) + "\n")

    @staticmethod
    def now() -> float:
        return time.time()
