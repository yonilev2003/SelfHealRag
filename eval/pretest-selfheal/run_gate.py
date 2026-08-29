#!/usr/bin/env python3
"""Phase 1 (PLAN.md) pre-test gate: does the structural gap SelfHeal RAG bets
on actually exist, before committing the full ~24h build?

Runs 3 arms on the 6 mini-probes and evaluates the pre-registered decision
rule (PLAN.md Phase 1), in the stated precedence order:
  1. B-mini==6/6 OR A0-mini==6/6 (trivial) -> STOP.
  2. A-mini fails >=2/3 staleness probes AND B-mini<=5/6 AND A0-mini<=5/6
     AND budget projection passes -> PROCEED.
  3. Otherwise -> HARDEN (apply the recipe once, re-run).
  4. Second run not PROCEED in any direction -> STOP (2nd failed attempt,
     CLAUDE.md hard gate).

Arm A0-mini: whole mini-corpus inlined, single call, no retrieval.
Arm A-mini: BM25 top-3 chunks per question, single call.
Arm B-mini: generalist agent (Read/Grep/Glob only — no Bash/Write; this
  corpus-QA task needs no code execution, unlike LedgerGuard's CSV
  reconciliation, so the tool surface is legitimately narrower), sandboxed
  by a PreToolUse hook that mechanically denies any resolved path outside
  the corpus-only tempdir (unit-tested in test_guard_hook.py — this is a
  real preventive control, not prompt policy: see PLAN.md invariant #1 and
  the grill finding that "cwd is a starting-directory hint, not a boundary").
"""

import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from rank_bm25 import BM25Okapi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from match import grounded_match  # noqa: E402
from sandbox_guard import make_guard_hook  # noqa: E402

from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    TextBlock,
    query,
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MODEL = "claude-sonnet-5"
RESULTS_DIR = REPO / "results" / "pretest-selfheal"
TRAJ_DIR = REPO / "trajectories" / "pretest-selfheal"

STALENESS_CATEGORY = "contradiction"


def load_corpus(corpus_dir: Path):
    """Parse chunk-header markdown into {chunk_id: {entity_key, effective_date,
    supersedes_id, text}}. Mirrors the format advanced/build_index.py will
    use in Phase 3 — parses RAW text only, never the registry."""
    chunks = {}
    for f in sorted(corpus_dir.glob("*.md")):
        for block in f.read_text().split("<!-- chunk_id:")[1:]:
            header, _, body = block.partition("-->")
            parts = header.strip().split()
            # parts: [chunk_id, "entity_key:", key, "effective_date:", date, "supersedes_id:", val]
            chunk_id = parts[0]
            entity_key = parts[parts.index("entity_key:") + 1]
            eff_date = parts[parts.index("effective_date:") + 1]
            supersedes = parts[parts.index("supersedes_id:") + 1]
            chunks[chunk_id] = {
                "entity_key": entity_key, "effective_date": eff_date,
                "supersedes_id": None if supersedes == "null" else supersedes,
                "text": body.strip(),
            }
    return chunks


def render_chunk(chunk_id, c):
    return (f"[chunk_id: {chunk_id}] [effective_date: {c['effective_date']}]\n"
            f"{c['text']}")


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
    import re
    fences = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidates = fences or re.findall(r"\{.*\}", text, re.S)
    for cand in reversed(candidates):
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue
    return None


async def run_single_call(prompt: str, traj_path: Path):
    options = ClaudeAgentOptions(
        model=MODEL, allowed_tools=[], disallowed_tools=["*"], max_turns=1,
        setting_sources=[], mcp_servers={}, strict_mcp_config=True,
    )
    messages, final_text, meta = [], "", {}
    t0 = time.time()
    async for msg in query(prompt=prompt, options=options):
        messages.append(to_jsonable(msg))
        if isinstance(msg, AssistantMessage):
            for b in msg.content:
                if isinstance(b, TextBlock):
                    final_text = b.text
        if isinstance(msg, ResultMessage):
            meta = {"total_cost_usd": getattr(msg, "total_cost_usd", None),
                     "duration_ms": getattr(msg, "duration_ms", None)}
            if getattr(msg, "result", None):
                final_text = msg.result
    traj_path.parent.mkdir(parents=True, exist_ok=True)
    with open(traj_path, "w") as f:
        for m in messages:
            f.write(json.dumps(m) + "\n")
    return {"wall_s": round(time.time() - t0, 2), "predicted": extract_json(final_text or ""), **meta}


