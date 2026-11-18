import os
from typing import Optional

from scenedetect import SceneManager, VideoManager
from scenedetect.detectors import ContentDetector


def detect_shots(video_path: str, threshold: float = 27.0,
                 start: Optional[float] = None, end: Optional[float] = None):
    """Detect content cuts in the requested portion of the actual video."""
    manager = VideoManager([video_path])
    if start is not None or end is not None:
        manager.set_duration(start_time=start or 0, end_time=end)
    detector = SceneManager()
    detector.add_detector(ContentDetector(threshold=threshold))
    manager.set_downscale_factor()
    manager.start()
    try:
        detector.detect_scenes(frame_source=manager)
        scenes = detector.get_scene_list()
    finally:
        manager.release()
    return [{"start_sec": float(s.get_seconds()),
             "end_sec": float(e.get_seconds())} for s, e in scenes]


def extract_frames(video_path, shots, output_dir, frames_per_shot=3):
    """Extract timestamped JPEG evidence with ffmpeg; fail on extraction errors."""
    import subprocess
    os.makedirs(output_dir, exist_ok=True)
    result = []
    for index, shot in enumerate(shots):
        start, finish = shot["start_sec"], shot["end_sec"]
        count = max(1, frames_per_shot)
        for frame_index in range(count):
            ratio = (frame_index + 1) / (count + 1)
            timestamp = start + (finish - start) * ratio
            path = os.path.join(output_dir, f"shot-{index:05d}-{frame_index:02d}.jpg")
            command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                       "-ss", f"{timestamp:.3f}", "-i", video_path,
                       "-frames:v", "1", "-q:v", "2", path]
            try:
                subprocess.run(command, check=True)
            except (OSError, subprocess.CalledProcessError) as exc:
                raise RuntimeError(f"frame extraction failed at {timestamp:.3f}s: {exc}") from exc
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                raise RuntimeError(f"ffmpeg produced an empty frame at {timestamp:.3f}s")
            result.append({"path": path, "timestamp_sec": timestamp,
                           "shot_index": index})
    return result

