#!/usr/bin/env python3
"""Frozen-test grader. Stdlib + eval/match.py only -- NO import of
advanced/verifier.py, advanced/tuner.py, or any LLM client (invariant #4):
the pass/fail check is inline exact-match against the locked test split,
independent of the solution's own inner loop.

Usage: python3 eval/grade_test.py <results.json> [--test-split PATH]
results.json: {probe_id: {"predicted": {"value":..., "chunk_id":...}}}
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from match import grounded_match  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def grade(results: dict, test_split: list) -> dict:
    rows = []
    n_correct = 0
    for probe in test_split:
        r = results.get(probe["probe_id"], {})
        pred = r.get("predicted") or {}
        correct = grounded_match(pred.get("value"), pred.get("chunk_id"),
                                 probe["expected_value"], probe["expected_chunk_id"])
        n_correct += int(correct)
        rows.append({"probe_id": probe["probe_id"], "category": probe["category"],
                     "trap_subtype": probe["trap_subtype"], "correct": correct,
                     "expected": {"value": probe["expected_value"], "chunk_id": probe["expected_chunk_id"]},
                     "predicted": pred})
    return {"n_correct": n_correct, "n_total": len(test_split),
            "accuracy": round(n_correct / len(test_split), 4) if test_split else 0.0, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_path")
    ap.add_argument("--test-split", default=str(REPO / "data" / "probes" / "test_split.locked.json"))
    args = ap.parse_args()
    results = json.loads(Path(args.results_path).read_text())
    test_split = json.loads(Path(args.test_split).read_text())
    out = grade(results, test_split)
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()