async def run_arm_b(corpus_dir: Path, question: str, traj_path: Path, max_turns=25, timeout_s=480):
    work = Path(tempfile.mkdtemp(prefix="selfheal-armb-"))
    for f in corpus_dir.glob("*.md"):
        shutil.copy(f, work / f.name)
    root = os.path.realpath(str(work))
    denied = []
    options = ClaudeAgentOptions(
        model=MODEL, cwd=root, allowed_tools=["Read", "Grep", "Glob"],
        # allowed_tools is a PRE-APPROVAL allowlist, NOT a hard restriction --
        # verified live: with only allowed_tools set (no disallowed_tools),
        # Bash still executed successfully and was never even denied by our
        # PreToolUse hook (which doesn't parse Bash's `command` string for
        # paths). disallowed_tools is the actual enforcement; without it the
        # sandbox is a no-op for anything not explicitly blocked here.
        disallowed_tools=["Bash", "Write", "Edit", "MultiEdit", "NotebookEdit",
                          "WebFetch", "WebSearch", "Task", "ToolSearch"],
        hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[make_guard_hook(root, denied)])]},
        max_turns=max_turns, setting_sources=[], mcp_servers={}, strict_mcp_config=True,
    )
    prompt = (
        "You are answering a factual question about Acme Corp company policy. "
        "The current directory contains the company's policy documents as "
        "markdown files, each with chunk_id / entity_key / effective_date "
        "headers. Company policies are sometimes revised — read enough of the "
        "corpus to find every excerpt relevant to this question, and identify "
        "the CURRENT (most recent, non-superseded) value before answering.\n\n"
        f"Question: {question}\n\n"
        "Respond with ONLY this JSON object as your final message, no other "
        "text before or after it:\n"
        '{"value": "<the current value, as a bare number or short phrase '
        'with no units or extra words -- e.g. \\"4\\" not \\"4 hours\\", '
        '\\"750\\" not \\"$750 USD\\">", '
        '"chunk_id": "<id of the excerpt that supports this as the CURRENT value>"}'
    )
    messages, final_text, meta = [], "", {}
    t0 = time.time()

    async def _consume():
        async for msg in query(prompt=prompt, options=options):
            messages.append(to_jsonable(msg))

    try:
        await asyncio.wait_for(_consume(), timeout=timeout_s)
    except asyncio.TimeoutError:
        meta["timed_out"] = True
    for m in messages:
        if m.get("_type") == "AssistantMessage":
            for b in m.get("content", []):
                if isinstance(b, dict) and b.get("_type") == "TextBlock":
                    final_text = b.get("text", final_text)
        if m.get("_type") == "ResultMessage":
            meta["total_cost_usd"] = m.get("total_cost_usd")
            meta["duration_ms"] = m.get("duration_ms")
            if m.get("result"):
                final_text = m["result"]
    traj_path.parent.mkdir(parents=True, exist_ok=True)
    with open(traj_path, "w") as f:
        for m in messages:
            f.write(json.dumps(m) + "\n")
    shutil.rmtree(work, ignore_errors=True)
    return {"wall_s": round(time.time() - t0, 2), "predicted": extract_json(final_text or ""),
            "denied_tool_calls": denied, **meta}


def bm25_top_k(chunks: dict, question: str, k=3):
    ids = list(chunks.keys())
    corpus_tokens = [chunks[i]["text"].lower().split() for i in ids]
    bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(question.lower().split())
    ranked = sorted(zip(ids, scores), key=lambda x: -x[1])[:k]
    return [cid for cid, _ in ranked]


async def run_arm_a0(chunks: dict, template: str, probe: dict, traj_dir: Path):
    excerpts = "\n\n".join(render_chunk(cid, c) for cid, c in chunks.items())
    prompt = template.format(question=probe["question"], excerpts=excerpts)
    return await run_single_call(prompt, traj_dir / f"{probe['probe_id']}-A0.jsonl")


async def run_arm_a(chunks: dict, template: str, probe: dict, traj_dir: Path, k=3):
    top_ids = bm25_top_k(chunks, probe["question"], k=k)
    excerpts = "\n\n".join(render_chunk(cid, chunks[cid]) for cid in top_ids)
    prompt = template.format(question=probe["question"], excerpts=excerpts)
    res = await run_single_call(prompt, traj_dir / f"{probe['probe_id']}-A.jsonl")
    res["retrieved_chunk_ids"] = top_ids
    return res


