# AGENTS.md

Tool-agnostic orientation for any coding agent working in this repo.
`CLAUDE.md` covers Claude-Code-specific workflow/hook conventions; this
file is the mental model any agent needs regardless of which tool it is.

## System purpose

SelfHeal RAG: a correction-aware, stateful RAG pipeline over a versioned
company-policy corpus. It closes a specific gap — the correct answer is
categorically absent from the indexed corpus and reachable only through
an external correction signal (a ticket, an audit note) — by combining
BM25 retrieval, a persistent entity-scoped correction memory, a
deterministic supersession verifier, and a failure-taxonomy-driven
self-improvement loop. See `README.md` §1–4 for the full mechanism and
equations.

## Architecture (one paragraph)

`retriever.py` (BM25, optional temporal prior) → `generator.py` (checks
`memory.json` per retrieved entity, consults `correction_signals.json` and
persists a new entry via `memory_writer.py` if one's missing, then calls
the LLM with any matching memory note appended) → optionally
`verifier.py` (deterministic chain-head check against `entity_index.json`
— **disabled in the shipped config**, see below). `tuner.py` drives an
offline dev-loop that classifies failures via `eval/taxonomy.py` and tries
one mapped action per round, keeping it only on a ≥2-case dev-accuracy
improvement (memory writes excepted, kept unconditionally).

## Key entry points

| File | Role |
|---|---|
| `advanced/run_case.py` | Runs one case through the full Arm C pipeline; `--no-verifier`/`--no-hybrid`/`--no-memory`/`--k N` flags drive the ablations |
| `advanced/generator.py` | The live self-heal path — read this first to understand the actual runtime behavior |
| `advanced/verifier.py` | Deterministic chain-head override logic (currently disabled — see below) |
| `advanced/tuner.py` | The offline self-improvement loop |
| `eval/taxonomy.py` | The 6-category failure classifier the tuner acts on |
| `eval/match.py` | The single grounded-match rule used by both the dev loop and the frozen-test grader — never duplicate this logic elsewhere |
| `baseline/run_{A0,A,A2,B}_*.py` | The four baseline arms, all sharing `baseline/prompt_template.md` |

## Commands

```bash
make setup      # installs rank_bm25 + claude-agent-sdk
make baseline   # Arms A0/A/A2/B over the frozen test split
make advanced   # Arm C over the frozen test split
make eval       # eval/score.py — the results table
make verify-no-leak   # static oracle-isolation audit, no API calls
python3 eval/run_ablations.py   # memory/verifier/hybrid ablations
```

## Frozen / evaluation invariants — do not weaken silently

- `data/probes/test_split.locked.json` and `data/probes/dev_split.json` are
  SHA-256-locked and entity-disjoint by design (the structural-novelty
  requirement that caught the Phase-5 memory-gating bug — see
  `CHANGELOG.md`'s Main Failure Mode). Regenerating them is fine
  (`eval/split_and_lock.py` is deterministic and byte-identical), but never
  hand-edit the committed split files.
- `data/fact_registry.json` (the ground-truth oracle) and the locked test
  split are read **only** by grading code (`eval/grade_test.py`,
  `make verify-no-leak`), never by any arm's runtime path. If you add a
  new arm or code path, run `make verify-no-leak` before trusting it.
- `eval/match.py`'s `grounded_match()` is the single source of truth for
  "correct" across the dev loop, the frozen-test grader, and the Phase-1
  pre-test gate. Don't reimplement matching logic elsewhere — import it.
- The five arms (A0/A/A2/B/C) must keep sharing one prompt template, one
  model, and byte-identical chunk rendering (`build_index.py`). The one
  intentional asymmetry — only Arm C reads `correction_signals.json` — is
  the capability under test, not something to quietly extend to baselines
  or quietly remove from C.

## Files agents must not mutate casually

- `results/*.json`, `results/*.csv`, `results/test_run_log.md` — the
  committed, judged evaluation artifacts. Regenerate via the real pipeline
  (`make baseline && make advanced && make eval`), never hand-edit.
- `trajectories/raw/*.jsonl` and `trajectories/**` — raw session logs,
  disclosure artifacts. Never hand-edit.
- `video/demo_page.html` and `video/demo_page_v3.html` — published,
  QA-passed demo recordings. Rebuilding either means re-running the full
  record → compress → assemble → QA pipeline (`video/record_v3.py` →
  `video/build_v3_page.py` → `video/qa_v3.py` is the reference sequence for
  V3), not hand-patching the generated HTML.
- `.claude/hooks/guard_deploy.py` and `.claude/settings.json`'s hook wiring
  — the deploy-confirmation safety gate. Fix genuine bugs (e.g. path
  resolution), never weaken what it catches.

## Known limitations (see `README.md` §9 for the full list)

The verifier is real and unit-tested but showed zero held-out impact and
is **off** in the shipped config. Entity/version resolution is given as
ground truth, not inferred — the actual unbuilt IP for a real deployment
(`PRODUCTION_ROADMAP.md` §2–3). SelfHeal does not lead on raw aggregate
accuracy; its proven advantage is categorical and scoped to the
`memory_correction` category (N=3).

## Current shipped/reported configuration (`advanced/final_config.json`)

```json
{"k": 3, "hybrid_date_boost": false, "use_verifier": false, "use_memory": true}
```

Only `use_memory` differs from Arm A's static-RAG config — that single
flag is the entire measured source of SelfHeal's advantage (§6, memory
ON/OFF ablation). If you're tempted to flip `use_verifier` or
`hybrid_date_boost` back on because they "should" help: they were tried,
ablated, and shown to move nothing on the frozen test — re-enabling either
without new evidence reintroduces exactly the overclaim this repo's own
audit removed.
