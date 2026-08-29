#!/usr/bin/env python3
"""Focused pretest of the UNTESTED, categorically-unfakeable mechanism:
cross-session memory persistence. Not a 3rd attempt at the QA-accuracy
hypothesis both prior gates already killed (that hard gate stands) -- this
tests a structurally different claim the two prior pretests never touched:
information that exists ONLY as a prior session's diagnosed correction,
never in the corpus itself, is categorically inaccessible to any single-shot
call over the corpus alone, no matter how capable the model is. That's not
a "maybe Sonnet is strong enough" confound -- it's a hard information-
theoretic gap.

Setup: the corpus (as shipped) states the Eng on-call stipend is $200. In
reality (simulating a real SMB's actual condition) that figure is stale --
finance approved a raise to $250 via a support ticket that never made it
into the handbook doc. This is realistic corpus staleness, not a rigged
trick question.

Three short, independent (fresh-context) calls:
  1. Session 1 -- corpus only, no memory. Expected: answers $200 (the
     documented, but now-wrong, value) -- this is a CORRECT reading of the
     corpus, just wrong versus outside ground truth. Establishes the
     baseline blind spot.
  2. Session 2, WITH memory -- a fresh call (no shared transcript with
     session 1) given the corpus PLUS a short persisted correction note.
     Expected: answers $250 -- correct ONLY because of the note, since nothing
     in the corpus itself says $250.
  3. Session 2 control, WITHOUT memory -- fresh call, same corpus, no note.
     Expected: answers $200 again, matching session 1 -- proves the memory
     file (not randomness, not a different prompt) is what closes the gap.
"""

import asyncio
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS_DIR = REPO / "results" / "pretest-selfheal"
TRAJ_DIR = REPO / "trajectories" / "pretest-selfheal" / "memory_experiment"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "eval"))
from run_gate import load_corpus, render_chunk, run_single_call  # noqa: E402
from match import values_match  # noqa: E402

QUESTION = "What is the current weekly on-call stipend for engineers, in USD?"
TRUE_CURRENT_VALUE = "250"  # ground truth per the out-of-band correction, NOT in the corpus
STALE_DOCUMENTED_VALUE = "200"  # what the shipped corpus actually says

MEMORY_NOTE = (
    "MEMORY NOTE (persisted correction from a prior session, not present in "
    "the corpus itself): Per support ticket #4521 (2026-07-01), Finance "
    "approved raising the Engineering on-call stipend from $200 to $250/week. "
    "The employee handbook document has not yet been updated to reflect this "
    "change -- treat $250 as the current value for entity_key "
    "eng.oncall_stipend_usd, overriding the stale $200 figure in the corpus."
)

PROMPT_TEMPLATE = """You are answering a factual question about Acme Corp company policy using the
provided document excerpts{memory_clause}.

Question: {question}

Document excerpts:
{excerpts}
{memory_block}
Respond with ONLY this JSON object, no other text before or after it:
{{"value": "<the current value, as a bare number, no units>", "chunk_id": "<id of the excerpt that supports this, or \\"MEMORY\\" if the memory note is what determines the current value>"}}
"""


async def run_session(label: str, chunks: dict, memory_note: str | None):
    excerpts = "\n\n".join(render_chunk(cid, c) for cid, c in chunks.items()
                           if c["entity_key"] == "eng.oncall_stipend_usd")
    memory_clause = ", plus a persisted memory note from a prior session (if any)" if memory_note else ""
    memory_block = f"\nPersisted memory note:\n{memory_note}\n" if memory_note else ""
    prompt = PROMPT_TEMPLATE.format(question=QUESTION, excerpts=excerpts,
                                    memory_clause=memory_clause, memory_block=memory_block)
    res = await run_single_call(prompt, TRAJ_DIR / f"{label}.jsonl")
    return res


async def main():
    chunks = load_corpus(HERE / "corpus")

    print("=== Session 1: corpus only, no memory (fresh context) ===", file=sys.stderr)
    s1 = await run_session("session1_no_memory", chunks, memory_note=None)

    print("=== Session 2: FRESH context, corpus + memory note ===", file=sys.stderr)
    s2_with_memory = await run_session("session2_with_memory", chunks, memory_note=MEMORY_NOTE)

    print("=== Session 2 control: FRESH context, corpus only (no memory) ===", file=sys.stderr)
    s2_control = await run_session("session2_control_no_memory", chunks, memory_note=None)

    def val(s):
        return (s.get("predicted") or {}).get("value")

    result = {
        "question": QUESTION,
        "true_current_value": TRUE_CURRENT_VALUE,
        "stale_documented_value": STALE_DOCUMENTED_VALUE,
        "session1_no_memory": {"predicted_value": val(s1), "matches_stale": values_match(val(s1) or "", STALE_DOCUMENTED_VALUE),
                               "cost_usd": s1.get("total_cost_usd"), "raw": s1},
        "session2_with_memory": {"predicted_value": val(s2_with_memory),
                                 "matches_true_current": values_match(val(s2_with_memory) or "", TRUE_CURRENT_VALUE),
                                 "cost_usd": s2_with_memory.get("total_cost_usd"), "raw": s2_with_memory},
        "session2_control_no_memory": {"predicted_value": val(s2_control),
                                       "matches_stale": values_match(val(s2_control) or "", STALE_DOCUMENTED_VALUE),
                                       "cost_usd": s2_control.get("total_cost_usd"), "raw": s2_control},
    }
    categorical_gap_demonstrated = (
        result["session1_no_memory"]["matches_stale"]
        and result["session2_with_memory"]["matches_true_current"]
        and result["session2_control_no_memory"]["matches_stale"]
    )
    result["categorical_gap_demonstrated"] = categorical_gap_demonstrated

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "memory_experiment.json", "w") as f:
        json.dump(result, f, indent=1)

    print(json.dumps({k: v for k, v in result.items() if k not in
                      ("session1_no_memory", "session2_with_memory", "session2_control_no_memory")} |
                     {k: {kk: vv for kk, vv in v.items() if kk != "raw"}
                      for k, v in result.items() if isinstance(v, dict)}, indent=1))
    print(f"\nCATEGORICAL GAP DEMONSTRATED: {categorical_gap_demonstrated}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
