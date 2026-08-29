"""Classifies a full dev-round's results via eval/taxonomy.py, picks the
plurality failure category (priority order breaks ties), and — for
memory_correction_missed only — cross-references data/correction_signals.json
against each failing case's entity_key (never the oracle registry directly,
matching how a human triaging a ticket would work).
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
from taxonomy import classify  # noqa: E402

PRIORITY = ["memory_correction_missed", "retrieval_miss", "hallucinated_citation",
           "wrong_override", "stale_value_uncaught", "wrong_value_other"]


def diagnose_round(dev_split: list, results: dict) -> dict:
    by_category = {}
    for probe in dev_split:
        r = results.get(probe["probe_id"], {})
        cat = classify(probe, r)
        by_category.setdefault(cat, []).append(probe["probe_id"])

    n_correct = len(by_category.get("correct", []))
    failure_counts = {k: len(v) for k, v in by_category.items() if k != "correct"}
    plurality = None
    if failure_counts:
        max_count = max(failure_counts.values())
        for cat in PRIORITY:
            if failure_counts.get(cat) == max_count:
                plurality = cat
                break

    return {"n_correct": n_correct, "n_total": len(dev_split),
            "failure_counts_by_taxonomy": failure_counts,
            "case_ids_by_taxonomy": by_category,
            "plurality_category": plurality}


def find_correction_signals(entity_keys: list) -> dict:
    """entity_key -> signal dict, for any entity_key with a matching signal."""
    signals = json.loads((REPO / "data" / "correction_signals.json").read_text())
    by_entity = {s["entity_key"]: s for s in signals}
    return {ek: by_entity[ek] for ek in entity_keys if ek in by_entity}
