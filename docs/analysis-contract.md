# SceneBid analysis contract v1.0

`analysis-worker/main.py` writes `analysis.json` using schema version `1.0`.
Every interval is a floating-point second range on the original source
timeline, `[start_sec, end_sec)`. `video.duration_sec` comes from `ffprobe`.

The worker discovers shots with PySceneDetect, samples actual frames, and
transcribes actual audio with faster-whisper. Vision annotations are evidence
from those frames and the overlapping transcript. In per-shot mode, adjacent shots are grouped
only when model annotations share a category or advertiser; otherwise a
shot-level `unknown` segment is retained. Group boundaries are predictions,
and `boundary_source`/`boundary_evidence` preserve that fact.

The worker writes rule-generated candidates in `segments[].ad_opportunities`.
In window mode, a candidate starts at the window midpoint and ends five
seconds later or at the end of the window, whichever comes first.

The worker never reads campaigns, answer keys, chapter lists, or existing
annotations. Evaluation belongs in a separate post-inference command/module.

For the overlay demo, `scenebid serve` builds `/api/opportunities` from the
candidates in `analysis.json`, uses `transcript.json` for dialogue, and evaluates
fictional campaigns from `campaigns.json` when the browser calls `/api/decision`.
The optional `scenebid decide` command exports the candidates to
`opportunities.json` and simulated auction results to `decisions.json`.
Both Go commands default to a simulated bid floor of $2 CPM and accept
`-floor` for overrides.

Both commands use `DecideDemo`, which records the model's
`brand_safety` assessment in the decision trace and evaluates fictional bids
independently of that assessment. The separate `Decide` function requires
a scene to be explicitly marked safe before it can select a winner.

Run without re-analysis:

```bash
go test ./...
go run ./cmd/scenebid serve
open http://localhost:8080
```

The browser uses `/media/index.m3u8` when HLS is available. It can fall back to
`/media/TV_Commercials_1977.mp4` from `data/input/`. See
[Run and Verify](../README.md#run-and-verify) for the HLS packaging command.
Category matching is case-insensitive. The aliases map `camera` to
`cameras` and `foods` to `food`.

Window mode labels segments `analysis_window`; a fixed window is not a
verified commercial boundary and may contain multiple commercials. Per-shot
mode remains available for refinement. Runs store compatible checkpoints under
`output/runs/<cache-key>/`; `--resume` only reuses a matching input identity,
model, sampling, prompt, and schema configuration. Partial checkpoints are
never presented as completed final output.
