const video=document.querySelector("#player"), overlay=document.querySelector("#overlay"), status=document.querySelector("#status");
const src="/media/index.m3u8"; let shown=new Set(), active=null, filledDecisions=[], opportunities=[], requested=new Set(), decisionsLoaded=false, resumeAfterLoad=false;
const markers=document.querySelector("#markers");
fetch("/api/opportunities").then(r=>r.json()).then(items=>{opportunities=items;return Promise.all(items.map(async item=>{try{return [item,await fetch(`/api/decision?time=${item.start_sec}`).then(r=>r.json())]}catch{return [item,null]}}))}).then(items=>items.filter(([,decision])=>decision&&decision.status==="filled").map(([item,decision])=>{filledDecisions.push({...decision,trigger_sec:item.start_sec,opportunity_end_sec:item.end_sec});return item}).forEach(item=>{
 const dot=document.createElement("button"); dot.className="marker"; dot.title=`Ad opportunity at ${item.start_sec.toFixed(1)}s`;
 dot.dataset.time=item.start_sec; dot.addEventListener("click",()=>{video.currentTime=item.start_sec;video.play()});
 markers.appendChild(dot);
 const place=()=>{if(video.duration)dot.style.left=`${100*item.start_sec/video.duration}%`};
 video.addEventListener("loadedmetadata",place); place();
})).catch(()=>{}).finally(()=>{decisionsLoaded=true;if(resumeAfterLoad)video.play()});
if(video.canPlayType("application/vnd.apple.mpegurl")) video.src=src;
else if(window.Hls&&Hls.isSupported()){const h=new Hls();h.loadSource(src);h.attachMedia(video);}
else {video.src="/media/TV_Commercials_1977.mp4";status.textContent="HLS unavailable; using local MP4 fallback.";}
function showDecision(d){const t=video.currentTime;const cpm=Number(d.winner&&d.winner.cpm),contentTime=Number(d.content_time_sec);if(d.status!=="filled"||!d.winner||!Number.isFinite(cpm)||!Number.isFinite(contentTime)||shown.has(d.opportunity_id)||t<d.trigger_sec||t>=d.opportunity_end_sec)return;
 shown.add(d.opportunity_id);active={end_sec:d.opportunity_end_sec||d.content_time_sec+5};
 overlay.innerHTML=`<strong>${d.winner.headline||"Contextual message"}</strong><br><small>${d.winner.advertiser} · $${cpm.toFixed(2)} CPM<br>${d.reason}<br>Model safety: ${d.model_safety} · DEMO MODE (safety ignored)</small><br><a href="${d.winner.destination_url}" target="_blank" rel="noreferrer">Learn more</a>`;overlay.hidden=false;status.textContent=`Window ${contentTime.toFixed(2)}s · fictional decision; display event logged`;console.info("display_event",{opportunity_id:d.opportunity_id});}
video.addEventListener("timeupdate",async()=>{const t=video.currentTime;if(active&&t>=active.end_sec){overlay.hidden=true;active=null}filledDecisions.forEach(showDecision);const item=opportunities.find(x=>t>=x.start_sec&&t<x.end_sec);if(item&&!requested.has(item.id)){requested.add(item.id);try{const d=await fetch(`/api/decision?time=${item.start_sec}`).then(r=>r.json());if(d.status==="filled"){d.trigger_sec=item.start_sec;d.opportunity_end_sec=item.end_sec;filledDecisions.push(d);showDecision(d)}}catch{requested.delete(item.id)}}});
setInterval(()=>{if(video.paused)return;const t=video.currentTime;if(active&&t>=active.end_sec){overlay.hidden=true;active=null}filledDecisions.forEach(showDecision)},100);
video.addEventListener("play",()=>{if(!decisionsLoaded){resumeAfterLoad=true;video.pause();status.textContent="Loading ad decision timeline…"}});
video.addEventListener("seeking",()=>{active=null;overlay.hidden=true;shown.clear();});

