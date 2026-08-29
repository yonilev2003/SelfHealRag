"""Arm B: generalist agent, Read/Grep/Glob only (no Bash -- this corpus-QA
task needs no code execution; the live Phase-1 finding that allowed_tools
alone doesn't block Bash means disallowed_tools is the real enforcement,
see PROCESS.md), running in a tempdir containing ONLY a copy of
data/corpus/*.md, guarded by the PreToolUse path-containment hook
(eval/sandbox_guard.py). max_turns=25, 8-min timeout; a cap hit is scored
as-is (whatever the agent's last JSON attempt was, if any) and noted, not
silently discarded.
"""

import asyncio
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
from llm_call import MODEL, extract_json, to_jsonable  # noqa: E402
from sandbox_guard import make_guard_hook  # noqa: E402

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, HookMatcher, ResultMessage, TextBlock, query  # noqa: E402

MAX_TURNS = 25
TIMEOUT_S = 480

PROMPT_TEMPLATE = """You are answering a factual question about Acme Corp company policy. The
current directory contains the company's policy documents as markdown
files, each with chunk_id / entity_key / effective_date headers. Company
policies are sometimes revised, and some questions require combining two
or three separate excerpts (e.g. a base amount plus a bonus) -- read enough
of the corpus to find every excerpt relevant to this question, and identify
the CURRENT (most recent, non-superseded) value(s) before answering.

Question: {question}

Respond with ONLY this JSON object as your final message, no other text
before or after it:
{{"value": "<the current value, as a bare number or short phrase with no units>", "chunk_id": "<id(s) of the excerpt(s) that support this, joined with '+' if more than one>"}}
"""


async def run_case(corpus_dir: Path, question: str, traj_path: Path = None) -> dict:
    work = Path(tempfile.mkdtemp(prefix="selfheal-armb-"))
    for f in corpus_dir.glob("*.md"):
        shutil.copy(f, work / f.name)
    root = str(work.resolve())
    denied = []
    options = ClaudeAgentOptions(
        model=MODEL, cwd=root, allowed_tools=["Read", "Grep", "Glob"],
        disallowed_tools=["Bash", "Write", "Edit", "MultiEdit", "NotebookEdit",
                          "WebFetch", "WebSearch", "Task", "ToolSearch"],
        hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[make_guard_hook(root, denied)])]},
        max_turns=MAX_TURNS, setting_sources=[], mcp_servers={}, strict_mcp_config=True,
    )
    prompt = PROMPT_TEMPLATE.format(question=question)
    messages, final_text, meta = [], "", {}
    t0 = time.time()

    async def _consume():
        async for msg in query(prompt=prompt, options=options):
            messages.append(to_jsonable(msg))

    try:
        await asyncio.wait_for(_consume(), timeout=TIMEOUT_S)
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
            meta["num_turns"] = m.get("num_turns")
            if m.get("result"):
                final_text = m["result"]

    if traj_path:
        traj_path.parent.mkdir(parents=True, exist_ok=True)
        with open(traj_path, "w") as f:
            for m in messages:
                f.write(json.dumps(m) + "\n")
    shutil.rmtree(work, ignore_errors=True)

    hit_cap = meta.get("timed_out") or (meta.get("num_turns") or 0) >= MAX_TURNS
    return {"wall_s": round(time.time() - t0, 2), "predicted": extract_json(final_text or ""),
            "denied_tool_calls": denied, "cap_hit": bool(hit_cap), **meta}
