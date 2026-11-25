import unittest
from types import SimpleNamespace
import tempfile
import json

from pipeline import annotation_ids_for_segment, window_index_for_time, _cache_key


class PipelineMappingTests(unittest.TestCase):
    def test_range_is_part_of_checkpoint_key(self):
        with tempfile.NamedTemporaryFile() as video:
            common = dict(vision_provider="ollama", vision_endpoint="http://x",
                          vision_model="model", vision_mode="window",
                          window_sec=15, shot_threshold=27, frames_per_shot=2,
                          start=0, end=60, whisper_model="base", whisper_device="cpu",
                          vision_max_tokens=512, vision_timeout=180,
                          api_key=None)
            one_minute = _cache_key(video.name, SimpleNamespace(**common))
            common["whisper_device"] = "mps"
            gpu = _cache_key(video.name, SimpleNamespace(**common))
            self.assertNotEqual(one_minute, gpu)
            common["whisper_device"] = "cpu"
            common["end"] = None
            full_video = _cache_key(video.name, SimpleNamespace(**common))
            self.assertNotEqual(one_minute, full_video)

    def test_checkpoint_settings_exclude_api_key(self):
        settings = {"vision_model": "model", "api_key_configured": True}
        self.assertNotIn('"api_key":', json.dumps(settings))

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
