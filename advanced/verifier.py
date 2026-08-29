"""DETERMINISTIC (LLM-free) verifier: entity lookup -> supersession
chain-head from parsed headers -> override + reason + REQUIRES_HUMAN_REVIEW
flag. Never touches data/fact_registry.json or correction_signals.json --
reads only entity_index.json (built from raw corpus text by build_index.py)
and the generator's own predicted {value, chunk_id}.

Every case is scored regardless of REQUIRES_HUMAN_REVIEW (PLAN.md invariant
#4) -- the flag is metadata, never a scoring exclusion.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO / "advanced" / "entity_index.json"
_VALUE_RE = re.compile(r"[Cc]urrent value:\s*([^.\n]+)\.")


def load_entity_index() -> dict:
    return json.loads(INDEX_PATH.read_text())


def extract_bare_value(chunks: dict, entity_key: str, effective_date: str):
    """Regex-extracts the bare value from whichever sibling chunk of this
    (entity_key, effective_date) version carries the corpus's own
    'Current value: X.' sentence (generate_corpus.py always writes one such
    chunk per version) -- deterministic, LLM-free, reads only chunk TEXT
    that's already in the corpus, never the oracle."""
    for c in chunks.values():
        if c["entity_key"] == entity_key and c["effective_date"] == effective_date:
            m = _VALUE_RE.search(c["text"])
            if m:
                return m.group(1).strip()
    return None


def verify(chunks: dict, predicted: dict, entity_index: dict = None) -> dict:
    """Returns {value, chunk_id, overridden: bool, reason: str,
    requires_human_review: bool}."""
    entity_index = entity_index if entity_index is not None else load_entity_index()
    pred_value = (predicted or {}).get("value")
    pred_chunk_id = (predicted or {}).get("chunk_id", "") or ""

    # Multi-hop or memory-cited answers are outside the verifier's scope
    # (not a single versioned entity's supersession chain) -- pass through.
    if "+" in pred_chunk_id or pred_chunk_id == "MEMORY":
        return {"value": pred_value, "chunk_id": pred_chunk_id, "overridden": False,
                "reason": "not a single-entity citation; verifier scope is supersession chains only",
                "requires_human_review": False}

    if pred_chunk_id not in chunks:
        return {"value": pred_value, "chunk_id": pred_chunk_id, "overridden": False,
                "reason": "cited chunk_id not found in corpus", "requires_human_review": True}

    entity_key = chunks[pred_chunk_id]["entity_key"]
    chain = entity_index.get(entity_key, [])
    if not chain:
        return {"value": pred_value, "chunk_id": pred_chunk_id, "overridden": False,
                "reason": f"no entity_index chain for {entity_key}", "requires_human_review": True}

    # "Chain-head" is the LATEST VERSION (effective_date), not one specific
    # sibling chunk_id -- a version can span multiple chunks (e.g. a header
    # chunk + a value chunk) sharing the same date, and citing either sibling
    # of the current version must NOT be flagged as stale.
    pred_date = chunks[pred_chunk_id]["effective_date"]
    head_date = max(chunks[cid]["effective_date"] for cid in chain)
    if pred_date == head_date:
        return {"value": pred_value, "chunk_id": pred_chunk_id, "overridden": False,
                "reason": "cited chunk already belongs to the chain-head (current) version",
                "requires_human_review": False}

    # Predicted chunk belongs to a superseded version -> override.
    head_chunk_id = next(cid for cid in chain if chunks[cid]["effective_date"] == head_date)
    head_value = extract_bare_value(chunks, entity_key, head_date)
    return {"value": head_value if head_value is not None else pred_value,
            "chunk_id": head_chunk_id, "overridden": True,
            "reason": (f"cited chunk {pred_chunk_id} (effective_date {pred_date}) is superseded "
                      f"by the chain-head version dated {head_date} (e.g. {head_chunk_id})"),
            "requires_human_review": True}
