#!/usr/bin/env python3
"""Gate run 2: the one hardening attempt (CLAUDE.md hard gate, PLAN.md rule
3/4), executed per the CHECKPOINT_1.md recommendation -- scale the corpus
(~60 chunks, 2 additional decoy supersession pairs on different entities,
20 noise-topic distractor docs) rather than the originally-coded same-size
recipe, since run 1's STOP_TRIVIAL came from the pilot having no room for
A0/B to lose track of anything at n=12 chunks.

Same 6 probes, same target facts/ground truth as run 1 -- only the
surrounding corpus changes. Same decision rule, evaluated fresh. This is the
SECOND and FINAL gate run: if it doesn't clear PROCEED, CLAUDE.md's hard gate
applies (2 failed attempts -> stop and consult, no third pass).
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS_DIR = REPO / "results" / "pretest-selfheal"

sys.path.insert(0, str(HERE))
from run_gate import run_all_arms, decide  # noqa: E402


async def main():
    print("=== Regenerating corpus (--scale-up) ===", file=sys.stderr)
    subprocess.run([sys.executable, str(HERE / "gen_mini_corpus.py"), "--scale-up"],
                   check=True, cwd=HERE)

    template = (HERE / "prompt_template.md").read_text()
    probes = json.loads((HERE / "probes.json").read_text())

    print("=== Gate run 2 (scaled corpus) ===", file=sys.stderr)
    run2 = await run_all_arms(HERE / "corpus", probes, template, tag="run2_scaled")
    with open(RESULTS_DIR / "run2_scaled.json", "w") as f:
        json.dump(run2, f, indent=1)

    total_cost = sum(run2["cost_usd"].values())
    total_time_s = sum(run2["wall_s"].values())
    scale = 248 / max(run2["n_chunks"], 1)
    projected_cost = total_cost * scale
    projected_minutes = total_time_s * scale / 60
    budget_ok = projected_cost < 15 and projected_minutes < 40
    budget = {"scale_factor": round(scale, 2), "projected_cost_usd": round(projected_cost, 2),
              "projected_minutes": round(projected_minutes, 2), "budget_ok": budget_ok}
    with open(RESULTS_DIR / "budget_projection_run2_scaled.json", "w") as f:
        json.dump(budget, f, indent=1)

    verdict, reason = decide(run2["A0"], run2["A"], run2["B"], budget_ok)
    # Rule 4: a second run that still isn't PROCEED is the hard stop,
    # regardless of which of HARDEN/STOP_TRIVIAL it individually maps to.
    final_verdict = "PROCEED" if verdict == "PROCEED" else "STOP_2ND_ATTEMPT"
    final_reason = reason if verdict == "PROCEED" else (
        f"Second (scaled) gate run still not PROCEED ({verdict}: {reason}). "
        "This is the 2nd failed attempt under CLAUDE.md's hard gate -- "
        "no third pass, consult the user."
    )

    receipt = {
        "final_verdict": final_verdict, "final_reason": final_reason,
        "corpus": {"n_docs": None, "n_chunks": run2["n_chunks"], "scaled_up": True},
        "run2_scaled": {
            "A0": {k: v for k, v in run2["A0"].items() if k != "rows"},
            "A": {k: v for k, v in run2["A"].items() if k != "rows"},
            "B": {k: v for k, v in run2["B"].items() if k != "rows"},
            "cost_usd": run2["cost_usd"], "wall_s": run2["wall_s"], "n_chunks": run2["n_chunks"],
        },
        "budget_projection": budget,
    }
    with open(RESULTS_DIR / "gate_receipt_final.json", "w") as f:
        json.dump(receipt, f, indent=1)
    print(json.dumps(receipt, indent=1))
    print(f"\nFINAL VERDICT: {final_verdict} — {final_reason}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
