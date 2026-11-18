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
The Go service reads this contract and independently reads fictional campaigns.
