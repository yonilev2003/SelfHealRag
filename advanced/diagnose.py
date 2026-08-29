"""Classifies a full dev-round's results via eval/taxonomy.py and picks the
plurality failure category (priority order breaks ties). The actual
correction-signal consultation (for memory_correction_missed) lives in
advanced/memory_writer.py -- the one sanctioned place that opens
data/correction_signals.json, shared by both tuner.py's offline batch
action and generator.py's live runtime self-heal.
"""

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
