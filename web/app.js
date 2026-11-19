const video=document.querySelector("#player"), overlay=document.querySelector("#overlay"), status=document.querySelector("#status");
const src="/media/TV_Commercials_1977.m3u8"; let shown=new Set(), active=null;
if(video.canPlayType("application/vnd.apple.mpegurl")) video.src=src;
else if(window.Hls&&Hls.isSupported()){const h=new Hls();h.loadSource(src);h.attachMedia(video);}
else {video.src="/media/TV_Commercials_1977.mp4";status.textContent="HLS unavailable; using local MP4 fallback.";}
video.addEventListener("timeupdate",async()=>{const t=video.currentTime; if(active&&t>=active.end_sec){overlay.hidden=true;active=null}
 const r=await fetch(`/api/decision?time=${t}`);if(!r.ok)return;const d=await r.json();
 if(d.status==="filled"&&!shown.has(d.opportunity_id)){shown.add(d.opportunity_id);active={end_sec:d.opportunity_end_sec||d.content_time_sec+5};overlay.innerHTML=`<strong>${d.winner.headline||"Contextual message"}</strong><br><small>${d.winner.advertiser} · $${d.winner.cpm.toFixed(2)} CPM<br>${d.reason}<br>Model safety: ${d.model_safety} · DEMO MODE (safety ignored)</small><br><a href="${d.winner.destination_url}" target="_blank" rel="noreferrer">Learn more</a>`;overlay.hidden=false;status.textContent=`Window ${d.content_time_sec.toFixed(2)}s · fictional decision; display event logged`;console.info("display_event",{opportunity_id:d.opportunity_id});}});
video.addEventListener("seeking",()=>{active=null;overlay.hidden=true;shown.clear();});

