"""Arm A: BM25 k=3, static config (never tuned) -> one call. Uses the SAME
advanced/retriever.py function Arm C uses, at retriever.py's default (k=3,
hybrid_date_boost=False) -- Arm C's Phase-4 config knobs never touch this
arm (invariant #5: baselines are frozen, only advanced/ config evolves).
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


async def run_case(chunks: dict, question: str, traj_path: Path = None, k: int = 3) -> dict:
    retrieved = retrieve(chunks, question, k=k, hybrid_date_boost=False)
    excerpts = "\n\n".join(render_chunk(cid, chunks[cid]) for cid in retrieved)
    prompt = TEMPLATE.format(question=question, excerpts=excerpts)
    res = await run_single_call(prompt, traj_path)
    res["retrieved_chunk_ids"] = retrieved
    return res
