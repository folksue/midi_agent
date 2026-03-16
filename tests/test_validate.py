import unittest

from midi_agent.dsl import Chunk, Meta, NoteEvent, Track
from midi_agent.validate import validate


def _meta():
    return Meta(bpm=120, meter_num=4, meter_den=4, grid_str="1/16", bars=8)


def _track():
    return Track(name="piano", program=0, channel=0)


class TestValidate(unittest.TestCase):
    def test_validate_ok_chunk(self):
        chunk = Chunk(
            from_bar=0,
            to_bar=0,
            events=[
                NoteEvent(t=0.0, d=1.0, notes=[60], v=80),
                NoteEvent(t=1.0, d=1.0, notes=[64], v=80),
                NoteEvent(t=2.0, d=1.0, notes=[67], v=80),
            ],
        )
        result = validate(chunk, _meta(), _track())
        self.assertEqual(result.fatal_errors, [])
        self.assertEqual(result.stats["event_count"], 3)

    def test_validate_offgrid_warns_and_suggests_fix(self):
        chunk = Chunk(
            from_bar=0,
            to_bar=0,
            events=[NoteEvent(t=0.1, d=1.0, notes=[60], v=80)],
        )
        result = validate(chunk, _meta(), _track())
        self.assertEqual(result.fatal_errors, [])
        self.assertEqual(result.stats["offgrid_count"], 1)
        self.assertTrue(result.fix_suggested)

    def test_validate_overlap_is_fatal(self):
        chunk = Chunk(
            from_bar=0,
            to_bar=0,
            events=[
                NoteEvent(t=0.0, d=2.0, notes=[60], v=80),
                NoteEvent(t=1.0, d=1.0, notes=[60], v=80),
            ],
        )
        result = validate(chunk, _meta(), _track())
        self.assertGreaterEqual(len(result.fatal_errors), 1)
        self.assertTrue(any("overlap" in err for err in result.fatal_errors))

    def test_validate_out_of_bounds_and_ranges_are_fatal(self):
        chunk = Chunk(
            from_bar=0,
            to_bar=0,
            events=[
                NoteEvent(t=-0.25, d=1.0, notes=[60], v=80),
                NoteEvent(t=3.5, d=1.0, notes=[128], v=0),
            ],
        )
        result = validate(chunk, _meta(), _track())
        self.assertTrue(any("t<0" in err for err in result.fatal_errors))
        self.assertTrue(any("exceeds chunk end" in err for err in result.fatal_errors))
        self.assertTrue(any("pitch out of range" in err for err in result.fatal_errors))
        self.assertTrue(any("velocity out of range" in err for err in result.fatal_errors))


if __name__ == "__main__":
    unittest.main()
