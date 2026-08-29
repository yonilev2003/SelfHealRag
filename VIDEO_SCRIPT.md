# Video script (4:11) — SelfHeal RAG, V3

Real numbers, real commands. Every beat below runs against files already
committed in this repo — nothing here is staged or simulated, except beat 5
(the verifier), which is explicitly labeled on screen as a targeted
demonstration, not a frozen-test evaluation event (see that beat's notes).

## Beat 1 — Cold open (0:00–0:11)

Screen: `$250` vs the AI's stale `$200` answer, no context yet — the hook.

**VO:** "Your company changed the price to two hundred fifty dollars.
Yesterday. Your AI still confidently tells every employee... two hundred."

## Beat 2 — Evidence (0:11–0:27)

Screen: side-by-side of `data/corpus/eng_oncall_stipend_usd.md` (states
"$200") and `data/correction_signals.json`'s `TICKET-4521` entry ("approved
raising... from $200 to $250... handbook not yet updated").

**VO:** "Here's the evidence. On the left, the handbook — still says two
hundred. On the right, the finance ticket that actually approved the raise
— two hundred fifty. Nobody updated the handbook."

## Beat 3 — Baselines fail on camera (0:27–0:60)

Real output, `run_A0.py` (full 81-chunk corpus) and `run_B.py` (generalist
agent, `Read`/`Grep`/`Glob` only, sandboxed to a copy of `data/corpus/`,
capped at 25 turns / 8 minutes per `baseline/run_B_generalist.py`) both
answer `{'value': '200'}`.

**VO:** "Two strong baselines. Same wrong answer. Full context — every
document, one call — still two hundred. An agent free to search and read
across those same documents, however it likes — also two hundred. More
reading doesn't fix this, because the right answer simply isn't written
down anywhere in the documents."

## Beat 4 — SelfHeal fires, live (0:60–1:40)

```bash
python3 -c "
import asyncio,sys,json
sys.path.insert(0,'advanced'); sys.path.insert(0,'eval')
from build_index import load_corpus
from verifier import load_entity_index
from run_case import run_case
async def main():
    chunks = load_corpus(); idx = load_entity_index()
    r = await run_case(chunks, 'What is the current weekly on-call stipend for engineers, in USD?', idx, use_memory=True)
    print(json.dumps(r['predicted'], indent=1))
asyncio.run(main())
"
```
Show `advanced/memory_writer.py`'s self-heal happening live (the entity
isn't in `memory.json` yet, the correction-signal lookup, the write), then
the final answer: `{"value": "250", "chunk_id": "MEMORY"}`.

**VO:** "Now watch what happens differently. The entity isn't in memory
yet — so instead of guessing, SelfHeal checks a signal feed no baseline
ever gets: a stand-in for the ticket system this bot was never connected
to. Found it. Ticket 4521. Writing it to memory, right now, live. Final
answer: two hundred fifty, cited as memory. This check runs on each query
— not just once, during tuning."

## Beat 5 — The verifier: a targeted demo, not a claimed contribution (1:40–2:11)

```bash
python3 -c "
import sys, json
sys.path.insert(0, 'advanced')
from build_index import load_corpus, build_entity_index
from verifier import verify
chunks = load_corpus(); idx = build_entity_index(chunks)
# A generator that cited the January (stale) VPN policy
pred = {'value': '8', 'chunk_id': 'it_vpn_session_timeout_hours_v1-c01'}
print(json.dumps(verify(chunks, pred, idx), indent=1))
"
```
On screen, this beat is labeled **"Targeted verifier demo"**, not framed as
something that happened during the frozen-test evaluation shown in Beat 6
— because it didn't. `advanced/final_config.json` (the shipped config) has
`use_verifier: false`, and `results/ablations_summary.json`'s explicit
verifier-ON ablation shows byte-identical predictions to verifier-OFF
across every one of the 16 frozen-test cases — the verifier never actually
fired there. This is deliberately disclosed on screen and in the VO, not
glossed over.

**VO:** "I also built a deterministic verifier for stale citations. No
model call, no guessing. On this targeted revision case, it correctly
replaces the stale citation with the current one. But here's the important
part: on the frozen sixteen-case evaluation, it changed exactly zero
outputs. So it's disabled in the shipped accuracy configuration. Not every
component earns its place."

## Beat 6 — Frozen-test proof (2:11–2:46)

Screen: the results table from README.md Section 5, progressively revealed
row by row. `memory_correction: 0/3 across every baseline → 3/3`, and the
memory ON/OFF ablation confirming it — both explicitly scoped to the
`memory_correction` category, not overall accuracy (SelfHeal does **not**
win on raw aggregate — 11/16 vs. A0's 13/16).

**VO:** "Here's the proof, on sixteen test cases the system never saw
during development. Every baseline: zero out of three, on the
memory-correction category this was built for. SelfHeal: three for three.
Flip memory off, change nothing else — back to zero, on those same three
cases. One capability. For this category, that's the entire difference."

## Beat 7 — Why this matters at scale (2:46–3:05)

**VO:** "Think about the scale for a second. One employee getting the
wrong number is an annoyance. Ten thousand employees getting it — that's
not a bug anymore. That's an operating-system problem for your company's
own knowledge." (Thought experiment only — no invented savings, customer
counts, or deployment numbers.)

## Beat 8 — The lesson / hot take (3:05–3:42)

Screen: `CHANGELOG.md`'s Main Failure Mode + Hot Take.

**VO:** "The first time I ran this frozen test, SelfHeal tied the
baseline. Zero out of three, on the exact case it was built for. Not a
crash — just a quiet, forgettable number, the kind you could rationalize
away under deadline pressure. The bug: memory only ever learned from
training-time data, never from what it was actually being asked, live. A
good held-out test doesn't just measure whether you generalize — it
catches you lying to yourself about scope. Silently."

## Beat 9 — Closing / vision (3:42–4:11)

Screen: closer text + explicit `.vision-tag`: "vision, not yet built — see
PRODUCTION_ROADMAP.md".

**VO:** "A RAG system that retrieves information is useful. A system that
can recover when what it retrieves is contradicted by a newer signal —
that's something I'd actually trust inside a company. The production
vision is broader: organizational memory that can reason about versions,
permissions, and conflicting knowledge. That part isn't built yet. This is
the prototype that demonstrates the mechanism on the frozen evaluation."

---

## How V3 was actually built (claim-audited, not just re-recorded)

V3 replaced V2 after a dedicated claim-audit pass (chapter-by-chapter
against `REVIEW_FINDINGS.md`, `advanced/*.py`, the baseline arm scripts,
`results/ablations_summary.json`, `results/results_table.json`, and
`README.md`) surfaced real overclaim risk in the pre-audit draft. Fixed,
with both the narration and the matching on-screen text:

- **The verifier** was framed as an active "always on" safety net. It
  isn't — `advanced/final_config.json` has `use_verifier: false`, and it
  changed zero outputs across every `results/C_*.json` file, including the
  explicit verifier-ON ablation. Reframed as a real, tested, but
  disabled-in-production negative result — arguably a stronger signal of
  engineering discipline than pretending it was load-bearing.
- **Arm B** ("free to search and read... however it likes") was
  "unrestricted agent, unlimited reads" — `baseline/run_B_generalist.py`
  actually caps it at 25 turns / 8 minutes and disallows `Bash`/`Write`/
  `Edit`.
- **"0/3 → 3/3"** is now explicitly scoped to the `memory_correction`
  category everywhere it's said or shown (SelfHeal does not win on raw
  aggregate — disclosed, not hidden).