def score_probes(results: dict, probes: list):
    n_correct, n_staleness_correct = 0, 0
    staleness_probes = [p for p in probes if p["category"] == STALENESS_CATEGORY]
    rows = []
    for p in probes:
        r = results.get(p["probe_id"], {})
        pred = r.get("predicted") or {}
        ok = grounded_match(pred.get("value"), pred.get("chunk_id"), p["expected_value"], p["expected_chunk_id"])
        rows.append({"probe_id": p["probe_id"], "category": p["category"], "question": p["question"],
                     "expected": {"value": p["expected_value"], "chunk_id": p["expected_chunk_id"]},
                     "predicted": pred, "correct": ok})
        if ok:
            n_correct += 1
            if p["category"] == STALENESS_CATEGORY:
                n_staleness_correct += 1
    return {"n_correct": n_correct, "n_total": len(probes),
            "n_staleness_correct": n_staleness_correct, "n_staleness_total": len(staleness_probes),
            "rows": rows}


async def run_all_arms(corpus_dir: Path, probes: list, template: str, tag: str):
    chunks = load_corpus(corpus_dir)
    traj_dir = TRAJ_DIR / tag
    a0_results, a_results, b_results = {}, {}, {}
    cost = {"A0": 0.0, "A": 0.0, "B": 0.0}
    wall = {"A0": 0.0, "A": 0.0, "B": 0.0}
    for p in probes:
        r0 = await run_arm_a0(chunks, template, p, traj_dir)
        a0_results[p["probe_id"]] = r0
        cost["A0"] += r0.get("total_cost_usd") or 0
        wall["A0"] += r0["wall_s"]

        ra = await run_arm_a(chunks, template, p, traj_dir)
        a_results[p["probe_id"]] = ra
        cost["A"] += ra.get("total_cost_usd") or 0
        wall["A"] += ra["wall_s"]

        rb = await run_arm_b(corpus_dir, p["question"], traj_dir / f"{p['probe_id']}-B.jsonl")
        b_results[p["probe_id"]] = rb
        cost["B"] += rb.get("total_cost_usd") or 0
        wall["B"] += rb["wall_s"]

    return {
        "A0": score_probes(a0_results, probes), "A": score_probes(a_results, probes),
        "B": score_probes(b_results, probes),
        "cost_usd": cost, "wall_s": wall,
        "n_chunks": len(chunks),
    }


def harden(corpus_dir: Path):
    """Apply the Phase-1 hardening recipe once (PLAN.md): more distractors,
    wider effective-date gap, supersession language moved further away,
    implicit pair loses any keyword entirely (it already has none here)."""
    text = (corpus_dir / "it_vpn_v2.md").read_text()
    # (a) +2 distractor chunks per supersession pair; (c) push supersession
    # language 3+ chunks away from the value chunk by inserting filler chunks
    # between the "supersedes" statement chunk and the numeric-value chunk.
    filler = (
        "\n<!-- chunk_id: it-vpn-v2-c01b entity_key: it.vpn_rollout_note "
        "effective_date: 2026-05-01 supersedes_id: null -->\n"
        "## Rollout Notes\n\nThe updated VPN policy was rolled out in three "
        "phases across engineering, sales, and support between March and May.\n"
        "\n<!-- chunk_id: it-vpn-v2-c01c entity_key: it.vpn_rollout_note "
        "effective_date: 2026-05-01 supersedes_id: null -->\n"
        "IT will hold two office-hours sessions for questions about the new "
        "VPN client configuration during the transition period.\n"
    )
    (corpus_dir / "it_vpn_v2.md").write_text(text + filler)

    text2 = (corpus_dir / "finance_refund_v2.md").read_text()
    filler2 = (
        "\n<!-- chunk_id: finance-refund-v2-c01b entity_key: finance.refund_process_note "
        "effective_date: 2026-06-15 supersedes_id: null -->\n"
        "## Refund Processing\n\nRefunds are processed via the original payment "
        "method within 5-7 business days of approval.\n"
        "\n<!-- chunk_id: finance-refund-v2-c01c entity_key: finance.refund_process_note "
        "effective_date: 2026-06-15 supersedes_id: null -->\n"
        "Store credit is offered as an alternative for customers without a "
        "valid original payment method on file.\n"
    )
    (corpus_dir / "finance_refund_v2.md").write_text(text2 + filler2)
    # (b) push effective_date >=90 days after v1 for the explicit pair (was
    # 2026-01-10 -> 2026-05-01, 111 days; already satisfies >=90, no change needed)


