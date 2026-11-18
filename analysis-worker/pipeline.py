"""Checkpointed, window-oriented analysis runner."""
import hashlib
import json
import os
import tempfile
import time
import subprocess

from schema import SCHEMA_VERSION, TIMELINE_UNIT
from shots import detect_shots, extract_frames
from transcription import transcribe
from scene_analysis import analyze_frames

def window_index_for_time(time_sec, start_sec, window_sec, count):
    index = int((time_sec - start_sec) // window_sec)
    return max(0, min(index, count - 1))

def annotation_ids_for_segment(segment, annotations):
    return [annotations[unit_id] for unit_id in segment.get("shot_ids", [])
            if unit_id in annotations]

def intelligence_from_annotation(annotation):
    if not annotation:
        return {"summary": None, "categories": [], "entities": [],
                "primary_advertiser": {"name": None, "status": "unknown", "evidence": []},
                "brand_safety": {"status": "unknown", "method": "not_evaluated", "reasons": []}}
    return {
        "summary": annotation.get("description"),
        "categories": [{"id": value, "source": "vision_and_transcript",
                        "evidence": annotation.get("frame_evidence", [])}
                       for value in annotation.get("categories", [])],
        "entities": [{"type": "product", "name": value, "source": "vision_model",
                      "evidence": annotation.get("frame_evidence", [])}
                     for value in annotation.get("products", [])],
        "primary_advertiser": {"name": annotation.get("advertiser"),
                               "status": "identified" if annotation.get("advertiser") else "unknown",
                               "evidence": []},
        "brand_safety": {"status": annotation.get("safety", "unknown"),
                         "method": "vision_model", "reasons": annotation.get("unknowns", [])}}


def _write(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".tmp-", dir=os.path.dirname(path))
    with os.fdopen(fd, "w") as output:
        json.dump(value, output, indent=2)
    os.replace(temporary, path)


def _cache_key(video, args):
    stat = os.stat(video)
    identity = f"{os.path.abspath(video)}:{stat.st_size}:{stat.st_mtime_ns}"
    settings = {
        "schema": SCHEMA_VERSION, "prompt": "compact-v2",
        "provider": args.vision_provider, "endpoint": args.vision_endpoint,
        "model": args.vision_model, "mode": args.vision_mode,
        "window_sec": args.window_sec, "threshold": args.shot_threshold,
        "frames": args.frames_per_shot, "start": args.start, "end": args.end,
        "whisper_model": args.whisper_model,
        "vision_max_tokens": args.vision_max_tokens,
        "vision_timeout": args.vision_timeout,
        "api_key_configured": bool(args.api_key),
    }
    return hashlib.sha256((identity + json.dumps(settings, sort_keys=True)).encode()).hexdigest()[:16]

def _source_duration(video):
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", video]
    return float(subprocess.check_output(command, text=True).strip())


def run(args):
    started = time.monotonic()
    key = _cache_key(args.video, args)
    run_dir = os.path.join(args.output_dir, "runs", key)
    checkpoint = os.path.join(run_dir, "checkpoint.json")
    os.makedirs(run_dir, exist_ok=True)
    settings = {name: value for name, value in vars(args).items()
                if name != "api_key"}
    settings["api_key_configured"] = bool(args.api_key)
    state = {"cache_key": key, "status": "partial", "errors": [],
             "settings": settings, "run_id": f"run-{int(time.time())}"}
    if args.resume and os.path.exists(checkpoint):
        with open(checkpoint) as source:
            state = json.load(source)
        if state.get("cache_key") != key:
            raise RuntimeError("checkpoint cache mismatch; use a new run or compatible settings")
        print(f"resuming compatible checkpoint {key}", flush=True)

    if "shots" not in state:
        state["shots"] = detect_shots(args.video, args.shot_threshold, args.start, args.end)
        _write(checkpoint, state)
        print(f"checkpointed {len(state['shots'])} shots", flush=True)
    shots = state["shots"]
    if "frames" not in state:
        frame_dir = os.path.join(run_dir, "frames")
        frames = extract_frames(args.video, shots, frame_dir, args.frames_per_shot)
        for frame in frames:
            frame["shot_id"] = shots[frame["shot_index"]]["id"]
            frame["path"] = os.path.relpath(frame["path"], args.output_dir)
            frame["window_index"] = None
        state["frames"] = frames
        _write(checkpoint, state)
        print(f"checkpointed {len(frames)} frames", flush=True)
    if "transcript" not in state:
        state["transcript"] = transcribe(args.video, args.whisper_model,
                                         start=args.start, end=args.end)["segments"]
        _write(checkpoint, state)
        print(f"checkpointed {len(state['transcript'])} transcript segments", flush=True)

    start = shots[0]["start_sec"]
    end = shots[-1]["end_sec"]
    windows = []
    cursor = start
    while cursor < end:
        finish = min(end, cursor + args.window_sec)
        windows.append({"id": f"window-{len(windows)+1:05d}",
                        "start_sec": cursor, "end_sec": finish,
                        "boundary_source": "fixed_time_window"})
        cursor = finish
    for frame in state["frames"]:
        frame["window_index"] = window_index_for_time(
            frame["time_sec"], start, args.window_sec, len(windows))
    pending = [w for i, w in enumerate(windows)
               if f"window-{i+1:05d}" not in state.get("annotations", {})]
    if "annotations" not in state:
        state["annotations"] = {}

    def save_result(index, unit, annotation):
        state["annotations"][unit["id"]] = annotation
        _write(checkpoint, state)

    local_frames = []
    for local_index, unit in enumerate(pending):
        unit_index = windows.index(unit)
        for frame in [f for f in state["frames"]
                      if f["window_index"] == unit_index][:2]:
            copy = dict(frame)
            copy["path"] = os.path.join(args.output_dir, frame["path"])
            copy["shot_index"] = local_index
            local_frames.append(copy)
    analyze_frames(local_frames, pending, {"segments": state["transcript"]},
                   args.vision_provider, args.vision_model, args.vision_endpoint,
                   args.api_key, args.vision_max_tokens, args.vision_timeout,
                   save_result)

    segments = []
    for i, window in enumerate(windows):
        annotation = state["annotations"].get(window["id"])
        status = "completed" if annotation else "failed"
        segments.append({
            "id": f"segment-{i+1:05d}", "kind": "analysis_window",
            "start_sec": window["start_sec"], "end_sec": window["end_sec"],
            "boundary_source": "fixed_time_window",
            "boundary_evidence": ["Fixed analysis window; may cross a commercial boundary."],
            "shot_ids": [s["id"] for s in shots
                         if s["start_sec"] < window["end_sec"] and window["start_sec"] < s["end_sec"]],
            "analysis_status": status, "window_id": window["id"],
            "intelligence": intelligence_from_annotation(annotation),
            "ad_opportunities": []
        })
    result = {"schema_version": SCHEMA_VERSION,
              "video": {"id": os.path.splitext(os.path.basename(args.video))[0],
                        "source_file": os.path.abspath(args.video),
                        "duration_sec": _source_duration(args.video),
                        "analyzed_range": {"start_sec": args.start or 0.0,
                                           "end_sec": args.end or _source_duration(args.video)},
                        "timeline_unit": TIMELINE_UNIT},
              "analysis": {"run_id": state["run_id"], "status": "completed",
                           "vision_mode": "window", "cache_key": key,
                           "effective_settings": settings,
                           "models": {"speech": {"provider": "faster-whisper", "model": args.whisper_model},
                                      "vision": {"provider": args.vision_provider, "model": args.vision_model}}},
              "shots": shots, "transcript": state["transcript"],
              "segments": segments, "errors": state["errors"]}
    _write(os.path.join(args.output_dir, "analysis.json"), result)
    _write(os.path.join(args.output_dir, "transcript.json"), state["transcript"])
    state["status"] = "completed"
    _write(checkpoint, state)
    print(f"completed in {time.monotonic()-started:.1f}s: {len(windows)} windows", flush=True)
