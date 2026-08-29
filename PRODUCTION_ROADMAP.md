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

## 4. Human approval before a correction goes live

`advanced/memory_writer.py`'s `heal_entities()` writes a new correction
straight into `advanced/memory.json` the moment the LLM extracts a value
— no draft state, no reviewer sign-off, no undo path beyond hand-editing
the file. `advanced/generator.py` then serves that value on the very next
query. For HR/legal/finance content, one LLM misread of an ambiguous
message (sarcasm, a hypothetical, a since-reversed decision) becomes a
silently-adopted fact with nobody prompted to confirm it. **Minimal fix:**
a `pending_memory.json` queue — extracted corrections land there with
signal provenance and a confidence score; a `Heal Proposal` (Slack message
or a one-page review UI) with Approve/Reject; only approved entries move
into the live store `generator.py` actually reads. This is a genuinely
small, well-scoped addition on top of the existing `memory_writer.py`
interface — not a redesign.

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
entirely **integration engineering and a trust layer**, not more
research: multi-format ingestion, automatic version inference, a real
signal connector with entity resolution, human-approval gating, and a
production datastore. A scoped pilot — one already-versioned document
source (e.g. Confluence page history), one real signal channel (a
dedicated ticket queue), a human-approval queue in front of any memory
write, deployed read-only for one team — is a credible few-weeks
engagement, not a wish. That's the honest gap this roadmap exists to name.
