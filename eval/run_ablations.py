#!/usr/bin/env python3
"""Phase 5 ablations (PLAN.md): Arm C at varied configs, all on the frozen
test split. The PRIMARY row is memory ON/OFF, scored specifically on the
memory_correction test cases. Secondary: verifier ON/OFF, tuned vs round-0
default, hybrid ON/OFF. Each variant writes its own results file (never
overwriting results/C_test.json, the official run) and appends its own
test_run_log.md receipt.
"""

import asyncio
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
from run_eval import run_arm_over_split  # noqa: E402
from match import grounded_match  # noqa: E402

FINAL_CONFIG = json.loads((REPO / "advanced" / "final_config.json").read_text())
ROUND0_CONFIG = {"k": 3, "hybrid_date_boost": False, "use_verifier": False, "use_memory": True}

VARIANTS = {
    "C_memory_off": {**FINAL_CONFIG, "use_memory": False},
    "C_verifier_on": {**FINAL_CONFIG, "use_verifier": True},
    "C_round0_config": ROUND0_CONFIG,
    "C_hybrid_on": {**FINAL_CONFIG, "hybrid_date_boost": True},
}


async def run_variant(tag: str, config: dict):
    """Runs Arm C at `config` over the test split, writes results/{tag}.json
    (renamed from run_arm_over_split's default results/C_test.json output,
    so each variant gets its own file and the official run is never
    overwritten)."""
    from run_eval import RESULTS_DIR
    receipt = await run_arm_over_split("C", "test", config)
    (RESULTS_DIR / "C_test.json").rename(RESULTS_DIR / f"{tag}.json")
    (RESULTS_DIR / "C_test.csv").rename(RESULTS_DIR / f"{tag}.csv")
    return receipt


def score_on_category(results_path: Path, category: str) -> dict:
    test_split = json.loads((REPO / "data" / "probes" / "test_split.locked.json").read_text())
    results = json.loads(results_path.read_text())
    cases = [p for p in test_split if p["category"] == category]
    n_correct = 0
    rows = []
    for p in cases:
        r = results.get(p["probe_id"], {})
        pred = r.get("predicted") or {}
        correct = grounded_match(pred.get("value"), pred.get("chunk_id"),
                                 p["expected_value"], p["expected_chunk_id"])
        n_correct += int(correct)
        rows.append({"probe_id": p["probe_id"], "correct": correct, "predicted": pred,
                     "expected": {"value": p["expected_value"], "chunk_id": p["expected_chunk_id"]}})
    return {"category": category, "n_correct": n_correct, "n_total": len(cases), "rows": rows}


async def main():
    results_dir = REPO / "results"
    official_path = results_dir / "C_test.json"
    if not official_path.exists():
        raise SystemExit("results/C_test.json (the official frozen run) not found -- "
                         "run scripts/run_advanced.sh first")
    # Preserve the official run BEFORE any variant overwrites C_test.json --
    # run_arm_over_split always writes to that exact path.
    official_backup = results_dir / "C_official_test.json"
    official_backup.write_bytes(official_path.read_bytes())
    (results_dir / "C_official_test.csv").write_bytes((results_dir / "C_test.csv").read_bytes())

    summary = {}
    for tag, config in VARIANTS.items():
        print(f"=== {tag}: {config} ===", file=sys.stderr)
        await run_variant(tag, config)
        summary[tag] = config

    # Restore the official run as C_test.json (run_variant's last iteration
    # left C_test.json missing -- it renames it away every time).
    official_path.write_bytes(official_backup.read_bytes())
    (results_dir / "C_test.csv").write_bytes((results_dir / "C_official_test.csv").read_bytes())

    memory_on_score = score_on_category(official_backup, "memory_correction")
    memory_off_score = score_on_category(results_dir / "C_memory_off.json", "memory_correction")
    verifier_on_score = score_on_category(results_dir / "C_verifier_on.json", "contradiction")
    verifier_off_score = score_on_category(official_backup, "contradiction")

    out = {
        "PRIMARY_memory_ablation": {
            "memory_ON (official C_test.json)": memory_on_score,
            "memory_OFF": memory_off_score,
        },
        "secondary_verifier_ablation_on_contradiction": {
            "verifier_ON": verifier_on_score,
            "verifier_OFF (official C_test.json)": verifier_off_score,
        },
        "variant_configs": summary,
    }
    (results_dir / "ablations_summary.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "variant_configs"} | {
        "PRIMARY_memory_ablation": {
            kk: {k2: v2 for k2, v2 in vv.items() if k2 != "rows"}
            for kk, vv in out["PRIMARY_memory_ablation"].items()},
        "secondary_verifier_ablation_on_contradiction": {
            kk: {k2: v2 for k2, v2 in vv.items() if k2 != "rows"}
            for kk, vv in out["secondary_verifier_ablation_on_contradiction"].items()},
    }, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
