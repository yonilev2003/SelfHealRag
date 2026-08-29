"""Shared template, one call per case. ALSO self-heals LIVE: checks
advanced/memory.json for a persisted correction matching a RETRIEVED
chunk's entity_key (entity_key is corpus-derived, never the oracle); for
any retrieved entity with NO memory entry yet, consults
data/correction_signals.json on the spot and persists a new one if a
signal exists (advanced/memory_writer.py -- the SAME function
advanced/tuner.py's offline dev-loop action calls, so there is exactly one
signal-consultation code path). This is what makes memory self-healing
actually continuous rather than confined to whichever entities happened to
appear in the dev split -- found necessary live when Phase 5's frozen test
run showed Arm C scoring identically to Arm A on every test-split
memory_correction case, because Phase 4's dev-only batch action had never
had a reason to touch those (disjoint, by design) entities. See
PROCESS.md.

Baselines (A0/A/A2/B) NEVER call this with memory enabled -- they use the
shared `baseline/prompt_template.md` directly with no memory lookup or
self-heal at all (invariant #5's one deliberate asymmetry).
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
sys.path.insert(0, str(REPO / "advanced"))
from llm_call import run_single_call  # noqa: E402
from build_index import render_chunk  # noqa: E402
from memory_writer import heal_entities, load_memory  # noqa: E402

TEMPLATE = (REPO / "baseline" / "prompt_template.md").read_text()

MEMORY_ADDENDUM = """
A persisted correction from a prior diagnosis is also available (it may or
may not be relevant to this question -- use it only if it applies to the
same entity as your answer). If it applies, its value OVERRIDES whatever
the document excerpts say (the excerpts may be stale), and you must cite
"chunk_id": "MEMORY" instead of a document excerpt id:
{memory_notes}
"""


async def generate(chunks: dict, retrieved_ids: list, question: str, traj_path: Path = None,
                   use_memory: bool = True) -> dict:
    excerpts = "\n\n".join(render_chunk(cid, chunks[cid]) for cid in retrieved_ids)
    prompt = TEMPLATE.format(question=question, excerpts=excerpts)

    if use_memory:
        retrieved_entities = {chunks[cid]["entity_key"] for cid in retrieved_ids}
        await heal_entities(retrieved_entities, round_label="live-generate")
        memory = load_memory()
        matches = {ek: v for ek, v in memory.items() if ek in retrieved_entities}
        if matches:
            notes = "\n".join(
                f"- entity {ek}: current value is {v['value']} (source: {v['source_signal_id']})"
                for ek, v in matches.items()
            )
            prompt += MEMORY_ADDENDUM.format(memory_notes=notes)

    res = await run_single_call(prompt, traj_path)
    res["retrieved_chunk_ids"] = retrieved_ids
    return res
