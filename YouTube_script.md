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

> A quick architecture tour: The Python analysis worker reads the local MP4 video, creates timestamped annotations, and writes AI scene intelligence. FFmpeg packages the video for browser playback. When the browser reaches an opportunity, it asks the Go decisioning API for an ad. The API combines the context with fictional campaign data, returns the ad decision, and the browser displays the overlay ad.
>
> The AI worker finds shot changes, transcribes the audio with **faster-whisper** to `transcript.json`, and sends 15-second windows of sampled frames plus transcript excerpts to **Qwen 2.5 VL** (a vision-language model)[show Hugging Face page] through Ollama.

> It writes scene descriptions, products, and possible advertisers into `analysis.json`.

**On screen:** Point to README’s "--resume" description, then `checkpoint.json` file.

> When AI analysis failed partly through the video, the checkpoint let me retry the failed window and continue without starting over. I used the `--resume` parameter. `checkpoint.json` stores the AI result as it moves through the video.

### 3:30–4:20 — Opportunities and simulated decisions

**On screen:** Open `campaigns.json`, `opportunities.json`, then `decisions.json`.

> Next, Go’s `decide` command compares the AI context with fictional advertisers and bids in `campaigns.json`, then picks the highest CPM eligible campaign.
>
> The Go `decide` command creates `opportunities.json`, which indexes where ads may appear, and `decisions.json`, which says which campaign won, or why there was no ad fill.
>
> So `analysis.json` describes the video content, `campaigns.json` defines the fictional demand, `opportunities.json` indexes where ads may appear, and `decisions.json` records which ad campaign got picked and why.

**On screen:** Return to the browser player.

> During playback, the browser requests context and an ad decision using the title and content timestamp. The Go service returns the simulated decision, and the browser displays it as a ad overlay at the right time.
>
> In **demo mode**, these bids are simulated, and it ignores the model’s safety value, so I can demo these ads. A production system would apply publisher and advertiser suitability rules, plus pacing and frequency caps. My prototype doesn't implement a real OpenRTB exchange or server-side ad insertion.

### 5:00–6:00 — Scaling to VOD and live FAST channels

**On screen:** Show the VOD scaling diagram, then the live linear diagram.

> First, see the VOD diagram’s 2 separate paths. The AI analysis path starts with the video in S3, moves through EventBridge and SQS into Step Functions, and then runs CPU and GPU jobs. The results go through validation into PostgreSQL and Redis, where the Go decisioning service can reuse the scene context for many viewers.
>
> The second VOD path is delivery: the source video goes to MediaConvert for HLS packaging, which creates the `.ts` segments. CloudFront then delivers those segments to the player. Analysis happens ahead of playback, while HLS packaging and delivery serve the finished video.
>
> Compare that with the live linear TV diagram. The delivery path starts with the live TV channel feed, goes through MediaLive and MediaPackage to create HLS, then reaches viewers through CloudFront.
>
> The AI analysis path samples that HLS feed, sends output to Kafka and Flink, and keeps the current context in Redis. The Go service uses that context when the player requests an ad decision.
>
> For FAST channels, I’d pre-analyze known assets and map their timelines to the live channel. For truly live/unmatched content, I’d analyze continuously and publish context before the viewer reaches the opportunity. Shared scene context serves many viewers, while the final campaign decision can vary by session.
>
> Thanks for watching.
