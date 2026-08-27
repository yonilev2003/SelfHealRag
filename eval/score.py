#!/usr/bin/env python3
"""Rubric-based scoring: baseline vs advanced.

Fill in CRITERIA once the problem is known. Each check_fn takes the captured
stdout of a run and returns a 0-1 score; the weighted sum gives one comparable
number instead of an eyeballed "looks better." This is the file that turns
"Measured Improvement" from a claim into a number in CHANGELOG.md.
"""
import json
import subprocess

# TODO: define once the problem is known. Keep each criterion independently
# testable — e.g. {"correctness": (0.5, check_correctness), "latency": (0.2, check_latency)}
CRITERIA = {
    # "correctness": (0.5, lambda output: 1.0 if "expected_marker" in output else 0.0),
}


def run_and_capture(script_path: str) -> str:
    result = subprocess.run(["bash", script_path], capture_output=True, text=True)
    return result.stdout


def score(output: str) -> dict:
    scores = {name: {"weight": w, "value": fn(output)} for name, (w, fn) in CRITERIA.items()}
    total = sum(s["weight"] * s["value"] for s in scores.values())
    return {"criteria": scores, "total": total}


def main():
    baseline_out = run_and_capture("scripts/run_baseline.sh")
    advanced_out = run_and_capture("scripts/run_advanced.sh")
    baseline_score = score(baseline_out)
    advanced_score = score(advanced_out)
    result = {
        "baseline": baseline_score,
        "advanced": advanced_score,
        "delta": advanced_score["total"] - baseline_score["total"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
