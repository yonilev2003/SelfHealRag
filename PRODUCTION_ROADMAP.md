# Path to production — what "Corporate RAG Healer" would actually need

This repo demonstrates a **mechanism**: given a retrieved fact and a
correction signal, self-heal the answer and keep it healed. That
mechanism is real, measured, and holds on held-out data (README Section
5). It is **not** a deployable product yet. This document names the gap
honestly, tied to the actual code, not to marketing language — the kind
of scope a technical buyer could hand to their own engineers and trust.

## 1. Ingestion — "connect it to a folder in a day" is not true yet

`advanced/build_index.py`'s `load_corpus()` reads `*.md` files from one
flat directory and parses a fixed inline header
(`<!-- chunk_id: ... entity_key: ... effective_date: ... supersedes_id: ... -->`)
that `eval/generate_corpus.py` writes into every file by construction.
Pointed at a real company folder — PDFs, DOCX, Confluence exports, Slack
threads — this code produces **zero chunks**, not a degraded result. What
a real connector needs: a multi-format loader (PDF/DOCX/HTML/Confluence
API/SharePoint API), a real chunking algorithm, incremental
crawl/diff (not "reprocess everything from scratch," which is what
`build_index.py`'s `main()` does today), and file-permission/ACL
awareness. **Effort: real, well-trodden engineering — days to a couple of
weeks, not a research problem.**

## 2. Automatic version/supersession detection — the hard, novel part

`advanced/verifier.py`'s supersession-chain logic depends entirely on
`effective_date`/`supersedes_id` being handed to it as ground truth. Real
documents don't carry that metadata inline. Inferring it — via a source
system's own version history where available (SharePoint/Confluence page
history), or via LLM-based entity/version resolution across semantically
similar chunks from different documents and times where it isn't — is
**unimplemented here** and is the one piece of this repo's approach that
doesn't yet exist as general-purpose code. **This is the actual
differentiated IP to build, not the retrieval or the self-heal loop
themselves.**

## 3. A real live-signal connector, with entity resolution

`data/correction_signals.json` is a static, hand-authored fixture where
every signal's `entity_key` is pre-labeled to match the corpus's own
taxonomy exactly. `advanced/memory_writer.py`'s one LLM call
(`prompts/signal_extractor.md`) is told the entity up front and only
extracts a bare value — it does **zero entity linking**. A real connector
needs, per source (Slack/ticketing/email): auth + rate-limit handling, a
classifier for "is this even a correction signal," an entity-resolution
step (embedding similarity against known entities + LLM disambiguation),
and a conflict/recency policy when two signals disagree. **This is
currently the single most unimplemented piece of the "live signal feed"
story** — today it's a lookup table, not a feed.

## 4. Confidence-gated autonomy, not human review by default

**The design goal is not "a human checks every correction."** That
doesn't scale, and it defeats the point of a *self-healing* system — if
every correction needs a person, the system isn't healing, it's
drafting. The goal is maximal autonomy: strong enough verification that
the large majority of corrections apply end-to-end with no human in the
path at all, and human attention is spent only where it actually changes
the outcome.

**Today's code is neither of those things — it's a third state, and
that's the actual gap.** `advanced/memory_writer.py`'s `heal_entities()`
writes a new correction straight into `advanced/memory.json` the moment
the LLM extracts *any* value, with no confidence signal computed, no
gate, and no escalation path — not "confidently autonomous," just
"unconditionally autonomous." `advanced/generator.py` then serves that
value on the very next query. For HR/legal/finance content that's a real
liability: a single LLM misread of an ambiguous message (sarcasm, a
hypothetical, a since-reversed decision) becomes a silently-adopted fact
with nobody prompted to confirm it.

**Closing that gap needs two different mechanisms, not one:**

- **Human-in-the-loop (HITL) as a configurable *exception path*, not a
  default gate.** Most extractions should carry a confidence signal
  (extraction-model agreement, signal-source trust tier, how cleanly the
  text maps to a known entity) high enough to auto-apply — that's meant
  to be the common case, staying fast and unattended. A correction routes
  to a human queue only when it trips a configurable trigger: low
  extraction confidence, a direct contradiction with another live signal,
  a change above a customer-defined impact threshold (e.g. anything
  touching compensation or legal terms), or a source tier the customer
  hasn't pre-trusted. Concretely: a `pending_memory.json` queue for
  anything that trips a trigger, with signal provenance + confidence
  attached, an Approve/Reject surface (Slack message or a one-page UI),
  everything else applying straight through. Thresholds are policy, set
  per customer, not a hardcoded universal gate.

- **Human evaluation as a separate, systematic QA/learning layer — not
  tied to any single output.** Independent of whether any individual
  correction was auto-applied or human-approved, a production deployment
  needs planned, ongoing **sampling** of served answers for quality
  measurement: clear grading rubrics (not ad hoc judgment calls), quality
  control on the evaluators themselves, calibration / inter-rater
  agreement tracking so the measurement is trustworthy, and a sample rate
  that scales with volume and risk (denser sampling on high-impact or
  low-confidence traffic, sparser on routine cases) instead of trying to
  manually review everything as volume grows. This is the RLHF-style
  feedback loop that actually improves the system over time — distinct
  from, and complementary to, the HITL exception path above.

Both are **genuinely small, well-scoped additions** on top of the
existing `memory_writer.py` interface (a confidence score, a queue, a
policy config, a sampling job) — not a redesign — but neither exists in
this repo today.

*(Not wired into this repo's live path or the frozen test: doing so would
change Arm C's measured behavior and require re-running the hash-locked
test split, which is out of scope for a hackathon submission under
deadline — but it's the first thing to build before any real deployment.)*

## 5. Multi-tenancy, a real datastore, a persisted index

`advanced/memory.json` and `advanced/entity_index.json` are flat,
single-process files — `memory_writer.py`'s own docstring calls itself
"thread-unsafe by design." No tenant partitioning, no locking, no audit
trail beyond `source_signal_id`/`round_added`. This maps cleanly onto
Postgres (tenant-scoped tables, row-level transactions, an audit-log
table) **without touching the core retrieval/verification/generation
logic** — a storage-layer swap, not a redesign. The one piece that isn't
just storage: `advanced/retriever.py`'s `retrieve()` rebuilds a full BM25
index from every chunk's text on **every single call**, with no
persistence or caching. Invisible at 81 chunks; a real per-query
latency/cost problem at a company's actual corpus size. Needs a persisted
search index (OpenSearch/Elasticsearch, or a vector store) — well-trodden,
not novel.

## Honest bottom line

The algorithmic core — retrieve, generate, verify, self-heal, and the
discipline of proving it on held-out data — is done and measured. What's
missing to sell this as a real implementation engagement is almost
entirely **integration engineering and a confidence/trust layer**, not
more research: multi-format ingestion, automatic version inference, a
real signal connector with entity resolution, a confidence-scored
autonomy gate (auto-apply by default, escalate on threshold, sample for
QA — not blanket human review), and a production datastore. A scoped
pilot — one already-versioned document source (e.g. Confluence page
history), one real signal channel (a dedicated ticket queue), a
confidence threshold plus an exception queue in front of memory writes,
deployed read-only for one team — is a credible few-weeks engagement, not
a wish. That's the honest gap this roadmap exists to name.
