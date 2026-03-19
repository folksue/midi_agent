import unittest

from midi_agent.dsl import ParseError, parse_chunk


class TestDSLParse(unittest.TestCase):
    def test_parse_chunk_ok_basic(self):
        text = """
        @chunk from_bar=0 to_bar=0
        t=0.00 d=1.00 notes=[60,64,67] v=80
        t=1.00 d=0.50 notes=[72] v=90
        @eochunk
        """
        chunk = parse_chunk(text)
        self.assertEqual(chunk.from_bar, 0)
        self.assertEqual(chunk.to_bar, 0)
        self.assertEqual(len(chunk.events), 2)
        self.assertEqual(chunk.events[0].notes, [60, 64, 67])

    def test_parse_chunk_ignores_comments_and_blank_lines(self):
        text = """

        # comment
        @chunk from_bar=2 to_bar=2

        t=0.25 d=0.25 notes=[60] v=70
        # another comment
        @eochunk
        """
        chunk = parse_chunk(text)
        self.assertEqual(chunk.from_bar, 2)
        self.assertEqual(chunk.to_bar, 2)
        self.assertEqual(len(chunk.events), 1)

    def test_parse_chunk_missing_eochunk_raises(self):
        text = """
        @chunk from_bar=0 to_bar=0
        t=0.00 d=1.00 notes=[60] v=80
        """
        with self.assertRaises(ParseError) as cm:
            parse_chunk(text)
        self.assertIn("@eochunk", str(cm.exception))

    def test_parse_chunk_bad_event_line_raises(self):
        text = """
        @chunk from_bar=0 to_bar=0
        t=bad d=1.00 notes=[60] v=80
        @eochunk
        """
        with self.assertRaises(ParseError):
            parse_chunk(text)


if __name__ == "__main__":
    unittest.main()
