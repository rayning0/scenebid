## Before you record

- Start the app and open `http://localhost:8080/`.
- If you want viewers to hear the commercial, enable **tab or system-audio sharing** in your recording tool and make a short test recording. If the platform doesn’t capture audio, narrate what the dialogue panel shows.
- Open `campaigns.json`, `analysis.json`, `opportunities.json`, and `decisions.json` in Cursor tabs, ideally positioned on short examples.
- Have your README’s scaling diagrams open in another tab.
- Rehearse clicking the **Del Monte** and **Kodak or another working opportunity** markers. Check the exact markers and playback behavior before recording.

---

## SceneBid YouTube demo script

**Target length:** About 6 minutes. The timestamps are guides; pause briefly to let each overlay appear.

### 0:00–0:30 — Introduction

**On screen:** SceneBid player at `localhost:8080`, paused at the beginning.

> Hi, I’m Raymond Gan. This is **SceneBid**, a prototype I built to explore how AI video understanding can drive contextual ad decisions.
>
> SceneBid analyzes video frames and spoken dialogue, generates timestamped context, and uses that context to match advertising campaigns. During playback, it displays the selected campaign as an overlay.
>
> For this demo, I’m using a compilation of 1977 television commercials. The video analysis is real; the campaign bids and auction decisions are simulated.

### 0:30–1:40 — Playback and dynamic context

**On screen:** Press play. Point to the right-hand panel as it updates.

> It's the classic Oscar Mayer bologna commercial! Such a cute kid! As the video plays, the panel on the right updates with the current **dialogue** and **scene summary**.
>
> The dialogue comes from AI speech transcription. The scene summary comes from analyzing sampled video frames together with transcript context. I created these AI observations before playback and synchronized them with the video timeline.

**On screen:** Let the video reach the first ad opportunity near 22.5 seconds. Point to the overlay and the **Ad Playing** section.

> Now the video naturally hits its first ad opportunity. SceneBid has matched the detected context with an Oscar Mayer bologna campaign, and the ad overlay shows at the bottom of the video.
>
> The **Ad Playing** section on the right updates at the same time. The overlay shows the campaign, its simulated CPM, and a “Learn more” link, which goes to the Oscar Mayer website.

**On screen:** Point to the orange dots beneath the video.

> The orange dots mark ad opportunities. I can let the video play to an opportunity, as we just saw, or I can click a dot to jump directly to one.

### 1:40–2:25 — Jump to another ad opportunity

**On screen:** Click the Del Monte marker near 67.5 seconds. Let the context panel and overlay update.

> Now I’m jumping to the Del Monte corn ad opportunity. The dialogue and scene summary change to reflect this part of the video, the **Ad Playing** section updates, and the matching corn overlay appears.
>
> The connection is the timestamp: the player reaches an opportunity, SceneBid looks up the corresponding video context, and the Go decisioning service evaluates the simulated campaigns.

**On screen:** Click the Triscuit marker near 187.5 seconds, or another opportunity you’ve verified works.

> Here’s an ad for Triscuit wafers.
>
> The analysis worker wasn’t given the commercial chapter list as an answer key. It inferred context from the video and audio. The results aren’t perfect, so I can compare them with the known commercial list afterward.

### 2:25–3:30 — How the AI analysis works

**On screen:** Show README architecture diagram. Open `analysis.json` and `transcript.json`. Point to the timestamps, scene summary, categories, and detected products.

> A quick architecture tour: The Python analysis worker reads the local MP4 video, creates timestamped annotations, and writes the scene intelligence. FFmpeg packages the video for browser playback. When the browser reaches an opportunity, it asks the Go decisioning API for an ad. The Go API combines the context with fictional campaign data, returns the decision, and the browser displays the overlay ad.
>
> My Python worker detects visual shot changes, extracts representative frames, and uses **faster-whisper** to transcribe the audio into `transcript.json`. Then I divide the video into 15-second windows and send sampled frames plus transcript excerpts to **Qwen 2.5 VL** through Ollama.

> The AI model writes scene descriptions, categories, products, and possible advertisers into `analysis.json`. These windows aren't always exact commercial boundaries, and AI can misspell or misidentify products and brands, so the results still need review.

**On screen:** Optionally show the checkpoint directory or point to the README’s "--resume" description.

> My AI analysis failed partway through this video. Checkpointing let me keep the completed work and resume from the failed window with `--resume`, instead of starting over.

### 3:30–4:20 — Opportunities and simulated decisions

**On screen:** Open `campaigns.json`, `opportunities.json`, then `decisions.json`.

> Next, I run the Go `decide` command. It reads the AI analysis and candidate opportunities, then loads `campaigns.json`. That file is my fictional demand: advertisers, simulated bids, target categories, headlines, product images, and links. The Go decisioning code compares those campaigns with the detected context and picks the highest eligible simulated bid.
>
> `opportunities.json` is a compact index of where ads may appear, including timestamps and context. `decisions.json` records the simulated outcome: the candidate bids, the selected campaign or no-fill result, and the reason.
>
> In short, `analysis.json` describes the content, `opportunities.json` indexes where ads may appear, `campaigns.json` defines the fictional demand, and `decisions.json` records which campaign was selected and why.

**On screen:** Return to the browser player.

> During playback, the browser requests context and an ad decision using the title and content timestamp. The Go service returns the simulated decision, and the browser displays it as a ad overlay at the right time.
>
> This is **demo mode**: the bids are simulated, and it ignores the model’s safety value, so I can demo these overlay ads. A production system would apply publisher and advertiser suitability rules, plus pacing and frequency caps. This prototype does not yet implement a real OpenRTB exchange or server-side ad insertion.

### 5:00–6:00 — Scaling to VOD and live FAST channels

**On screen:** Show the VOD scaling diagram, then the live linear diagram.

> To scale VOD, I’d analyze each title ahead of playback with queued CPU and GPU workers, then store and reuse its scene intelligence across viewers. In AWS terms, we could us S3 for video and artifacts, SQS and Step Functions for durable workflow, and AWS Batch for GPU jobs. The Go decisioning service could scale independently, so viewer requests wouldn’t wait for AI inference.
>
> For FAST channels, I’d pre-analyze known assets and map their timelines to the live channel. For live or unmatched content, I’d analyze the feed continuously and publish context before the viewer reaches the opportunity. Shared scene context can serve many viewers, while the final campaign decision can vary by session.
>
> My local prototype took roughly 25 seconds of vision inference per 15-second window. That isn’t a production benchmark, but it shows why throughput and latency matter for a continuous channel.
>
> Thanks for watching.
