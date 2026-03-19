import unittest

from benchmark.core.predictions import (
    get_prediction_explanation,
    get_prediction_label,
    get_prediction_notes,
    make_prediction_row,
)


class TestBenchmarkPredictions(unittest.TestCase):
    def test_get_prediction_label_prefers_canonical_field(self):
        row = {
            "prediction_label": "dominant",
            "prediction": "tonic",
        }
        self.assertEqual(get_prediction_label(row, "task3_harmonic_function"), "dominant")

    def test_get_prediction_notes_prefers_structured_payload(self):
        row = {
            "prediction_notes": "t=0 d=1 notes=[C4] v=80",
            "prediction_structured": [{"t": 0.0, "p": 62, "d": 1.0, "v": 80}],
        }
        notes = get_prediction_notes(row, "task5_transposition", "note_level")
        self.assertEqual(notes, [{"t": 0.0, "p": 62, "d": 1.0, "v": 80}])

    def test_make_prediction_row_sets_explanation_for_label_tasks(self):
        case = {"case_id": "c1", "task": "task3_harmonic_function"}
        row = make_prediction_row(case, "dominant", prediction_explanation="Analytical note")
        self.assertEqual(row["prediction_type"], "label")
        self.assertEqual(row["prediction_label"], "dominant")
        self.assertEqual(get_prediction_explanation(row), "Analytical note")

    def test_make_prediction_row_sets_prediction_notes_for_sequence_tasks(self):
        case = {"case_id": "c2", "task": "task7_retrograde"}
        row = make_prediction_row(case, "t=0 d=1 notes=[C4] v=80")
        self.assertEqual(row["prediction_type"], "notes")
        self.assertIn("prediction_notes", row)


if __name__ == "__main__":
    unittest.main()
