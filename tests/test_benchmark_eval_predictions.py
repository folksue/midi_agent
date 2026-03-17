import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmark.scripts import eval_predictions


class TestBenchmarkEvalPredictions(unittest.TestCase):
    def test_eval_predictions_handles_label_and_sequence_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gold_path = root / "gold.jsonl"
            pred_path = root / "pred.jsonl"
            out_path = root / "eval.json"

            gold_rows = [
                {
                    "id": "task3-1",
                    "task": "task3_harmonic_function",
                    "ground_truth": "dominant",
                    "target": "dominant",
                    "payload": {"key": "C_major", "chord": "G"},
                    "target_payload": "dominant",
                    "meta": {"tokenizer": "note_level"},
                },
                {
                    "id": "task3-2",
                    "task": "task3_harmonic_function",
                    "ground_truth": "tonic",
                    "target": "tonic",
                    "payload": {"key": "C_major", "chord": "C"},
                    "target_payload": "tonic",
                    "meta": {"tokenizer": "note_level"},
                },
                {
                    "id": "task4-1",
                    "task": "task4_transposition",
                    "ground_truth": "t=0 d=1 notes=[62] v=80 | t=1 d=1 notes=[64] v=80",
                    "target": "t=0 d=1 notes=[62] v=80 | t=1 d=1 notes=[64] v=80",
                    "payload": {
                        "melody": [
                            {"t": 0.0, "p": 60, "d": 1.0, "v": 80},
                            {"t": 1.0, "p": 62, "d": 1.0, "v": 80},
                        ]
                    },
                    "target_payload": [
                        {"t": 0.0, "p": 62, "d": 1.0, "v": 80},
                        {"t": 1.0, "p": 64, "d": 1.0, "v": 80},
                    ],
                    "meta": {"tokenizer": "note_level"},
                },
            ]
            pred_rows = [
                {"id": "task3-1", "prediction_label": "dominant", "prediction": "dominant"},
                {"id": "task3-2", "prediction_label": "dominant", "prediction": "dominant"},
                {
                    "id": "task4-1",
                    "prediction_notes": "t=0 d=1 notes=[62] v=80 | t=1 d=1 notes=[64] v=80",
                    "prediction_structured": [
                        {"t": 0.0, "p": 62, "d": 1.0, "v": 80},
                        {"t": 1.0, "p": 64, "d": 1.0, "v": 80},
                    ],
                },
            ]

            gold_path.write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in gold_rows) + "\n",
                encoding="utf-8",
            )
            pred_path.write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in pred_rows) + "\n",
                encoding="utf-8",
            )

            argv = [
                "eval_predictions.py",
                "--gold",
                str(gold_path),
                "--pred",
                str(pred_path),
                "--out",
                str(out_path),
            ]
            with patch("sys.argv", argv):
                rc = eval_predictions.main()

            self.assertEqual(rc, 0)
            result = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertAlmostEqual(result["overall"]["accuracy"], 2 / 3)
            self.assertAlmostEqual(result["by_task"]["task3_harmonic_function"]["accuracy"], 0.5)
            self.assertIn("macro_f1", result["by_task"]["task3_harmonic_function"])
            self.assertAlmostEqual(result["by_task"]["task4_transposition"]["exact_match"], 1.0)


if __name__ == "__main__":
    unittest.main()
