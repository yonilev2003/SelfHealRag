# Hackathon submission form text

Draft for the micro1 Agentic Workflows Hackathon submission form. Copy the
sections below into the form once the video URL is finalized.

## Title

SelfHeal RAG — Correction-Aware Memory for Stale Enterprise Knowledge

## Description

**The problem:** Company policy documents go stale in one very specific,
very common way — a fact changes (Finance approves a stipend increase, an
SLA gets tightened, an NDA term gets extended) and the change is recorded
*somewhere* (a ticket, an audit note) but the document a RAG bot actually
reads never gets updated. The bot then answers confidently and wrong,
citing a real, on-topic document, which is worse than not answering at all.

**The finding that shaped this build:** this is not a "smarter model" or
"better retrieval" problem. Giving a model the *entire* 81-chunk synthetic
corpus in one call, or a sandboxed generalist agent (`Read`/`Grep`/`Glob`
only, capped at 25 turns / 8 minutes — not unlimited) full read access to
every document, both fail identically on this case class — because the
correct answer is not in the corpus at all. No amount of reading harder or
reasoning longer closes an information-theoretic gap.

**The solution — SelfHeal RAG:** a retrieve → generate pipeline that adds
exactly one new resource no baseline gets — a feed of correction signals
(synthetic support tickets, audit notes, each pre-associated with a known
entity key) it checks for every retrieved entity, on each relevant query —
not only during a one-time offline tuning pass. When an entity it just
retrieved has no persisted correction yet, it checks the signal feed,
persists any match it finds, and cites `"MEMORY"` instead of a stale
document chunk, so the source stays auditable. This demonstrates
correction *propagation* from a known signal to a known entity — not
autonomous, general staleness detection over arbitrary content. A
separate deterministic supersession verifier is also implemented and
unit-tested, but is disabled in the reported configuration
(`use_verifier: false`) because an explicit ablation changed zero outputs
across the frozen test — kept and disclosed as a real negative result, not
a claimed contribution. (The verifier demo in the video is a targeted,
labeled demonstration of the mechanism working on a synthetic revision
case — it is not an event from the frozen-test run.)

**Measured, on a frozen 16-case held-out test split (entity-disjoint from
dev):** on `memory_correction` (N=3) — the one case class no baseline can
solve, by construction, since only SelfHeal reads the correction-signal
feed — every baseline scores **0/3**. SelfHeal RAG scores **3/3**,
reproduced by a direct ablation: flipping `use_memory` off (same config,
nothing else changed) returns SelfHeal to **0/3** on that same slice. On
raw aggregate accuracy across all 16 cases, SelfHeal RAG does **not** lead
— A0 (full-context) scores 13/16, B (sandboxed agent) 12/16, SelfHeal RAG
11/16 — reported honestly, not hidden, because its retrieval configuration
never improved past its starting point during self-improvement. The
categorical, ablation-confirmed result on `memory_correction` — a 3-case
slice, not a large-sample claim — is the actual contribution this
submission is built on.

**Built and broken in public:** the most consequential bug in this build
was found by the frozen test itself — the first official run showed
SelfHeal RAG *tying* the static baseline (0/3, not 3/3) because the
self-improvement loop only ever learned corrections for entities seen
during offline dev-tuning, and the entity-disjoint test split (by design)
used different ones. Fixed by making the correction-lookup run live, on
each relevant query, rather than tuning-time-only — full root cause and
fix in `CHANGELOG.md` / `PROCESS.md`.

**Reproducible end to end:** `make setup && make baseline && make advanced
&& make eval` regenerates every number in this submission. Corpus
generation, the dev/test split, grading, and hashing are deterministic
and SHA-256-locked; live LLM inference is not guaranteed deterministic
call-to-call, so the *committed* results under `results/` are the
reproducible artifact, not a promise that a fresh run reproduces every
prediction byte-for-byte. Full writeup, architecture, and every ablation:
https://github.com/yonilev2003/SelfHealRag

## Video URL

https://github.com/user-attachments/assets/af85d5fd-8e7d-4ea8-8a30-2c0806af9c2c
