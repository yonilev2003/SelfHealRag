#!/usr/bin/env python3
"""Rubric-based scoring: baseline vs advanced, on the frozen test split.

Reads results/{A0,A,A2,B,C}_test.json (written by scripts/run_baseline.sh /
run_advanced.sh via eval/run_eval.py) and grades each with eval/grade_test.py
(the single, independent, oracle-free grader). Primary metric: Grounded
Answer Accuracy. "baseline" = Arm B (the kickoff doc's own fair baseline:
"one general purpose agent with basic tools"); "advanced" = Arm C
(SelfHeal RAG, final tuned config). All arms are reported for the full
comparison table; this {baseline, advanced, delta} shape is what
CHANGELOG.md / the Makefile / CI expect.
"""

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO / "results"

ARMS = ["A0", "A", "A2", "B", "C"]
BASELINE_ARM = "B"
ADVANCED_ARM = "C"


def run_and_capture(script_path: str) -> str:
    result = subprocess.run(["bash", script_path], capture_output=True, text=True, cwd=REPO)
    return result.stdout + result.stderr


def grade_arm(arm: str) -> dict:
    results_path = RESULTS_DIR / f"{arm}_test.json"
    if not results_path.exists():
        return {"error": f"{results_path} not found -- run scripts/run_baseline.sh / run_advanced.sh first"}
    out = subprocess.run(
        ["python3", str(REPO / "eval" / "grade_test.py"), str(results_path)],
        capture_output=True, text=True, cwd=REPO,
    )
    return json.loads(out.stdout)


def score(arm: str) -> dict:
    graded = grade_arm(arm)
    if "error" in graded:
        return graded
    return {"total": graded["accuracy"], "n_correct": graded["n_correct"], "n_total": graded["n_total"],
            "rows": graded["rows"]}


def main():
    all_scores = {arm: score(arm) for arm in ARMS}
    baseline_score = all_scores[BASELINE_ARM]
    advanced_score = all_scores[ADVANCED_ARM]
    delta = None
    if "total" in baseline_score and "total" in advanced_score:
        delta = round(advanced_score["total"] - baseline_score["total"], 4)

    result = {
        "primary_metric": "Grounded Answer Accuracy (joint value + citation exact-match, frozen 16-case test split)",
        "baseline_arm": BASELINE_ARM, "advanced_arm": ADVANCED_ARM,
        "baseline": {k: v for k, v in baseline_score.items() if k != "rows"},
        "advanced": {k: v for k, v in advanced_score.items() if k != "rows"},
        "delta": delta,
        "all_arms": {arm: {k: v for k, v in s.items() if k != "rows"} for arm, s in all_scores.items()},
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
