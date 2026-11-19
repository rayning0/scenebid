# SceneBid: AI Video Intelligence and Contextual Ad Decisioning
### by Raymond Gan

SceneBid is a local proof of concept that analyzes video and audio to find
timestamped contextual advertising opportunities. It uses a compilation of
1977 television commercials as a sample video.

The project combines real AI-generated video intelligence with fictional
advertiser campaigns and simulated bids. A Go decisioning service selects
eligible ads using the generated annotations and explains each decision.
The browser demo plays the video and displays contextual overlays,
timestamped dialogue, scene summaries, and active ad information.

## Problem

Streaming publishers need to understand what is happening at a particular
moment in a video, determine whether an ad is suitable, and choose among
advertisers interested in that context.

SceneBid explores the connection between:

- Multimodal video and audio understanding.
- Timestamped scene-level metadata.
- Contextual targeting and brand separation.
- Ad eligibility and auction decisions.
- Video playback and contextual ad presentation.

## Project Status

The end-to-end local demo is implemented for the sample video. The analysis
worker produces timestamped transcript and scene annotations, the Go service
generates simulated decisions and serves playback APIs, and the browser
renders synchronized contextual information and overlay ads.

Mock OpenRTB exchange behavior remains exploratory; campaign demand and bids
are still fictional.

## MVP Scope

### Real analysis

- Read the local `TV_Commercials_1977.mp4` file.
- Detect visual shot boundaries and extract timestamped frames.
- Transcribe speech with faster-whisper.
- Analyze frames and transcript excerpts with AI models.
- Produce timestamped scene annotations containing visual and audio
  evidence, categories, and model metadata.
- Identify likely advertisers or products when supported by the available
  evidence; retain unknown values when uncertain.
- Optionally index embeddings for visual and transcript search.

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
2. Analyze its audio and video to produce timestamped model-generated
   annotations.
3. Package the video into an HLS playlist and media segments.
4. Start the Go API and browser player.
5. During playback, look up the current video time in the annotations.
6. Evaluate fictional campaign bids against the current context and rules.
7. Display the winning overlay, campaign logo, and decision reason, or show a
   no-fill explanation.
8. Update the dialogue, scene summary, and active-ad panel as playback time
   advances.

Analysis happens before playback. Ad selection and overlay presentation
happen during playback.

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

The first end-to-end worker can be run with (the default is a 30-second
development range):

```bash
go test ./...
go run ./cmd/scenebid analyze \
  -video data/input/TV_Commercials_1977.mp4 \
  -at 5
go run ./cmd/scenebid decide
```

The analysis worker defaults to local Ollama:

- `VISION_PROVIDER=ollama`
- `VISION_MODEL=qwen3-vl:8b`
- `VISION_ENDPOINT=http://localhost:11434/api/chat`
- `VISION_API_KEY` is optional for Ollama.

For an OpenAI-compatible vision service, set the provider, model, endpoint,
and API key explicitly. The worker also supports:

- `WHISPER_MODEL`, default `base`, for faster-whisper transcription.
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
  -at 5
```

To run the completed six-minute analysis in the browser without re-running
AI analysis:

```bash
go test ./...
go run ./cmd/scenebid decide
go run ./cmd/scenebid serve
open http://localhost:8080
```

The demo serves the locally generated HLS playlist when
`data/output/TV_Commercials_1977/hls/index.m3u8` exists. Generate it from the
local MP4 when needed:

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
frames from the actual MP4, transcribes with faster-whisper, and sends each
shot's frames and transcript excerpt to the configured vision-language
provider. Use `-end -1` for the full video, or invoke the worker directly for
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
