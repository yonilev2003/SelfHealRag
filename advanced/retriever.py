"""BM25 retriever with tunable knobs (PLAN.md Phase 3/4): k, hybrid_date_boost.
Same function is called by Arm A/A2 baselines (round-0 config, never tuned)
and Arm C (config evolves across the Phase-4 dev loop).
"""

from rank_bm25 import BM25Okapi

DEFAULT_K = 3


def retrieve(chunks: dict, question: str, k: int = DEFAULT_K, hybrid_date_boost: bool = False) -> list:
    """Returns a list of chunk_ids, best first."""
    ids = list(chunks.keys())
    corpus_tokens = [chunks[i]["text"].lower().split() for i in ids]
    bm25 = BM25Okapi(corpus_tokens)
    scores = list(bm25.get_scores(question.lower().split()))

    if hybrid_date_boost:
        # Small boost toward more recent chunks WITHIN each entity's own
        # chunk set, so a superseding chunk doesn't need to out-lexically-
        # match its own superseded predecessor to win a close BM25 race --
        # it only competes against chunks of OTHER entities on raw score.
        by_entity = {}
        for cid in ids:
            by_entity.setdefault(chunks[cid]["entity_key"], []).append(cid)
        for entity_ids in by_entity.values():
            if len(entity_ids) < 2:
                continue
            ordered = sorted(entity_ids, key=lambda c: chunks[c]["effective_date"])
            for rank, cid in enumerate(ordered):
                idx = ids.index(cid)
                scores[idx] += 0.5 * rank  # later version gets a small additive boost

    ranked = sorted(zip(ids, scores), key=lambda x: -x[1])
    return [cid for cid, _ in ranked[:k]]
