# Hackathon submission form text

Draft for the micro1 Agentic Workflows Hackathon submission form. Copy the
sections below into the form once the video URL is finalized.

## Title

SelfHeal RAG: A Company-Policy RAG That Catches and Fixes Its Own Stale Answers

## Description

**The problem:** Company policy documents go stale in one very specific,
very common way — a fact changes (Finance approves a stipend increase, an
SLA gets tightened, an NDA term gets extended) and the change is recorded
*somewhere* (a ticket, an audit note) but the document a RAG bot actually
reads never gets updated. The bot then answers confidently and wrong,
citing a real, on-topic document, which is worse than not answering at all.

**The finding that shaped this build:** this is not a "smarter model" or
"better retrieval" problem. Giving a model the *entire* 81-chunk corpus in
one call, or an agent unlimited turns to read every document, both fail
identically on this case class — because the correct answer is not in the
corpus at all. No amount of reading harder or reasoning longer closes an
information-theoretic gap.

**The solution — SelfHeal RAG:** a retrieve → generate → verify pipeline
that adds exactly one new resource no baseline gets — a feed of internal
correction signals (support tickets, audit notes) it can consult and learn
from *continuously and live*, not just during a one-time offline tuning
pass. When it's unsure a retrieved fact is current, it checks the signal
feed, persists any correction it finds, and cites `"MEMORY"` instead of a
stale document chunk, so the source stays auditable. A separate
deterministic verifier also catches stale citations within the corpus's
own document-revision history, independent of memory.

**Measured, on a frozen 16-case held-out test split (entity-disjoint from
dev):** on the `memory_correction` category — the one case class no
baseline can ever solve, by construction — every baseline (full-context,
static RAG, self-correcting RAG, and an unrestricted generalist agent)
scores **0/3**. SelfHeal RAG scores **3/3**. A direct ablation (memory
on/off, same config, nothing else changed) reproduces the same 3/3 → 0/3
swing. On raw aggregate accuracy SelfHeal RAG does *not* beat every
baseline — reported honestly, not hidden — because its retrieval
configuration never improved past its starting point during
self-improvement. The categorical result on `memory_correction` is the
actual claim this submission is built on.

**Built and broken in public:** the most consequential bug in this build
was found by the frozen test itself — the first official run showed
SelfHeal RAG *tying* the static baseline (0/3, not 3/3) because the
self-improvement loop only ever learned corrections for entities seen
during offline dev-tuning, and the entity-disjoint test split (by design)
used different ones. Fixed by making the correction-lookup continuous and
live rather than tuning-time-only — full root cause and fix in
`CHANGELOG.md` / `PROCESS.md`.

**Reproducible end to end:** `make setup && make baseline && make advanced
&& make eval` regenerates every number in this submission from a
deterministic, SHA-256-locked corpus and test split. Full writeup,
architecture, every ablation, and the agent trajectories behind every
claim: https://github.com/yonilev2003/hackathonaug28.08.26

## Video URL

[fill in once hosted]
