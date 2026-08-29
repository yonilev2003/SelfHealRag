"""Arm A2: Arm A's first answer, PLUS exactly one additional forced
re-query turn with a different search angle (prompts/a2_recheck.md) before
finalizing -- the genuine self-correction control the grill required
(distinct from a bare "please double-check yourself" single-call prompt).
Re-query angle: the original question expanded with revision-signal terms
("supersedes updated effective current latest"), so it's more likely to
surface a chunk the first retrieval missed -- exactly the failure mode
Phase 1's Arm A showed (mini-01: BM25 missed the value-bearing chunk).
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
sys.path.insert(0, str(REPO / "advanced"))
from llm_call import run_single_call  # noqa: E402
from build_index import render_chunk  # noqa: E402
from retriever import retrieve  # noqa: E402

TEMPLATE = (REPO / "baseline" / "prompt_template.md").read_text()
RECHECK_TEMPLATE = (REPO / "prompts" / "a2_recheck.md").read_text()
REQUERY_SUFFIX = " supersedes updated effective current latest revision"


async def run_case(chunks: dict, question: str, traj_path: Path = None, k: int = 3) -> dict:
    first_retrieved = retrieve(chunks, question, k=k, hybrid_date_boost=False)
    first_excerpts = "\n\n".join(render_chunk(cid, chunks[cid]) for cid in first_retrieved)
    first_prompt = TEMPLATE.format(question=question, excerpts=first_excerpts)
    traj1 = traj_path.with_suffix(".turn1.jsonl") if traj_path else None
    first_res = await run_single_call(first_prompt, traj1)
    first_answer = first_res.get("predicted") or {}

    requery_retrieved = retrieve(chunks, question + REQUERY_SUFFIX, k=k, hybrid_date_boost=False)
    new_ids = [cid for cid in requery_retrieved if cid not in first_retrieved]
    requery_excerpts = "\n\n".join(render_chunk(cid, chunks[cid]) for cid in new_ids) or "(no new excerpts found)"

    recheck_prompt = RECHECK_TEMPLATE.format(
        first_answer=first_answer, question=question, requery_excerpts=requery_excerpts)
    traj2 = traj_path.with_suffix(".turn2.jsonl") if traj_path else None
    final_res = await run_single_call(recheck_prompt, traj2)
    final_res["retrieved_chunk_ids"] = sorted(set(first_retrieved) | set(requery_retrieved))
    final_res["first_turn_answer"] = first_answer
    final_res["total_cost_usd"] = (first_res.get("total_cost_usd") or 0) + (final_res.get("total_cost_usd") or 0)
    final_res["wall_s"] = (first_res.get("wall_s") or 0) + (final_res.get("wall_s") or 0)
    return final_res
