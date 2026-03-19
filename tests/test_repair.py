import unittest

from midi_agent.dsl import Chunk, Meta, NoteEvent, Track
from midi_agent.repair import repair
from midi_agent.validate import validate


def _meta():
    return Meta(bpm=120, meter_num=4, meter_den=4, grid_str="1/16", bars=8)


def _track():
    return Track(name="piano", program=0, channel=0)


class TestRepair(unittest.TestCase):
    def test_repair_quantize_and_truncate_and_clamp(self):
        chunk = Chunk(
            from_bar=0,
            to_bar=0,
            events=[
                NoteEvent(t=0.10, d=0.90, notes=[-4, 130], v=200),
                NoteEvent(t=3.75, d=1.00, notes=[60], v=80),
            ],
        )

        repaired, report = repair(chunk, _meta(), _track())

        self.assertGreater(report.quantize_total_abs_delta, 0)
        self.assertGreaterEqual(report.num_truncated, 1)

        e0 = repaired.events[0]
        self.assertEqual(e0.t, 0.0)
        self.assertEqual(e0.d, 1.0)
        self.assertEqual(e0.notes, [0, 127])
        self.assertEqual(e0.v, 127)

        e1 = repaired.events[1]
        self.assertEqual(e1.t, 3.75)
        self.assertEqual(e1.d, 0.25)

    def test_repair_fixes_overlap_by_shortening_earlier(self):
        chunk = Chunk(
            from_bar=0,
            to_bar=0,
            events=[
                NoteEvent(t=0.0, d=2.0, notes=[60], v=80),
                NoteEvent(t=1.0, d=1.0, notes=[60], v=90),
            ],
        )
        repaired, report = repair(chunk, _meta(), _track())
        self.assertGreaterEqual(report.num_overlap_fixed, 1)

        result = validate(repaired, _meta(), _track())
        self.assertEqual(result.fatal_errors, [])

    def test_repair_too_much_fix_flagged_for_heavy_quantization(self):
        chunk = Chunk(
            from_bar=0,
            to_bar=0,
            events=[
                NoteEvent(t=0.12, d=0.12, notes=[60], v=80),
                NoteEvent(t=0.37, d=0.12, notes=[62], v=80),
                NoteEvent(t=0.62, d=0.12, notes=[64], v=80),
                NoteEvent(t=0.87, d=0.12, notes=[65], v=80),
            ],
        )
        _, report = repair(chunk, _meta(), _track())
        self.assertTrue(report.too_much_fix)


if __name__ == "__main__":
    unittest.main()
