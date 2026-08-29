#!/usr/bin/env python3
"""Phase 5/6: builds the primary results table (all arms x frozen test
split) + the 3-way structural proof (A0/A/A2 vs C on memory_correction and
contradiction test cases) + human-time/cost rows. Reads only
results/*.json + data/probes/test_split.locked.json.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO / "results"

import sys  # noqa: E402
sys.path.insert(0, str(REPO / "eval"))
from match import grounded_match  # noqa: E402

ARMS = ["A0", "A", "A2", "B", "C"]
HUMAN_SEC_PER_CHUNK = 20
HUMAN_CHUNKS_TO_CHECK = 15
HUMAN_SEC_PER_TICKET_CROSSCHECK = 90  # for memory_correction cases specifically


def load_results(arm: str) -> dict:
    path = RESULTS_DIR / f"{arm}_test.json"
    return json.loads(path.read_text()) if path.exists() else {}


def grade(results: dict, test_split: list) -> dict:
    rows = []
    n_correct = 0
    total_cost, total_wall = 0.0, 0.0
    for p in test_split:
        r = results.get(p["probe_id"], {})
        pred = r.get("predicted") or {}
        correct = grounded_match(pred.get("value"), pred.get("chunk_id"),
                                 p["expected_value"], p["expected_chunk_id"])
        n_correct += int(correct)
        total_cost += r.get("total_cost_usd") or 0
        total_wall += r.get("wall_s") or 0
        rows.append({"probe_id": p["probe_id"], "category": p["category"], "correct": correct})
    n = len(test_split)
    return {"n_correct": n_correct, "n_total": n, "accuracy": round(n_correct / n, 4) if n else 0,
            "total_cost_usd": round(total_cost, 4), "total_wall_s": round(total_wall, 1),
            "cost_per_case_usd": round(total_cost / n, 4) if n else 0,
            "wall_s_per_case": round(total_wall / n, 2) if n else 0, "rows": rows}


def main():
    test_split = json.loads((REPO / "data" / "probes" / "test_split.locked.json").read_text())
    all_results = {arm: load_results(arm) for arm in ARMS}
    graded = {arm: grade(all_results[arm], test_split) for arm in ARMS if all_results[arm]}

    # human-time modeled estimate (disclosed assumptions, never presented as measured)
    n_memory = sum(1 for p in test_split if p["category"] == "memory_correction")
    n_other = len(test_split) - n_memory
    human_time_s = (n_other * HUMAN_CHUNKS_TO_CHECK * HUMAN_SEC_PER_CHUNK
                    + n_memory * HUMAN_SEC_PER_TICKET_CROSSCHECK)

    # 3-way structural proof: A0/A/A2 vs C, on memory_correction + contradiction categories
    three_way = {"memory_correction": [], "contradiction": []}
    for p in test_split:
        if p["category"] not in three_way:
            continue
        row = {"probe_id": p["probe_id"]}
        for arm in ["A0", "A", "A2", "C"]:
            r = all_results.get(arm, {}).get(p["probe_id"], {})
            pred = r.get("predicted") or {}
            row[arm] = grounded_match(pred.get("value"), pred.get("chunk_id"),
                                      p["expected_value"], p["expected_chunk_id"])
        row["all_baselines_fail_only_C_succeeds"] = (
            not row.get("A0") and not row.get("A") and not row.get("A2") and row.get("C"))
        three_way[p["category"]].append(row)

    n_proof_memory = sum(1 for r in three_way["memory_correction"] if r["all_baselines_fail_only_C_succeeds"])
    n_proof_contradiction = sum(1 for r in three_way["contradiction"] if r["all_baselines_fail_only_C_succeeds"])

    summary_table = {arm: {k: v for k, v in g.items() if k != "rows"} for arm, g in graded.items()}
    out = {
        "primary_metric": "Grounded Answer Accuracy (16-case frozen test split)",
        "results_table": summary_table,
        "human_time_modeled_seconds": human_time_s,
        "human_time_methodology": (
            f"Modeled, not measured: {HUMAN_CHUNKS_TO_CHECK} chunks x {HUMAN_SEC_PER_CHUNK}s/chunk "
            f"for {n_other} non-memory cases + {HUMAN_SEC_PER_TICKET_CROSSCHECK}s/case ticket "
            f"cross-check for {n_memory} memory_correction cases."),
        "three_way_structural_proof": {
            "memory_correction": {"n_cases": len(three_way["memory_correction"]),
                                  "n_all_baselines_fail_only_C_succeeds": n_proof_memory,
                                  "rows": three_way["memory_correction"]},
            "contradiction": {"n_cases": len(three_way["contradiction"]),
                              "n_all_baselines_fail_only_C_succeeds": n_proof_contradiction,
                              "rows": three_way["contradiction"]},
        },
    }
    (RESULTS_DIR / "results_table.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "three_way_structural_proof"} | {
        "three_way_structural_proof_counts": {
            "memory_correction": f"{n_proof_memory}/{len(three_way['memory_correction'])}",
            "contradiction": f"{n_proof_contradiction}/{len(three_way['contradiction'])}",
        }}, indent=1))


if __name__ == "__main__":
    main()
