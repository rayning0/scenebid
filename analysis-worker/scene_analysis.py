import base64
import json
import os
import urllib.request


def transcript_excerpt(segments, start, end):
    return " ".join(s["text"] for s in segments
                    if s["end_sec"] >= start and s["start_sec"] <= end).strip()


def analyze_frames(frames, shots, transcript, provider, model, endpoint=None,
                   api_key=None):
    if provider not in ("openai_compatible", "ollama"):
        raise ValueError("VISION_PROVIDER must be openai_compatible or ollama; a vision model is required")
    if not endpoint:
        endpoint = "http://localhost:11434/api/chat" if provider == "ollama" else "https://api.openai.com/v1/chat/completions"
    scenes = []
    for index, shot in enumerate(shots):
        evidence = [f for f in frames if f["shot_index"] == index]
        images = []
        for item in evidence:
            with open(item["path"], "rb") as image:
                images.append({"type": "image_url", "image_url": {
                    "url": "data:image/jpeg;base64," + base64.b64encode(image.read()).decode()}})
        prompt = (
            "Analyze only the supplied video-frame evidence and transcript. Return JSON with "
            "description (string), categories (array of short strings), advertiser (string or null), "
            "products (array), safety (safe|unknown|unsafe), confidence (0..1), unknowns (array). "
            "Do not infer details not supported by evidence. Transcript: " +
            transcript_excerpt(transcript["segments"], shot["start_sec"], shot["end_sec"])
        )
        if provider == "ollama":
            payload = {"model": model, "stream": False, "think": False,
                       "options": {"num_ctx": 4096, "num_predict": 384,
                                   "temperature": 0},
                       "format": "json", "messages": [{"role": "user", "content": prompt,
                       "images": [item["image_url"]["url"].split(",", 1)[1] for item in images]}]}
        else:
            payload = {"model": model, "temperature": 0,
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + images}]}
        request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json",
                                                  **({"Authorization": f"Bearer {api_key}"} if api_key else {})})
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body = json.loads(response.read())
            content = body["message"]["content"] if provider == "ollama" else body["choices"][0]["message"]["content"]
            annotation = json.loads(content)
        except Exception as exc:
            raise RuntimeError(f"vision provider failed for shot {index}: {exc}") from exc
        annotation.update({
            "id": f"scene-{index:05d}", "start_sec": shot["start_sec"],
            "end_sec": shot["end_sec"], "frame_evidence": evidence,
            "transcript_excerpt": transcript_excerpt(transcript["segments"], shot["start_sec"], shot["end_sec"]),
            "model": model, "provider": provider,
        })
        scenes.append(annotation)
    return scenes