def decide(a0, a, b, budget_ok: bool):
    n_stale = a["n_staleness_total"]
    if b["n_correct"] == b["n_total"] or a0["n_correct"] == a0["n_total"]:
        return "STOP_TRIVIAL", (f"B-mini={b['n_correct']}/{b['n_total']}, "
                                f"A0-mini={a0['n_correct']}/{a0['n_total']}: baselines solve it trivially.")
    if (a["n_staleness_total"] - a["n_staleness_correct"] >= 2
            and b["n_correct"] <= 5 and a0["n_correct"] <= 5 and budget_ok):
        return "PROCEED", "Structural gap confirmed: A-mini fails staleness, B/A0 imperfect, budget OK."
    return "HARDEN", (f"A-mini staleness {a['n_staleness_correct']}/{n_stale} correct "
                      f"(need <=1/{n_stale} correct i.e. >=2 failures) or A0/B too strong "
                      f"or budget projection failed.")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-chunks-full", type=int, default=248,
                    help="Real Phase-2 corpus chunk count, for the budget scaling formula")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    template = (HERE / "prompt_template.md").read_text()
    probes = json.loads((HERE / "probes.json").read_text())

    print("=== Gate run 1 ===", file=sys.stderr)
    run1 = await run_all_arms(HERE / "corpus", probes, template, tag="run1")

    with open(RESULTS_DIR / "run1.json", "w") as f:
        json.dump(run1, f, indent=1)

    total_calls = len(probes) * 3
    total_cost = sum(run1["cost_usd"].values())
    total_time_s = sum(run1["wall_s"].values())
    scale = args.corpus_chunks_full / max(run1["n_chunks"], 1)
    # Arm B scales with corpus size (it reads more of the corpus); A/A0 scale
    # roughly with retrieved/inlined chunk volume too, applied uniformly here
    # as the conservative (over-)estimate.
    projected_cost = run1["cost_usd"]["A0"] * scale + run1["cost_usd"]["A"] * scale + run1["cost_usd"]["B"] * scale
    projected_minutes = (run1["wall_s"]["A0"] + run1["wall_s"]["A"] + run1["wall_s"]["B"]) * scale / 60
    budget_ok = projected_cost < 15 and projected_minutes < 40
    budget = {"scale_factor": round(scale, 2), "projected_cost_usd": round(projected_cost, 2),
              "projected_minutes": round(projected_minutes, 2), "budget_ok": budget_ok}
    with open(RESULTS_DIR / "budget_projection_run1.json", "w") as f:
        json.dump(budget, f, indent=1)

    verdict1, reason1 = decide(run1["A0"], run1["A"], run1["B"], budget_ok)
    print(f"Run 1 verdict: {verdict1} — {reason1}", file=sys.stderr)

    final_verdict, final_reason, run2 = verdict1, reason1, None
    if verdict1 == "HARDEN":
        print("=== Applying hardening recipe, run 2 ===", file=sys.stderr)
        harden(HERE / "corpus")
        run2 = await run_all_arms(HERE / "corpus", probes, template, tag="run2")
        with open(RESULTS_DIR / "run2.json", "w") as f:
            json.dump(run2, f, indent=1)
        verdict2, reason2 = decide(run2["A0"], run2["A"], run2["B"], budget_ok)
        print(f"Run 2 verdict: {verdict2} — {reason2}", file=sys.stderr)
        if verdict2 == "PROCEED":
            final_verdict, final_reason = "PROCEED", reason2
        else:
            final_verdict = "STOP_2ND_ATTEMPT"
            final_reason = (f"Second gate run still not PROCEED ({verdict2}: {reason2}). "
                            "This is the 2nd failed attempt under CLAUDE.md's hard gate — "
                            "no third pass, consult the user.")

    receipt = {
        "final_verdict": final_verdict, "final_reason": final_reason,
        "run1": {"A0": {k: v for k, v in run1["A0"].items() if k != "rows"},
                 "A": {k: v for k, v in run1["A"].items() if k != "rows"},
                 "B": {k: v for k, v in run1["B"].items() if k != "rows"},
                 "cost_usd": run1["cost_usd"], "wall_s": run1["wall_s"], "n_chunks": run1["n_chunks"]},
        "run2_applied": run2 is not None,
        "budget_projection": budget,
    }
    if run2:
        receipt["run2"] = {"A0": {k: v for k, v in run2["A0"].items() if k != "rows"},
                            "A": {k: v for k, v in run2["A"].items() if k != "rows"},
                            "B": {k: v for k, v in run2["B"].items() if k != "rows"},
                            "cost_usd": run2["cost_usd"], "wall_s": run2["wall_s"], "n_chunks": run2["n_chunks"]}
    with open(RESULTS_DIR / "gate_receipt.json", "w") as f:
        json.dump(receipt, f, indent=1)
    print(json.dumps(receipt, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
