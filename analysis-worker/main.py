import argparse
import json
import os
import sys

from schema import SCHEMA_VERSION
from shots import detect_shots, extract_frames
from transcription import transcribe
from scene_analysis import analyze_frames
from visual_search import embed_frames


def main():
    parser = argparse.ArgumentParser(description="SceneBid real video analysis worker")
    parser.add_argument("video", help="input MP4")
    parser.add_argument("output_dir", help="directory for generated analysis")
    parser.add_argument("--start", type=float, default=None)
    parser.add_argument("--end", type=float, default=None)
    parser.add_argument("--shot-threshold", type=float, default=27)
    parser.add_argument("--frames-per-shot", type=int, default=3)
    parser.add_argument("--clip-model",
                        default=os.getenv("CLIP_MODEL", "clip-ViT-B-32"))
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
        shots = detect_shots(args.video, args.shot_threshold, args.start, args.end)
        if not shots:
            raise RuntimeError("no shots detected in the requested range")
        frames = extract_frames(args.video, shots, os.path.join(args.output_dir, "frames"),
                                args.frames_per_shot)
        frames = embed_frames(frames, args.clip_model)
        transcript = transcribe(args.video, args.whisper_model, start=args.start, end=args.end)
        scenes = analyze_frames(frames, shots, transcript, args.vision_provider,
                                args.vision_model, args.vision_endpoint, args.api_key)
        result = {"schema_version": SCHEMA_VERSION, "video": os.path.abspath(args.video),
                  "range": {"start_sec": args.start, "end_sec": args.end},
                  "shots": shots, "frames": frames, "transcript": transcript,
                  "scenes": scenes}
        with open(os.path.join(args.output_dir, "analysis.json"), "w") as output:
            json.dump(result, output, indent=2)
        for name, value in (("shots.json", shots), ("transcript.json", transcript),
                            ("scenes.json", scenes)):
            with open(os.path.join(args.output_dir, name), "w") as output:
                json.dump(value, output, indent=2)
    except Exception as exc:
        print(f"SceneBid analysis failed: {exc}", file=sys.stderr)
        return 1
    print(f"Analyzed {len(shots)} shots and wrote {args.output_dir}/analysis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
