"""Assembles the final V3 demo page: recorded video + 9 synced narration
tracks + toggleable WebVTT captions, mirroring video/demo_page.html's
established audio-sync pattern (BOUNDS array + syncToTime() on the video's
play/pause/seeking/timeupdate events) but for 9 beats instead of 6.
"""
import base64
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VIDEO_DIR = REPO / "video"
AUDIO_DIR = VIDEO_DIR / "audio"
REC_DIR = VIDEO_DIR / "recording"

VIDEO_FILE = REC_DIR / "v3_compressed.webm"

BEATS = [
    {"id": "beat0_hook", "start": 0.0, "end": 11.154,
     "cues": ["Your company changed the price to two hundred fifty dollars.",
              "Yesterday.",
              "Your AI still confidently tells every employee... two hundred."]},
    {"id": "beat1_evidence", "start": 11.154, "end": 27.350,
     "cues": ["Here's the evidence.",
              "On the left, the handbook — still says two hundred.",
              "On the right, the finance ticket that actually approved the raise — two hundred fifty.",
              "Nobody updated the handbook."]},
    {"id": "beat2_baselines", "start": 27.350, "end": 59.637,
     "cues": ["Two strong baselines.",
              "Same wrong answer.",
              "Full context — every document, one call — still two hundred.",
              "An agent free to search and read across those same documents, however it likes — also two hundred.",
              "More reading doesn't fix this, because the right answer simply isn't written down anywhere in the documents."]},
    {"id": "beat3_selfheal", "start": 59.637, "end": 99.683,
     "cues": ["Now watch what happens differently.",
              "The entity isn't in memory yet — so instead of guessing, SelfHeal checks a signal feed no baseline ever gets:",
              "a stand-in for the ticket system this bot was never connected to.",
              "Found it. Ticket 4521.",
              "Writing it to memory, right now, live.",
              "Final answer: two hundred fifty, cited as memory.",
              "This check runs on each query — not just once, during tuning."]},
    {"id": "beat4_verifier", "start": 99.683, "end": 131.004,
     "cues": ["I also built a deterministic verifier for stale citations.",
              "No model call, no guessing.",
              "On this targeted revision case, it correctly replaces the stale citation with the current one.",
              "But here's the important part: on the frozen sixteen-case evaluation, it changed exactly zero outputs.",
              "So it's disabled in the shipped accuracy configuration.",
              "Not every component earns its place."]},
    {"id": "beat5_frozentest", "start": 131.004, "end": 165.695,
     "cues": ["Here's the proof, on sixteen test cases the system never saw during development.",
              "Every baseline: zero out of three, on the memory-correction category this was built for.",
              "SelfHeal: three for three.",
              "Flip memory off, change nothing else — back to zero, on those same three cases.",
              "One capability.",
              "For this category, that's the entire difference."]},
    {"id": "beat6_scale", "start": 165.695, "end": 185.026,
     "cues": ["Think about the scale for a second.",
              "One employee getting the wrong number is an annoyance.",
              "Ten thousand employees getting it — that's not a bug anymore.",
              "That's an operating-system problem for your company's own knowledge."]},
    {"id": "beat7_lesson", "start": 185.026, "end": 221.702,
     "cues": ["The first time I ran this frozen test, SelfHeal tied the baseline.",
              "Zero out of three, on the exact case it was built for.",
              "Not a crash — just a quiet, forgettable number, the kind you could rationalize away under deadline pressure.",
              "The bug: memory only ever learned from training-time data, never from what it was actually being asked, live.",
              "A good held-out test doesn't just measure whether you generalize —",
              "it catches you lying to yourself about scope.",
              "Silently."]},
    {"id": "beat8_closing", "start": 221.702, "end": 251.168,
     "cues": ["A RAG system that retrieves information is useful.",
              "A system that can recover when what it retrieves is contradicted by a newer signal —",
              "that's something I'd actually trust inside a company.",
              "The production vision is broader: organizational memory that can reason about versions, permissions, and conflicting knowledge.",
              "That part isn't built yet.",
              "This is the prototype that demonstrates the mechanism on the frozen evaluation."]},
]


