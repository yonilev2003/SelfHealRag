#!/usr/bin/env python3
"""Pre-test harness: does the structural gap actually exist?

Runs one reconciliation case through a baseline arm and reports predicted vs
planted true total. Success definition (fixed BEFORE any run, per the kickoff
doc's "define what a good final result looks like before running"):
a close is acceptable when total_revenue_usd is within 0.5% of the planted
true total; the discrepancy list must cite row-level evidence.

Arms:
  text  — single claude-sonnet-5 call, no tools, CSVs inlined in the prompt.
  agent — single generalist claude-sonnet-5 agent session with basic tools
          (Read/Bash/Write/Glob), files on disk. One session, no orchestration,
          no verification, no memory. This is the PDF's "one general purpose
          agent with basic tools" baseline.

Isolation: the case's manifest.json (the oracle) is never copied into the
working directory any arm can see. setting_sources=[] so no CLAUDE.md leaks.
"""

import argparse
import asyncio
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

REPO = Path(__file__).resolve().parent.parent
MODEL = "claude-sonnet-5"

TASK = """You are performing the {month} monthly close for Meridian Goods Co.

The company's Revenue Recognition & Reconciliation Policy is in RULES.md
{rules_hint}. The month's system exports are:
orders.csv, payments.csv, shipments.csv, fx_rates.csv {files_hint}.

Deliver the close: compute recognized revenue for {month} in USD exactly per
the policy, and list every discrepancy / export artifact / reconciliation item
you find with row-level evidence (IDs) and USD impact.

Your FINAL message must be exactly one JSON object, no other text:
{{"total_revenue_usd": <number>,
  "discrepancies": [{{"type": "<short>", "description": "<what/why>",
                      "evidence_ids": ["..."], "impact_usd": <number>}}]}}
"""


def to_jsonable(obj, depth=0):
    if depth > 6:
        return str(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(x, depth + 1) for x in obj]
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v, depth + 1) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        d = {"_type": type(obj).__name__}
        d.update({k: to_jsonable(v, depth + 1) for k, v in vars(obj).items()})
        return d
    return str(obj)


def extract_json(text: str):
    fences = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidates = fences or re.findall(r"\{.*\}", text, re.S)
    for cand in reversed(candidates):
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue
    return None


async def run_arm(arm: str, case_dir: Path, month: str, traj_path: Path):
    work = Path(tempfile.mkdtemp(prefix=f"ledger-{arm}-"))
    for f in ["orders.csv", "payments.csv", "shipments.csv", "fx_rates.csv"]:
        shutil.copy(case_dir / f, work / f)
    shutil.copy(REPO / "eval" / "BUSINESS_RULES.md", work / "RULES.md")

    if arm == "text":
        inline = []
        for f in ["RULES.md", "orders.csv", "payments.csv", "shipments.csv", "fx_rates.csv"]:
            inline.append(f"===== {f} =====\n{(work / f).read_text()}")
        prompt = TASK.format(month=month, rules_hint="(inlined below)",
                             files_hint="(inlined below)") + "\n\n" + "\n\n".join(inline)
        prompt += ("\nWork carefully step by step through every policy rule, "
                   "double-check your arithmetic, then give the final JSON object "
                   "as the last thing in your reply.")
        options = ClaudeAgentOptions(
            model=MODEL, cwd=str(work), allowed_tools=[], disallowed_tools=["*"],
            max_turns=1, setting_sources=[], mcp_servers={}, strict_mcp_config=True,
        )
    else:
        prompt = TASK.format(month=month, rules_hint="in the current directory",
                             files_hint="in the current directory")
        prompt += ("\nYou may use your tools (reading files, running Python) "
                   "however you see fit to get the close right.")
        options = ClaudeAgentOptions(
            model=MODEL, cwd=str(work),
            allowed_tools=["Read", "Bash", "Write", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=60, setting_sources=[], mcp_servers={}, strict_mcp_config=True,
        )

    messages, final_text, result_meta = [], "", {}
    t0 = time.time()
    async for msg in query(prompt=prompt, options=options):
        messages.append(to_jsonable(msg))
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    final_text = block.text
        if isinstance(msg, ResultMessage):
            result_meta = {
                "num_turns": getattr(msg, "num_turns", None),
                "total_cost_usd": getattr(msg, "total_cost_usd", None),
                "duration_ms": getattr(msg, "duration_ms", None),
                "is_error": getattr(msg, "is_error", None),
            }
            if getattr(msg, "result", None):
                final_text = msg.result

    traj_path.parent.mkdir(parents=True, exist_ok=True)
    with open(traj_path, "w") as f:
        for m in messages:
            f.write(json.dumps(m) + "\n")

    parsed = extract_json(final_text or "")
    shutil.rmtree(work, ignore_errors=True)
    return {
        "arm": arm, "case": case_dir.name, "wall_s": round(time.time() - t0, 1),
        "predicted": parsed, **result_meta,
    }


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--arm", choices=["text", "agent"], required=True)
    ap.add_argument("--traj-dir", default=str(REPO / "trajectories" / "pretest"))
    args = ap.parse_args()
    case_dir = Path(args.case)
    manifest = json.loads((case_dir / "manifest.json").read_text())
    month_name = {"07": "July"}.get(manifest["month"][5:7], manifest["month"]) + " " + manifest["month"][:4]

    res = await run_arm(args.arm, case_dir, month_name,
                        Path(args.traj_dir) / f"{case_dir.name}-{args.arm}.jsonl")

    true_total = manifest["true_total_usd"]
    pred = None
    if isinstance(res["predicted"], dict):
        try:
            pred = float(res["predicted"].get("total_revenue_usd"))
        except (TypeError, ValueError):
            pred = None
    res["true_total_usd"] = true_total
    res["predicted_total_usd"] = pred
    if pred is not None:
        res["abs_error_usd"] = round(abs(pred - true_total), 2)
        res["pct_error"] = round(abs(pred - true_total) / true_total * 100, 4)
        res["pass_0p5pct"] = res["pct_error"] <= 0.5
    n_found = len(res["predicted"].get("discrepancies", [])) if isinstance(res["predicted"], dict) else 0
    res["n_discrepancies_reported"] = n_found
    out = {k: v for k, v in res.items() if k != "predicted"}
    print(json.dumps(out, indent=1))
    results_dir = REPO / "results" / "pretest"
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / f"{case_dir.name}-{args.arm}.json", "w") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
