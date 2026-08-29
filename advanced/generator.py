"""Shared template, one call per case. ALSO checks advanced/memory.json for
a persisted correction matching a RETRIEVED chunk's entity_key (entity_key
is a corpus-derived property from build_index.py's header parsing, never
the oracle) and injects it into the prompt if present -- the exact
mechanic `results/pretest-selfheal/memory_experiment.json` proved works.

Baselines (A0/A/A2/B) NEVER call this with memory enabled -- they use the
shared `baseline/prompt_template.md` directly with no memory lookup at all
(invariant #5's one deliberate asymmetry).
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
sys.path.insert(0, str(REPO / "advanced"))
from llm_call import run_single_call  # noqa: E402
from build_index import render_chunk  # noqa: E402

TEMPLATE = (REPO / "baseline" / "prompt_template.md").read_text()
MEMORY_PATH = REPO / "advanced" / "memory.json"

MEMORY_ADDENDUM = """
A persisted correction from a prior diagnosis round is also available (it
may or may not be relevant to this question -- use it only if it applies to
the same entity as your answer):
{memory_notes}
"""


def load_memory() -> dict:
    if MEMORY_PATH.exists():
        return json.loads(MEMORY_PATH.read_text())
    return {}


async def generate(chunks: dict, retrieved_ids: list, question: str, traj_path: Path = None,
                   use_memory: bool = True) -> dict:
    excerpts = "\n\n".join(render_chunk(cid, chunks[cid]) for cid in retrieved_ids)
    prompt = TEMPLATE.format(question=question, excerpts=excerpts)

    if use_memory:
        memory = load_memory()
        retrieved_entities = {chunks[cid]["entity_key"] for cid in retrieved_ids}
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
