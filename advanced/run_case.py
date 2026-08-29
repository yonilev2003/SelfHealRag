"""Runs ONE case through the full Arm C pipeline: retrieve -> generate
(with memory lookup) -> verify. Flags let ablations toggle each component
independently: --no-verifier --no-hybrid --no-memory --k N.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "advanced"))
sys.path.insert(0, str(REPO / "eval"))
from build_index import load_corpus  # noqa: E402
from retriever import retrieve  # noqa: E402
from generator import generate  # noqa: E402
from verifier import load_entity_index, verify  # noqa: E402


async def run_case(chunks: dict, question: str, entity_index: dict = None, traj_path: Path = None,
                   k: int = 3, hybrid_date_boost: bool = False,
                   use_verifier: bool = True, use_memory: bool = True) -> dict:
    retrieved = retrieve(chunks, question, k=k, hybrid_date_boost=hybrid_date_boost)
    gen_res = await generate(chunks, retrieved, question, traj_path, use_memory=use_memory)
    predicted = gen_res.get("predicted") or {}

    if use_verifier:
        entity_index = entity_index if entity_index is not None else load_entity_index()
        vres = verify(chunks, predicted, entity_index)
        final_value, final_chunk_id = vres["value"], vres["chunk_id"]
        verifier_meta = {"overridden": vres["overridden"], "reason": vres["reason"],
                         "requires_human_review": vres["requires_human_review"]}
    else:
        final_value, final_chunk_id = predicted.get("value"), predicted.get("chunk_id")
        verifier_meta = {"overridden": False, "reason": "verifier disabled", "requires_human_review": False}

    return {
        "predicted": {"value": final_value, "chunk_id": final_chunk_id},
        "generator_predicted": predicted,
        "retrieved_chunk_ids": retrieved,
        "verifier": verifier_meta,
        "total_cost_usd": gen_res.get("total_cost_usd"),
        "wall_s": gen_res.get("wall_s"),
        "config": {"k": k, "hybrid_date_boost": hybrid_date_boost,
                  "use_verifier": use_verifier, "use_memory": use_memory},
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--no-hybrid", action="store_true")
    ap.add_argument("--no-verifier", action="store_true")
    ap.add_argument("--no-memory", action="store_true")
    args = ap.parse_args()

    chunks = load_corpus()
    res = await run_case(chunks, args.question, k=args.k, hybrid_date_boost=not args.no_hybrid,
                         use_verifier=not args.no_verifier, use_memory=not args.no_memory)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
