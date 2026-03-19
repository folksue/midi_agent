import unittest

from benchmark.core.musicology import EXPLANATION_POLICY, label_task_explanation


class TestBenchmarkMusicology(unittest.TestCase):
    def test_explanation_policy_is_hybrid(self):
        self.assertEqual(EXPLANATION_POLICY["mode"], "hybrid")

    def test_interval_explanation_mentions_interval(self):
        payload = {"notes": [60, 67]}
        text = label_task_explanation("task1_interval_identification", payload, "perfect_fifth")
        self.assertIn("7 semitones", text)
        self.assertIn("perfect fifth", text)

    def test_harmonic_function_explanation_mentions_key_and_function(self):
        payload = {"key": "C_major", "chord": "G_major"}
        text = label_task_explanation("task3_harmonic_function", payload, "dominant")
        self.assertIn("C major", text)
        self.assertIn("dominant", text)


if __name__ == "__main__":
    unittest.main()
