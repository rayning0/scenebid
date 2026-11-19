# SceneBid: AI Video Intelligence and Contextual Ad Decisioning

### by Raymond Gan

SceneBid is a local proof of concept that analyzes video and audio to find timestamped contextual ad opportunities. It uses a compilation of [1977 television commercials](https://archive.org/details/1977TVCommercials) as a sample video.

I combine real AI-generated video intelligence with fictional ad campaigns and simulated bids:

1. The [Python analysis worker](https://github.com/rayning0/scenebid/tree/main/analysis-worker) produces timestamped transcript and scene annotations.
2. The Go decisioning service generates simulated ad decisions and serves playback APIs. It picks eligible ads using the generated annotations and explains each decision.
3. The browser shows synchronized contextual information and overlay ads at the right video moments. It plays the video and shows contextual overlays, timestamped dialogue, scene summaries, and active ad info.

The Go decisioning service generates simulated ad decisions and serves
playback APIs. It picks eligible ads using the generated annotations and
explains each decision.

Relevant Go decisioning code:

- [`cmd/scenebid/main.go`](cmd/scenebid/main.go): implements the `decide`
  command and the HTTP `serve` mode, including the `/api/decision`,
  `/api/opportunities`, and `/api/context` playback endpoints.
- [`internal/auction/auction.go`](internal/auction/auction.go): evaluates
  bids and selects eligible winners or returns no-fill decisions.
- [`internal/model/model.go`](internal/model/model.go): defines bids and
  ad-decision data structures.
- [`internal/model/contract.go`](internal/model/contract.go): defines the
  generated analysis and ad-opportunity contract consumed by decisioning.

## Problem

Streaming video publishers must understand what's happening at a specific moment in a video, decide if an ad matches that moment, and choose among advertisers interested in that context.

SceneBid explores the relation between:

- Multimodal video and audio AI understanding.
- Timestamped scene-level metadata.
- Contextual ad targeting and brand separation.
- Ad eligibility and auction decisions.
- Video playback and contextual ad presentation.

## Demo

I finished the "P0: end-to-end" local demo for my sample video!

1. In Terminal, first run `go run ./cmd/scenebid serve`
2. Playing my `TV_Commercials_1977.mp4` video in http://localhost:8080/ shows this:

Start of video, showing Oscar Mayer bologna commercial. No overlay ad yet:
![Start of video. Oscar Mayer commercial.](https://github.com/rayning0/scenebid/blob/main/img/scenebid_demo_no_ad.png)

At 22.5 secs, see overlay ad #1 at bottom of video. It's for Oscar Mayer Bologna. Clicking "Learn more" link opens Oscar Mayer site:
![Oscar Mayer Bologna overlay ad](https://github.com/rayning0/scenebid/blob/main/img/scenebid_demo_ad1.png)

At 67.5 secs, see overlay ad #2, for Del Monte corn:
![Del Monte corn overlay ad](https://github.com/rayning0/scenebid/blob/main/img/scenebid_demo_ad2.png)

At 157.5 secs, see overlay ad #3, for "Hardy Boys and Nancy Drew Mysteries" TV show:
![Hardy Boys TV show overlay ad](https://github.com/rayning0/scenebid/blob/main/img/scenebid_demo_ad3.png)

At 187.5 secs, see overlay ad #4, for Triscuit wafers:
![Triscuit overlay ad](https://github.com/rayning0/scenebid/blob/main/img/scenebid_demo_ad4.png)

3. In 2 cases, we see overlay ads:
- If video naturally hits that ad time while playing.
- If we click orange dot placed at the ad time.

4. Right side shows **Dialogue**, which changes as video plays.
5. Right side shows **Scene Summary**, AI understanding of what's happening in each scene.
6. As each ad pops up, right side shows **Ad Playing**.

Mock OpenRTB exchange behavior remains exploratory; campaign demand and bids are still fictional.

## MVP Scope

### Real analysis

- Read the local `TV_Commercials_1977.mp4` file.
- Detect visual shot boundaries and extract timestamped frames.
- Transcribe speech with `faster-whisper`.
- Analyze frames and transcript excerpts with AI models.
- Produce timestamped scene annotations containing visual and audio
evidence, categories, and model metadata.
- Identify likely advertisers or products when supported by the available
evidence; retain unknown values when uncertain.
- Optional index embeddings for visual and transcript search.

### Simulated demand

- Load fictional campaigns and bids from local JSON fixtures.
- Evaluate campaign categories, bid floors, and configured separation rules.
- Return the winning eligible bid or a no-fill reason.
- Optionally exchange mock OpenRTB-style requests and responses between
simulated SSP and DSP components.

### Real playback and presentation

- Package the source MP4 into an HLS playlist and media segments.
- Play the video in a browser.
- Use playback time and generated annotations to request an ad decision.
- Display the selected fictional campaign as a bottom banner overlay.
- Show a campaign logo from each campaign's `logo_url` fixture field.
- Synchronize transcript dialogue and scene summaries in the live context panel.
- Mark ad opportunities on the playback timeline.

## Architecture

```mermaid
flowchart TD
    V["Local MP4"] --> A["Python analysis worker"]
    A --> S["Timestamped annotations"]
    V --> H["FFmpeg HLS packaging"]
    S --> G["Go decisioning API"]
    B["Fictional bids and campaigns"] --> G
    G --> D["Ad decision and explanation"]
    H --> P["Browser player"]
    D --> P
    P --> O["Contextual overlay"]
```

## Process Flow

1. Place the source MP4 under `data/input/`.
2. Analyze its audio and video to produce timestamped model-generated annotations.
3. Package the video into an HLS playlist and media segments.
4. Start the Go API and browser player.
5. During playback, look up the current video time in the annotations.
6. Evaluate fictional campaign bids against the current context and rules.
7. Display the winning overlay, campaign logo, and decision reason, or show a no-fill explanation.
8. Update the dialogue, scene summary, and active-ad panel as playback time advances.

Analysis happens before playback. Ad selection and overlay presentation happen during playback.

## Priorities

### P0: End-to-end demonstration

- Real speech transcription and frame analysis on a short sample.
- Timestamped annotations with evidence.
- HLS playback in a browser.
- Fictional campaign selection using real generated annotations.
- Visible overlay and decision explanation.

### P1: Better analysis and decisioning

- Process the full video.
- Improve shot grouping and brand identification.
- Add configurable brand and competitor separation.
- Add basic safety handling and clear unknown/no-fill behavior.
- Evaluate selected predictions against manually verified examples.

### P2: Ad-tech integration

- Simulate SSP/DSP communication with mock OpenRTB-style requests and
responses.
- Add request deadlines, no-bid behavior, and decision traces.
- Add simple playback and overlay event logging.

### P3: Search and future extensions

- Add CLIP/FAISS semantic search using ideas from In-Video Search.
- Explore linear video ads, VAST, and HLS-based SSAI separately.
- Explore live streaming analysis and low-latency updates.

## Repository Layout

- `cmd/scenebid/`: Go application entry point.
- `internal/`: Go analysis orchestration, decisioning, models, and storage.
- `analysis-worker/`: Python analysis worker for shots, transcription, and scene intelligence.
- `web/`: browser player, live context panel, timeline markers, and overlay UI.
- `data/input/`: local source video and creative assets.
- `data/fixtures/`: fictional campaigns and bids.
- `data/output/`: generated media, analysis, and decision traces.
- `docs/`: design notes.

## Run and Verify

The Go wrapper can run analysis, decision generation, and the local server:

```bash
go test ./...
go run ./cmd/scenebid analyze \
  -video data/input/TV_Commercials_1977.mp4 \
  -start 0
go run ./cmd/scenebid decide
```

The analysis worker defaults to local Ollama:

- `VISION_PROVIDER=ollama`
- `VISION_MODEL=qwen3-vl:8b`
- `VISION_ENDPOINT=http://localhost:11434/api/chat`
- `VISION_API_KEY` is optional for Ollama.

For an OpenAI-compatible vision service, set the provider, model, endpoint,
and API key explicitly. The worker also supports:

- `WHISPER_MODEL`, default `base`, for `faster-whisper` transcription.
- `VISION_MAX_TOKENS` is not an environment variable; use
`--vision-max-tokens` when invoking the worker.
- `VISION_ENDPOINT` defaults to the Ollama endpoint above and can point to
another OpenAI-compatible chat endpoint.

The Go `analyze` command invokes the worker with the selected video and
analysis range. Worker configuration is read from the environment or uses
the defaults above. For example:

```bash
VISION_PROVIDER=openai_compatible \
VISION_MODEL=gpt-4o-mini \
VISION_ENDPOINT=https://api.openai.com/v1/chat/completions \
VISION_API_KEY=... \
go run ./cmd/scenebid analyze \
  -video data/input/TV_Commercials_1977.mp4 \
  -start 0 \
  -end 360
```

### Analysis worker command and parameters

For the demo, to analyze the first 6 minutes of video, I used the worker directly:

```bash
VISION_PROVIDER=ollama \
VISION_MODEL=qwen2.5vl:3b \
WHISPER_MODEL=analysis-worker/models/faster-whisper-base \
analysis-worker/.venv/bin/python analysis-worker/main.py \
  data/input/TV_Commercials_1977.mp4 \
  data/output/TV_Commercials_1977 \
  --start 0 \
  --end 360 \
  --frames-per-shot 2 \
  --shot-threshold 27
```

The command-line parameters accepted by `analysis-worker/main.py` are:

- `video`: path to input MP4 video file.
- `output_dir`: path for `analysis.json`, `transcript.json`,
extracted frames, and checkpoint data.
- `--start`: starts analyzing video from this time (seconds). `0` starts at the
beginning.
- `--end`: analyzes video up to this time (seconds). `360` analyzes the first six
minutes. If omitted, analyzes the full video.
- `--shot-threshold`: scene-change sensitivity used by shot detection.
Default = `27`, which my demo used.
- `--frames-per-shot`: number of frames sampled from each detected shot.
Default = `2`, which my demo used.
- `--vision-max-tokens`: maximum tokens requested for each vision response.
Default = `512`.
- `--vision-mode`: vision grouping mode, either `window` or `shot`. Default = `window`, which my demo used.
- `--window-sec`: duration of each fixed analysis window when using window
mode. Default = `15.0` seconds.
- `--vision-timeout`: per-request vision client timeout (seconds). Default = `180`.
- `--resume`: resume a compatible checkpoint instead of starting the
checkpointed window pipeline from scratch.
- `--whisper-model`: `faster-whisper` model name or local model directory.
Default = `base`, but the demo used the downloaded local directory
`analysis-worker/models/faster-whisper-base` from Hugging Face.
- `--vision-provider`: vision backend. Default = `ollama`.
- `--vision-model`: vision model name. Default = `qwen3-vl:8b`. My demo
used `qwen2.5vl:3b`.
- `--vision-endpoint`: chat endpoint for selected vision provider. Ollama default = `http://localhost:11434/api/chat`.
- `--api-key`: optional vision API key, read by default from `VISION_API_KEY`.

The demo downloaded the `faster-whisper-base` model [from Hugging Face](https://huggingface.co/Systran/faster-whisper-base) and
passed its local directory through `WHISPER_MODEL`. The name `base` alone did not work with the installed Python transcription libraries, so using the downloaded local model directory made model resolution explicit and reproducible. Install Python dependencies from `analysis-worker/requirements.txt` inside `analysis-worker/.venv` before running the command.

To run the completed six-minute analysis in the browser without re-running AI analysis:

```bash
go test ./...
go run ./cmd/scenebid decide
go run ./cmd/scenebid serve
open http://localhost:8080
```

The demo serves the locally generated HLS playlist with .ts segments when
`data/output/TV_Commercials_1977/hls/index.m3u8` exists. Create it from the
local MP4 file when needed:

```bash
ffmpeg -i data/input/TV_Commercials_1977.mp4 \
  -c:v copy -c:a aac -f hls -hls_time 6 -hls_playlist_type vod \
  -hls_segment_filename data/output/TV_Commercials_1977/hls/segment_%05d.ts \
  data/output/TV_Commercials_1977/hls/index.m3u8
```

The overlay and live context panel are rendered client-side. Playback-time Go
APIs provide ad decisions and combined transcript/analysis context. Campaigns,
bids, logo URLs, and destination links are fictional; this is not SSAI,
OpenRTB, or a production auction.

Campaign fixtures support these key fields:

- `target_categories`: categories eligible for contextual matching.
- `bid_cpm_usd`: simulated CPM bid.
- `destination_url`: fictional click-through destination.
- `logo_url`: image displayed to the left of the active overlay ad.

The server also exposes `/api/opportunities`, `/api/decision?time=...`, and
`/api/context` for the browser demo.

`analyze` runs `analysis-worker/main.py`, which detects shots and extracts
frames from the actual MP4, transcribes with `faster-whisper`, and sends each
shot's frames and transcript excerpt to the configured vision-language
provider. Use `-end -1` to analyze the full video, or invoke the worker directly for
all options. A provider/model failure exits nonzero; no fixture annotations are
substituted.

Install Python dependencies from `analysis-worker/requirements.txt` and ensure
`ffmpeg` is on PATH. The OpenAI-compatible provider accepts `VISION_ENDPOINT`
and `VISION_API_KEY`; Ollama uses `VISION_PROVIDER=ollama`,
`VISION_ENDPOINT=http://localhost:11434/api/chat`, and a vision model.

## MVP Limitations

- Model outputs can be inaccurate; detected objects, brands, and safety
assessments require validation.
- The input is a compilation of commercials, not a normal TV episode.
- Campaigns, bids, and demand-side participants are fictional.
- An overlay is rendered by the browser; this does not itself demonstrate
server-side ad insertion.
- The project is not a production ad server or a claim of OpenRTB
compliance.
- Source video and generated media should stay out of the repository.
- Verify usage and redistribution rights for video and creative assets.

## Ad Tech Terms

- **Publisher / supply:** The party providing an advertising opportunity.
- **Advertiser / demand:** The buyer seeking to show an advertisement.
- **SSP:** A platform representing or enabling publisher-side supply.
- **DSP:** A platform that evaluates opportunities for advertisers.
- **CPM:** The price per 1,000 impressions.
- **Bid floor:** The minimum eligible bid for an opportunity.
- **OpenRTB:** A protocol used to exchange programmatic bid requests and
responses.
- **VAST:** A standard for describing video ad creatives and tracking.
- **SSAI:** Server-side ad insertion.
- **Impression:** A measured ad-display event, distinct from selecting an ad.
