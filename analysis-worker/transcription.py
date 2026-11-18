from faster_whisper import WhisperModel


def transcribe(video_path, model_name="base", device="cpu", compute_type="int8",
               start=None, end=None):
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, info = model.transcribe(video_path, vad_filter=True,
                                       clip_timestamps=(start, end) if start is not None or end is not None else None)
    return {
        "model": model_name,
        "language": getattr(info, "language", None),
        "segments": [{"start_sec": float(s.start), "end_sec": float(s.end),
                      "text": (s.text or "").strip()} for s in segments],
    }

