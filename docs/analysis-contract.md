# SceneBid analysis contract v1.0

`analysis-worker/main.py` writes `analysis.json` using schema version `1.0`.
Every interval is a floating-point second range on the original source
timeline, `[start_sec, end_sec)`. `video.duration_sec` comes from `ffprobe`.

The worker discovers shots with PySceneDetect, samples actual frames, and
transcribes actual audio with faster-whisper. Vision annotations are evidence
from those frames and the overlapping transcript. Adjacent shots are grouped
only when model annotations share a category or advertiser; otherwise a
shot-level `unknown` segment is retained. Group boundaries are predictions,
and `boundary_source`/`boundary_evidence` preserve that fact.

`ad_opportunities` are rule-generated candidates: the midpoint of a predicted
commercial segment through at most five seconds. They are not model-selected.
Unknown or unsafe `brand_safety` must produce no fill.

The worker never reads campaigns, answer keys, chapter lists, or existing
annotations. Evaluation belongs in a separate post-inference command/module.

For the overlay demo, `scenebid decide` derives `data/output/TV_Commercials_1977/opportunities.json`
from actual segment windows when the worker did not emit opportunities. These
are timing-rule candidates, not model-selected moments or verified boundaries.
The demo deliberately uses `DecideDemo`: it preserves and displays model
safety while ignoring it for this fictional bid evaluation. This is not SSAI,
OpenRTB, or a production auction.

Run without re-analysis:

```bash
go test ./...
go run ./cmd/scenebid decide
go run ./cmd/scenebid serve
# open http://localhost:8080
```

The server serves `/media/TV_Commercials_1977.m3u8` if an HLS playlist exists
under `data/input`; otherwise the browser falls back to
`/media/TV_Commercials_1977.mp4`. Generate HLS locally with:
`ffmpeg -i data/input/TV_Commercials_1977.mp4 -c:v copy -c:a aac -hls_time 6 -hls_playlist_type vod data/input/TV_Commercials_1977.m3u8`.
Category aliases are intentionally small and explicit: `camera` maps to
`cameras`, and `foods` maps to `food`; matching is otherwise case-insensitive.
The Go service reads this contract and independently reads fictional campaigns.

Window mode labels segments `analysis_window`; a fixed window is not a
verified commercial boundary and may contain multiple commercials. Per-shot
mode remains available for refinement. Runs store compatible checkpoints under
`output/runs/<cache-key>/`; `--resume` only reuses a matching input identity,
model, sampling, prompt, and schema configuration. Partial checkpoints are
never presented as completed final output.
