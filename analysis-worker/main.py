import argparse
import json
import os
import shutil
import subprocess
import sys

from schema import SCHEMA_VERSION, TIMELINE_UNIT, group_shots
from shots import detect_shots, extract_frames
from transcription import transcribe
from scene_analysis import analyze_frames

def probe_duration(video):
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", video]
    try:
        return float(subprocess.check_output(command, text=True).strip())
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        raise RuntimeError(f"ffprobe duration failed: {exc}") from exc


def main():
    parser = argparse.ArgumentParser(description="SceneBid real video analysis worker")
    parser.add_argument("video", help="input MP4")
    parser.add_argument("output_dir", help="directory for generated analysis")
    parser.add_argument("--start", type=float, default=None)
    parser.add_argument("--end", type=float, default=None,
                        help="optional development limit; default is the complete video")
    parser.add_argument("--shot-threshold", type=float, default=27)
    parser.add_argument("--frames-per-shot", type=int, default=3)
    parser.add_argument("--whisper-model",
                        default=os.getenv("WHISPER_MODEL", "base"))
    parser.add_argument("--vision-provider",
                        default=os.getenv("VISION_PROVIDER", "ollama"))
    parser.add_argument("--vision-model",
                        default=os.getenv("VISION_MODEL", "qwen3-vl:8b"))
    parser.add_argument("--vision-endpoint",
                        default=os.getenv("VISION_ENDPOINT",
                                        "http://localhost:11434/api/chat"))
    parser.add_argument("--api-key",
                        default=os.getenv("VISION_API_KEY"))
    args = parser.parse_args()
    if not os.path.isfile(args.video):
        parser.error(f"input video does not exist: {args.video}")
    if args.start is not None and args.start < 0:
        parser.error("--start must be nonnegative")
    if args.end is not None and (args.end <= (args.start or 0)):
        parser.error("--end must be after --start")
    os.makedirs(args.output_dir, exist_ok=True)
    try:
        frames_dir = os.path.join(args.output_dir, "frames")
        shutil.rmtree(frames_dir, ignore_errors=True)
        shots = detect_shots(args.video, args.shot_threshold, args.start, args.end)
        if not shots:
            raise RuntimeError("no shots detected in the requested range")
        frames = extract_frames(args.video, shots, os.path.join(args.output_dir, "frames"),
                                args.frames_per_shot)
        transcript = transcribe(args.video, args.whisper_model, start=args.start, end=args.end)
        scenes = analyze_frames(frames, shots, transcript, args.vision_provider,
                                args.vision_model, args.vision_endpoint, args.api_key)
        for shot in shots:
            shot["sampled_frames"] = [
                {"time_sec": f["time_sec"],
                 "path": os.path.relpath(f["path"], args.output_dir)}
                for f in frames if f["shot_index"] == shots.index(shot)]
        segments = group_shots(shots, scenes, transcript)
        for segment in segments:
            source_shots = [s for s in shots if s["id"] in segment["shot_ids"]]
            annotations = [scenes[shots.index(s)] for s in source_shots]
            transcript_ids = [f"speech-{i+1:05d}" for i, t in enumerate(transcript["segments"])
                              if any(t["start_sec"] < s["end_sec"] and s["start_sec"] < t["end_sec"]
                                     for s in source_shots)]
            merged = annotations[0] if annotations else {}
            safe = merged.get("safety", "unknown")
            segment.update({
                "transcript_ids": transcript_ids,
                "analysis_status": "completed",
                "intelligence": {
                    "summary": merged.get("description"),
                    "categories": [{"id": c, "source": "vision_and_transcript", "evidence": []}
                                   for c in merged.get("categories", [])],
                    "entities": [{"type": "product", "name": p, "source": "vision_model",
                                  "evidence": []} for p in merged.get("products", [])],
                    "primary_advertiser": {"name": merged.get("advertiser"),
                                           "status": "identified" if merged.get("advertiser") else "unknown",
                                           "evidence": []},
                    "brand_safety": {"status": safe, "method": "vision_model",
                                     "reasons": merged.get("unknowns", [])},
                },
                "ad_opportunities": [{
                    "id": f"opportunity-{len(segments):05d}",
                    "format": "overlay",
                    "start_sec": segment["start_sec"] + (segment["end_sec"]-segment["start_sec"])/2,
                    "end_sec": min(segment["end_sec"], segment["start_sec"] +
                                   (segment["end_sec"]-segment["start_sec"])/2 + 5.0),
                    "placement_source": "timing_rule", "status": "candidate",
                    "reason": "middle-of-segment rule; candidate only",
                }] if segment["kind"] == "predicted_commercial" else []
            })
        result = {"schema_version": SCHEMA_VERSION,
                  "video": {"id": os.path.splitext(os.path.basename(args.video))[0],
                            "source_file": os.path.abspath(args.video),
                            "duration_sec": probe_duration(args.video),
                            "timeline_unit": TIMELINE_UNIT},
                  "analysis": {"run_id": f"run-{int(__import__('time').time())}",
                               "status": "completed",
                               "models": {"speech": {"provider": "faster-whisper", "model": args.whisper_model},
                                          "vision": {"provider": args.vision_provider, "model": args.vision_model}}},
                  "shots": shots,
                  "transcript": [{"id": f"speech-{i+1:05d}", **s}
                                 for i, s in enumerate(transcript["segments"])],
                  "segments": segments, "errors": []}
        with open(os.path.join(args.output_dir, "analysis.json"), "w") as output:
            json.dump(result, output, indent=2)
        for name, value in (("transcript.json", result["transcript"]),):
            with open(os.path.join(args.output_dir, name), "w") as output:
                json.dump(value, output, indent=2)
    except Exception as exc:
        print(f"SceneBid analysis failed: {exc}", file=sys.stderr)
        return 1
    print(f"Analyzed {len(shots)} shots and wrote {args.output_dir}/analysis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