- **The closing line** ("knows when its own knowledge has expired") implied
  general staleness detection; the mechanism is a signal-triggered
  correction lookup. Replaced with a claim the code actually supports, and
  "demonstrates the mechanism" instead of "proves it works" (n=3 on
  `memory_correction`, confidence without overclaiming).
- "Not a lookup trick" and "continuously" (implying a background daemon)
  were dropped as unnecessary editorializing not worth the fight.

## How it was recorded

`video/beats.html` — rewritten for V3: 9 auto-advancing sections (Cold
open, Evidence, Baselines fail, SelfHeal fires, Verifier, Frozen test,
Scale, The lesson, Closing/vision), a 9-item pipeline stepper, staged
sub-reveals in the SelfHeal and frozen-test beats, driven by a JS clock —
no manual clicking, no editing cuts. Recorded via Playwright against the
pre-installed Chromium (`record_video_dir`, 1280×720, ~254s real-time
capture — `video/record_v3.py`), re-encoded with the pre-installed ffmpeg
(`-c:v libvpx -crf 32 -b:v 0 -an`) to ~3.1MB.

**Narration:** 9 clips via the ElevenLabs MCP connector (`eleven_v3`,
voice "Joel — Natural and reassuring", picked on ElevenLabs' own metadata
— warm/grounded/"trust and authenticity" framing — since audio can't be
judged by ear directly; confirmed acceptable against a 10-second sample
before committing to all 9). Real durations measured (`mutagen`) once
generated: 11.15 / 16.20 / 32.29 / 40.05 / 31.32 / 34.69 / 19.33 / 36.68 /
29.47 seconds — total 251.17s. `video/beats.html`'s timeline was trued up
from a provisional word-count estimate to these exact numbers, back-to-back
with zero inter-beat gap (no accidental dead air).

**Final assembly** (`video/build_v3_page.py`): video + all 9 narration
clips + a 48-cue WebVTT caption track (proportional to per-clause character
length within each beat's real window) assembled into
`video/demo_page_v3.html`, mirroring `video/demo_page.html`'s audio-sync
pattern — a `BOUNDS` array plus a `syncToTime()` handler on the video's
`play`/`pause`/`seeking`/`timeupdate` events — extended from 6 beats to 9.
Page size: 9.85MB, under the 16MB Artifact cap.

**QA** (`video/qa_v3.py`, Playwright): cold-start sync, pause/resume,
mid-beat seek, seek near the very end, caption toggle (`textTrack.mode`
showing/hidden) all verified correct. Caught and fixed two real bugs in
this pass: a narration-track array built from a Python list's `str()`
representation (produced malformed JS, so every `getElementById` call
returned `null` and no narration ever played — audio silently broken
until this was caught), and an external Google Fonts fetch failing with
`ERR_CONNECTION_RESET` in this sandbox (removed; system font stack used
instead). Zero console errors in the final pass. Also caught, during
visual review of the recorded video (not just narration text), that three
on-screen captions still had the pre-audit wording after the narration
itself had already been fixed — beat 9's closer, beat 5's verifier label,
and beat 6's scope qualifier — fixed all three so what's shown matches
what's said.

**Hosted video: https://github.com/user-attachments/assets/af85d5fd-8e7d-4ea8-8a30-2c0806af9c2c**
