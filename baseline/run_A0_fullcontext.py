"""Arm A0: whole corpus inline, one call, no retrieval. The PDF's own
"one direct prompt with basic instructions" baseline, given maximum
information (everything) to make the strongest possible case for a single
prompt. NEVER given advanced/memory.json or data/correction_signals.json
(invariant #5) -- exactly what a naive "paste everything into the prompt"
approach could do today, nothing more.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
sys.path.insert(0, str(REPO / "advanced"))
from llm_call import run_single_call  # noqa: E402
from build_index import render_chunk  # noqa: E402

TEMPLATE = (REPO / "baseline" / "prompt_template.md").read_text()


async def run_case(chunks: dict, question: str, traj_path: Path = None) -> dict:
    excerpts = "\n\n".join(render_chunk(cid, c) for cid, c in chunks.items())
    prompt = TEMPLATE.format(question=question, excerpts=excerpts)
    res = await run_single_call(prompt, traj_path)
    res["retrieved_chunk_ids"] = list(chunks.keys())
    return res
