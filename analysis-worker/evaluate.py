"""Optional post-inference comparison; never imported by the inference worker."""
import json

def evaluate(analysis_path, answer_key_path):
    with open(analysis_path) as f:
        analysis = json.load(f)
    with open(answer_key_path) as f:
        expected = json.load(f)
    predicted = [{"id": s["id"], "start_sec": s["start_sec"],
                 "end_sec": s["end_sec"], "kind": s.get("kind")}
                for s in analysis.get("segments", [])]
    return {"predicted_segments": predicted,
            "answer_key": expected,
            "warning": "Predicted boundaries and model labels may be wrong."}
