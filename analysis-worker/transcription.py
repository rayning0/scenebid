from faster_whisper import WhisperModel
import subprocess
import numpy as np

def decode_audio(video_path, start=None, end=None):
    command = ["ffmpeg", "-v", "error"]
    if start is not None:
        command += ["-ss", str(start)]
    command += ["-i", video_path]
    if end is not None:
        command += ["-t", str(end - (start or 0))]
    command += ["-f", "s16le", "-ac", "1", "-ar", "16000", "pipe:1"]
    try:
        raw = subprocess.check_output(command)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"audio extraction failed: {exc}") from exc
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def transcribe(video_path, model_name="base", device="cpu", compute_type=None,
               start=None, end=None):
    if compute_type is None:
        compute_type = "float32" if device == "mps" else "int8"
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    audio = decode_audio(video_path, start, end)
    segments, info = model.transcribe(audio, vad_filter=True)
    return {
        "model": model_name,
        "language": getattr(info, "language", None),
        "segments": [{"start_sec": float(s.start + (start or 0)),
                      "end_sec": float(s.end + (start or 0)),
                      "text": (s.text or "").strip()} for s in segments],
    }

