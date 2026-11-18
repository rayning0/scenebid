import unittest

from pipeline import annotation_ids_for_segment, window_index_for_time


class PipelineMappingTests(unittest.TestCase):
    def test_window_mapping_preserves_boundaries(self):
        self.assertEqual(window_index_for_time(0, 0, 15, 4), 0)
        self.assertEqual(window_index_for_time(14.99, 0, 15, 4), 0)
        self.assertEqual(window_index_for_time(15, 0, 15, 4), 1)
        self.assertEqual(window_index_for_time(60, 0, 15, 4), 3)

    def test_grouped_annotation_lookup_preserves_all_units(self):
        segment = {"shot_ids": ["window-00001", "window-00002"]}
        annotations = {"window-00001": {"x": 1}, "window-00002": {"x": 2}}
        self.assertEqual(annotation_ids_for_segment(segment, annotations),
                         [{"x": 1}, {"x": 2}])


if __name__ == "__main__":
    unittest.main()
