#!/usr/bin/env python3
"""Orchestrates one arm over one split (dev or test), writes
results/<arm>_<split>.json + a per-case CSV, and — for the frozen test
split only — auto-appends a receipt to results/test_run_log.md on EVERY
invocation (invariant #8), regardless of outcome.

Usage: python3 eval/run_eval.py --arm {A0,A,A2,B,C} --split {dev,test} [--config-json '{"k":3,...}']
"""

import argparse
import asyncio
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
sys.path.insert(0, str(REPO / "advanced"))
sys.path.insert(0, str(REPO / "baseline"))
from build_index import load_corpus  # noqa: E402
from verifier import load_entity_index  # noqa: E402

RESULTS_DIR = REPO / "results"
TRAJ_DIR = REPO / "trajectories"


async def run_arm_over_split(arm: str, split_name: str, config: dict = None):
    corpus_dir = REPO / "data" / "corpus"
    chunks = load_corpus(corpus_dir)
    split_path = REPO / "data" / "probes" / (
        "dev_split.json" if split_name == "dev" else "test_split.locked.json")
    probes = json.loads(split_path.read_text())

    traj_dir = TRAJ_DIR / f"{arm}_{split_name}"
    results = {}
    total_cost, total_wall = 0.0, 0.0

    if arm == "A0":
        import run_A0_fullcontext as mod
        run_one = lambda p: mod.run_case(chunks, p["question"], traj_dir / f"{p['probe_id']}.jsonl")
    elif arm == "A":
        import run_A_static_rag as mod
        run_one = lambda p: mod.run_case(chunks, p["question"], traj_dir / f"{p['probe_id']}.jsonl")
    elif arm == "A2":
        import run_A2_agentic as mod
        run_one = lambda p: mod.run_case(chunks, p["question"], traj_dir / f"{p['probe_id']}.jsonl")
    elif arm == "B":
        import run_B_generalist as mod
        run_one = lambda p: mod.run_case(corpus_dir, p["question"], traj_dir / f"{p['probe_id']}.jsonl")
    elif arm == "C":
        from run_case import run_case as c_run_case
        entity_index = load_entity_index()
        cfg = config or json.loads((REPO / "advanced" / "final_config.json").read_text())
        run_one = lambda p: c_run_case(chunks, p["question"], entity_index=entity_index,
                                       traj_path=traj_dir / f"{p['probe_id']}.jsonl", **cfg)
    else:
        raise ValueError(f"unknown arm {arm}")

    for p in probes:
        res = await run_one(p)
        results[p["probe_id"]] = res
        total_cost += res.get("total_cost_usd") or 0
        total_wall += res.get("wall_s") or 0

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{arm}_{split_name}.json"
    out_path.write_text(json.dumps(results, indent=1))

    csv_path = RESULTS_DIR / f"{arm}_{split_name}.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["probe_id", "category", "question", "expected_value", "expected_chunk_id",
                   "predicted_value", "predicted_chunk_id", "correct"])
        sys.path.insert(0, str(REPO / "eval"))
        from match import grounded_match
        for p in probes:
            r = results[p["probe_id"]]
            pred = r.get("predicted") or {}
            correct = grounded_match(pred.get("value"), pred.get("chunk_id"),
                                     p["expected_value"], p["expected_chunk_id"])
            w.writerow([p["probe_id"], p["category"], p["question"], p["expected_value"],
                       p["expected_chunk_id"], pred.get("value"), pred.get("chunk_id"), correct])

    receipt = {"arm": arm, "split": split_name, "config": config, "n_cases": len(probes),
              "total_cost_usd": round(total_cost, 4), "total_wall_s": round(total_wall, 1),
              "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    if split_name == "test":
        import subprocess
        git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        results_hash = __import__("hashlib").sha256(out_path.read_bytes()).hexdigest()[:16]
        receipt["git_sha"] = git_sha
        receipt["results_hash"] = results_hash
        log_path = RESULTS_DIR / "test_run_log.md"
        with open(log_path, "a") as f:
            f.write(f"- {receipt['timestamp_utc']} | arm={arm} | git_sha={git_sha[:10]} | "
                   f"results_hash={results_hash} | n={len(probes)} | "
                   f"cost=${receipt['total_cost_usd']} | wall={receipt['total_wall_s']}s\n")

    print(json.dumps(receipt, indent=1))
    return receipt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["A0", "A", "A2", "B", "C"])
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--config-json", default=None)
    args = ap.parse_args()
    config = json.loads(args.config_json) if args.config_json else None
    asyncio.run(run_arm_over_split(args.arm, args.split, config))


if __name__ == "__main__":
    main()
