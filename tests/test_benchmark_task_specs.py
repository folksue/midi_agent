import unittest

from benchmark.core.task_specs import (
    ALL_TASKS,
    LABEL_TASKS,
    SEQUENCE_TASKS,
    TASK_GROUPS,
    label_space_for_task,
    prediction_kind_for_task,
    primary_prediction_field_for_task,
)


class TestBenchmarkTaskSpecs(unittest.TestCase):
    def test_task_groups_cover_all_tasks(self):
        combined = set(LABEL_TASKS) | set(SEQUENCE_TASKS)
        self.assertEqual(combined, set(ALL_TASKS))
        self.assertEqual(set(TASK_GROUPS["all"]), set(ALL_TASKS))

    def test_prediction_kind_and_primary_field_match_task_type(self):
        for task in LABEL_TASKS:
            self.assertEqual(prediction_kind_for_task(task), "label")
            self.assertEqual(primary_prediction_field_for_task(task), "prediction_label")
        for task in SEQUENCE_TASKS:
            self.assertEqual(prediction_kind_for_task(task), "notes")
            self.assertEqual(primary_prediction_field_for_task(task), "prediction_notes")

    def test_known_label_spaces_are_available(self):
        self.assertIn("perfect_fifth", label_space_for_task("task1_interval_identification"))
        self.assertIn("dominant", label_space_for_task("task3_harmonic_function"))
        self.assertIn("voice_crossing", label_space_for_task("task8_voice_leading"))


if __name__ == "__main__":
    unittest.main()
