# Video script (≤5:00) — SelfHeal RAG

Real numbers, real commands. Every beat below runs against files already
committed in this repo — nothing here is staged or simulated.

## Beat 1 — Cold open (0:00–0:30)

Screen: side-by-side of `data/corpus/eng_oncall_stipend_usd.md` (states
"$200") and `data/correction_signals.json`'s `TICKET-4521` entry ("approved
raising... from $200 to $250... handbook not yet updated").

**VO:** "This is a real failure mode for any company RAG bot: a fact
changes, the change is recorded somewhere — a ticket, an audit note — and
the document the bot actually reads never gets updated. The bot then
answers confidently, and wrong."

## Beat 2 — Problem, baselines failing on camera (0:30–1:15)

Run live (or sped up 2×, disclosed on screen):
```bash
python3 -c "
import asyncio,sys,json
sys.path.insert(0,'baseline'); sys.path.insert(0,'advanced'); sys.path.insert(0,'eval')
from build_index import load_corpus
import run_A0_fullcontext as A0, run_B_generalist as B
async def main():
    chunks = load_corpus()
    q = 'What is the current weekly on-call stipend for engineers, in USD?'
    r0 = await A0.run_case(chunks, q)
    print('A0 (full 81-chunk corpus in one call):', r0['predicted'])
    rb = await B.run_case(__import__('pathlib').Path('data/corpus'), q)
    print('B (unrestricted agent):', rb['predicted'])
asyncio.run(main())
"
```
**VO:** "Full context — wrong. An agent with unlimited time to read every
document — also wrong. Same $200. Neither extra reading nor extra
reasoning time helps, because the right answer literally isn't in the
corpus."

## Beat 3 — One genuine, unedited SelfHeal run (1:15–2:45)

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
Show the `advanced/memory_writer.py` self-heal happening live in the
terminal (the extraction call + `advanced/memory.json` gaining the new
entry), then the final answer: `{"value": "250", "chunk_id": "MEMORY"}`.

**VO:** "SelfHeal checks a signal feed no baseline gets — a stand-in for
the ticket system a real company's RAG bot was never connected to — finds
the correction, persists it, and cites where it came from. This isn't a
one-time trick: it self-heals continuously as it serves queries, not only
during offline tuning — that continuous-healing property is itself
something this build got wrong on the first try and fixed live (see the
changelog beat)."

## Beat 4 — The verifier catching a stale citation (2:45–3:45)

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
**VO:** "Independent of memory, a deterministic verifier catches stale
citations on in-document policy revisions — the corpus's own supersession
chains — and overrides them with a reason."

## Beat 5 — Frozen-test comparison + changelog + removed experiment (3:45–4:30)

Screen: the results table from README.md Section 5. Point at
`memory_correction: 0/3 across every baseline → 3/3`. Then
`CHANGELOG.md`'s **removed experiment**: LedgerGuard, killed by its own
fair baseline (a plain agent with tools reconciled revenue to the cent,
20× cheaper than orchestration would have measured against) —
`archive/ledgerguard-pretest/README.md`.

**VO:** "The change that moved the number wasn't a smarter prompt or a
retrieval tweak — every other ablation we tried showed zero difference on
held-out data. It was giving the system exactly one new resource: a
channel to information that isn't in its own documents. And we didn't
start here — our first concept died to the same lesson this one almost
repeated."

## Beat 6 — Hot take (4:30–5:00)

**VO:** "The first time we ran the frozen test, SelfHeal tied the plain
baseline — 0 out of 3 on the exact case it was built for. Not a crash, not
an error — just a disappointing number, the kind you could rationalize
away under deadline pressure. The bug: memory only ever learned from
training-time data, not from what it was actually being asked live. A
held-out test split doesn't just measure whether you generalize — it will
catch you gating a capability to the wrong scope, silently, as a boring
number instead of a stack trace. That's the lesson."

---

**Recording notes:** terminal capture via `script`/asciinema or a
Playwright-recorded browser terminal; real command output, no post-hoc
editing of numbers. Total target: 4:30–5:00. Host as an unlisted/private
link or a claude.ai Artifact; final URL goes in the submission form and
this file.
