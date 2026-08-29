"""Deterministic failure-taxonomy classifier (PLAN.md Phase 4). Priority
order (checked top to bottom, first match wins): memory_correction_missed >
retrieval_miss > hallucinated_citation > wrong_override > stale_value_uncaught
> wrong_value_other. `correct` is terminal (checked first).

Consumes dev_split.json's expected_value/expected_chunk_id -- permitted
per invariant #1 (ordinary dev-set tuning, not an oracle leak; the
prohibition is scoped to fact_registry.json and the locked test split).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from match import grounded_match, values_match  # noqa: E402


def _ids(chunk_id_field: str) -> set:
    return set(str(chunk_id_field or "").split("+"))


def classify(probe: dict, result: dict) -> str:
    predicted = result.get("predicted") or {}
    if grounded_match(predicted.get("value"), predicted.get("chunk_id"),
                      probe["expected_value"], probe["expected_chunk_id"]):
        return "correct"

    if probe["category"] == "memory_correction":
        return "memory_correction_missed"

    expected_ids = _ids(probe["expected_chunk_id"])
    retrieved = set(result.get("retrieved_chunk_ids") or [])
    if not expected_ids.issubset(retrieved):
        return "retrieval_miss"

    value_ok = values_match(predicted.get("value"), probe["expected_value"])
    citation_ok = _ids(predicted.get("chunk_id")) == expected_ids
    if value_ok and not citation_ok:
        return "hallucinated_citation"

    gen_pred = result.get("generator_predicted") or predicted
    gen_correct = grounded_match(gen_pred.get("value"), gen_pred.get("chunk_id"),
                                 probe["expected_value"], probe["expected_chunk_id"])
    if gen_correct and not grounded_match(predicted.get("value"), predicted.get("chunk_id"),
                                          probe["expected_value"], probe["expected_chunk_id"]):
        return "wrong_override"

    if probe["category"] == "contradiction":
        return "stale_value_uncaught"

    return "wrong_value_other"
