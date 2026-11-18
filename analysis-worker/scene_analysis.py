import base64
import json
import os
import sys
import urllib.request
import urllib.error
import time


def transcript_excerpt(segments, start, end):
    return " ".join(s["text"] for s in segments
                    if s["end_sec"] >= start and s["start_sec"] <= end).strip()


def analyze_frames(frames, shots, transcript, provider, model, endpoint=None,
                   api_key=None, max_tokens=512, timeout=180, on_result=None):
    if provider not in ("openai_compatible", "ollama"):
        raise ValueError("VISION_PROVIDER must be openai_compatible or ollama; a vision model is required")
    if not endpoint:
        endpoint = "http://localhost:11434/api/chat" if provider == "ollama" else "https://api.openai.com/v1/chat/completions"
    scenes = []
    started = time.monotonic()
    total = len(shots)
    for index, shot in enumerate(shots):
        evidence = [f for f in frames if f["shot_index"] == index]
        if shot["id"].startswith("window-"):
            evidence = evidence[:2]
        images = []
        for item in evidence:
            with open(item["path"], "rb") as image:
                images.append({"type": "image_url", "image_url": {
                    "url": "data:image/jpeg;base64," + base64.b64encode(image.read()).decode()}})
        prompt = (
            "Analyze only the supplied video-frame evidence and transcript. Return ONLY one compact "
            "JSON object; do not provide reasoning, chain-of-thought, markdown, or explanations. "
            "Use at most 12 words for description, 5 categories, 5 products, and 3 unknowns. "
            "Return keys description (string), categories (array of short strings), advertiser "
            "(string or null), products (array), safety (safe|unknown|unsafe), confidence (number "
            "0..1), and unknowns (array). Use null or [] when unknown. "
            "Do not infer details not supported by evidence. Transcript: " +
            transcript_excerpt(transcript["segments"], shot["start_sec"], shot["end_sec"])
        )
        if provider == "ollama":
            payload = {"model": model, "stream": False, "think": False,
                       "options": {"num_ctx": 4096, "num_predict": max_tokens,
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
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read())
            content = body["message"]["content"] if provider == "ollama" else body["choices"][0]["message"]["content"]
            if provider == "ollama" and not content.strip():
                # Some Qwen builds spend the first response entirely in the
                # hidden reasoning channel for a long prompt. Retry compactly.
                payload["messages"][0]["content"] = (
                    "Return one compact JSON object only with keys "
                    "description, categories, advertiser, products, safety, "
                    "confidence, unknowns. Use null or [] when unknown."
                )
                with urllib.request.urlopen(
                    urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                                            headers={"Content-Type": "application/json"}),
                    timeout=timeout) as response:
                    retry_body = json.loads(response.read())
                content = retry_body["message"]["content"]
            if not content.strip():
                raise ValueError("vision provider returned empty content")
            annotation = json.loads(content)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"vision HTTP error window={shot.get('id')} "
                  f"range={shot['start_sec']:.3f}-{shot['end_sec']:.3f}s "
                  f"status={exc.code} body={body}", file=sys.stderr, flush=True)
            raise RuntimeError(
                f"vision provider failed for {shot.get('id')} "
                f"{shot['start_sec']:.3f}-{shot['end_sec']:.3f}s: HTTP {exc.code}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"vision provider failed for {shot.get('id')} "
                               f"{shot['start_sec']:.3f}-{shot['end_sec']:.3f}s: {exc}") from exc
        annotation.update({
            "id": f"scene-{index:05d}", "start_sec": shot["start_sec"],
            "end_sec": shot["end_sec"], "frame_evidence": evidence,
            "frame_count_sent": len(evidence),
            "frame_ids_sent": [f.get("path") for f in evidence],
            "transcript_excerpt": transcript_excerpt(transcript["segments"], shot["start_sec"], shot["end_sec"]),
            "model": model, "provider": provider,
        })
        scenes.append(annotation)
        if on_result:
            on_result(index, shot, annotation)
        elapsed = time.monotonic() - started
        average = elapsed / (index + 1)
        remaining = average * (total - index - 1)
        print(f"vision {index + 1}/{total} {shot['start_sec']:.2f}-{shot['end_sec']:.2f}s "
              f"elapsed={elapsed:.1f}s avg={average:.1f}s eta={remaining:.1f}s",
              flush=True)
    return scenes