def fmt_ts(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def build_vtt():
    lines = ["WEBVTT", ""]
    idx = 1
    for beat in BEATS:
        dur = beat["end"] - beat["start"]
        cues = beat["cues"]
        total_chars = sum(len(c) for c in cues)
        t = beat["start"]
        for cue in cues:
            share = len(cue) / total_chars
            cue_dur = max(0.9, dur * share)
            cue_end = min(beat["end"], t + cue_dur)
            lines.append(str(idx))
            lines.append(f"{fmt_ts(t)} --> {fmt_ts(cue_end)}")
            lines.append(cue)
            lines.append("")
            idx += 1
            t = cue_end
    return "\n".join(lines)


def b64_file(path, mime):
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def main():
    vtt_text = build_vtt()
    vtt_data_uri = "data:text/vtt;base64," + base64.b64encode(vtt_text.encode("utf-8")).decode("ascii")

    video_uri = b64_file(VIDEO_FILE, "video/webm")
    audio_uris = [b64_file(AUDIO_DIR / f"{b['id']}.mp3", "audio/mpeg") for b in BEATS]

    bounds = [b["start"] for b in BEATS] + [BEATS[-1]["end"]]
    bounds_js = "[" + ", ".join(f"{x:.3f}" for x in bounds) + "]"
    narrs_js = "[" + ", ".join(f'"{b["id"]}"' for b in BEATS) + "]"
    n_beats = len(BEATS)

    beatlist_html = "\n".join(
        f'      <div class="beat"><div class="t">{fmt_ts(b["start"])[3:8]}</div><div class="d"><strong>{title}</strong> — {desc}</div></div>'
        for b, title, desc in zip(BEATS, [
            "The problem, in one number",
            "The evidence",
            "Two strong baselines fail",
            "SelfHeal fires, live",
            "A second, tested-but-unexercised layer",
            "Frozen 16-case proof",
            "Why this matters at scale",
            "The lesson",
            "The vision",
        ], [
            "the handbook says $200, a ticket says $250. Nobody updated the handbook.",
            "the handbook vs. the finance ticket, side by side.",
            "full-context (A0) and a search-capable agent (B) both still answer $200.",
            "an unseen entity gets checked against a signal feed no baseline gets, corrected on the spot.",
            "a deterministic stale-citation verifier — real and tested, but disabled in the shipped config since it changed zero outputs on the frozen test.",
            "every baseline scores 0/3 on memory_correction, SelfHeal scores 3/3 — reproduced by a one-flag ablation.",
            "one wrong number is an annoyance; ten thousand is an operating-system problem.",
            "the first frozen run tied the baseline, and why that's the real finding.",
            "what a production version of this would need to add.",
        ])
    )

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>SelfHeal RAG V3</title>
<style>
  :root {{
    --bg: #0b0e14; --surface: #10141d; --surface-2: #161c29; --border: #232c3d;
    --text: #e8ecf1; --text-dim: #8b96a8; --text-faint: #5b6577;
    --accent: #4fd1c5; --accent-dim: #2f7a72; --good: #6ee7b7; --bad: #f28b82; --warn: #f6ad55;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; }}
  body {{ padding: 56px 24px 80px; }}
  .wrap {{ max-width: 860px; margin: 0 auto; }}
  .eyebrow {{
    font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 12.5px; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--accent); margin: 0 0 14px; display: flex; align-items: center; gap: 10px;
  }}
  .eyebrow::before {{ content: ""; display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 3px rgba(79,209,197,0.18); }}
  h1 {{ margin: 0 0 12px; font-size: 34px; }}
  .lede {{ font-size: 16px; line-height: 1.6; color: var(--text-dim); max-width: 720px; }}
  .lede strong {{ color: var(--text); }}
  .player {{ margin-top: 28px; border-radius: 14px; overflow: hidden; border: 1px solid var(--border); }}
  video {{ display: block; width: 100%; height: auto; background: #000; }}
  video::cue {{ background: rgba(10,13,20,0.82) !important; color: #f2f2f2 !important; font-size: 17px !important; line-height: 1.3 !important; font-family: 'IBM Plex Sans', -apple-system, sans-serif !important; }}
  .meta-row {{ display: flex; justify-content: space-between; align-items: baseline; gap: 16px; margin-top: 14px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 12.5px; color: var(--text-faint); flex-wrap: wrap; }}
  .meta-row a {{ color: var(--text-faint); }}
  .beats {{ margin-top: 52px; padding-top: 40px; border-top: 1px solid var(--border); }}
  .section-label {{ font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-faint); margin: 0 0 20px; }}
  .beatlist {{ display: grid; gap: 10px; }}
  .beat {{ display: grid; grid-template-columns: 64px 1fr; gap: 18px; padding: 14px 16px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }}
  .beat .t {{ font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 13px; color: var(--accent); font-variant-numeric: tabular-nums; padding-top: 1px; }}
  .beat .d {{ font-size: 14.5px; line-height: 1.5; color: var(--text-dim); }}
  .beat .d strong {{ color: var(--text); font-weight: 600; }}
  .result {{ margin-top: 44px; padding: 22px 24px; border-radius: 12px; background: var(--surface-2); border: 1px solid var(--border); display: flex; align-items: center; gap: 22px; flex-wrap: wrap; }}
  .result .num {{ font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 30px; font-weight: 700; white-space: nowrap; }}
  .result .num .bad {{ color: var(--bad); }}
  .result .num .arrow {{ color: var(--text-faint); margin: 0 8px; font-weight: 400; }}
  .result .num .good {{ color: var(--good); }}
  .result .cap {{ font-size: 14px; color: var(--text-dim); line-height: 1.55; flex: 1; min-width: 220px; }}
  footer {{ margin-top: 52px; padding-top: 28px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 13px; }}
  footer a {{ color: var(--accent); text-decoration: none; border-bottom: 1px solid var(--accent-dim); }}
  footer a:hover {{ border-bottom-color: var(--accent); }}
  footer .cmd {{ color: var(--text-faint); }}
  @media (max-width: 560px) {{ .beat {{ grid-template-columns: 1fr; gap: 4px; }} }}
</style>
</head>
<body>
<div class="wrap">

  <p class="eyebrow">micro1 Agentic Workflows Hackathon &middot; Solution demo (V3)</p>
  <h1>SelfHeal RAG</h1>
  <p class="lede">
    A company-policy RAG pipeline that <strong>catches its own stale answers and
    fixes them live</strong> — nine beats, real unedited command output, one
    frozen 16-case test, and an honest look at what didn't move the needle.
  </p>

  <div class="player">
    <video id="v3video" controls preload="metadata" playsinline crossorigin="anonymous"
      poster="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1280' height='720'%3E%3Crect width='1280' height='720' fill='%230b0e14'/%3E%3C/svg%3E">
      <source src="{video_uri}" type="video/webm">
      <track id="captions" kind="subtitles" srclang="en" label="English" src="{vtt_data_uri}" default>
    </video>
{"".join(f'''    <audio id="{b["id"]}" preload="auto" src="{uri}"></audio>
''' for b, uri in zip(BEATS, audio_uris))}  </div>
  <div class="meta-row">
    <span>4:11 &middot; toggleable captions &middot; no background music</span>
    <a href="https://github.com/yonilev2003/hackathonaug28.08.26">github.com/yonilev2003/hackathonaug28.08.26</a>
  </div>

  <div class="beats">
    <p class="section-label">What's in the four minutes</p>
    <div class="beatlist">
{beatlist_html}
    </div>
  </div>

  <div class="result">
    <div class="num"><span class="bad">0/3</span><span class="arrow">&rarr;</span><span class="good">3/3</span></div>
    <div class="cap">memory_correction accuracy on the frozen 16-case test — every baseline (full-context, static RAG, self-correcting RAG, search-capable agent) scores zero; SelfHeal RAG scores 3/3, reproduced by a one-flag memory on/off ablation. On raw aggregate SelfHeal does <strong>not</strong> beat every baseline — see README.md Section 5 for the full, honest numbers.</div>
  </div>

  <footer>
    <span class="cmd">make setup &amp;&amp; make baseline &amp;&amp; make advanced &amp;&amp; make eval</span>
    <a href="https://github.com/yonilev2003/hackathonaug28.08.26">github.com/yonilev2003/hackathonaug28.08.26</a>
  </footer>

</div>
<script>
  var video = document.getElementById('v3video');
  var narrs = {narrs_js};
  narrs = narrs.map(function (id) {{ return document.getElementById(id); }});

  var BOUNDS = {bounds_js};
  var N = {n_beats};
  var lastBeat = -1;

  function beatIndexFor(t) {{
    for (var i = 0; i < N; i++) {{
      if (t >= BOUNDS[i] && t < BOUNDS[i + 1]) return i;
    }}
    return t >= BOUNDS[N] ? N - 1 : 0;
  }}
  function stopAllNarration() {{
    narrs.forEach(function (a) {{ a.pause(); }});
  }}
  function syncToTime(t) {{
    var idx = beatIndexFor(t);
    if (idx !== lastBeat) {{
      stopAllNarration();
      lastBeat = idx;
      var offset = Math.max(0, t - BOUNDS[idx]);
      var a = narrs[idx];
      try {{ if (isFinite(offset)) a.currentTime = offset; }} catch (e) {{}}
      if (!video.paused) a.play().catch(function () {{}});
    }}
  }}
  video.addEventListener('play', function () {{ syncToTime(video.currentTime); }});
  video.addEventListener('pause', function () {{ stopAllNarration(); }});
  video.addEventListener('ended', function () {{ stopAllNarration(); }});
  video.addEventListener('seeking', function () {{ stopAllNarration(); lastBeat = -1; }});
  video.addEventListener('timeupdate', function () {{ if (!video.paused) syncToTime(video.currentTime); }});
</script>
</body>
</html>
"""

    out_path = VIDEO_DIR / "demo_page_v3.html"
    out_path.write_text(html)
    print(f"Wrote {out_path} ({out_path.stat().st_size / 1e6:.2f} MB)")
    print(f"VTT cues: {vtt_text.count(chr(10) + chr(10))}")


if __name__ == "__main__":
    main()
