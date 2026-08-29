"""Shared headless-call helpers for every arm (baselines + advanced). One
copy so trajectory capture, JSON extraction, and single-call options are
byte-identical everywhere they're used.
"""

import json
import re
import time
from pathlib import Path

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

MODEL = "claude-sonnet-5"


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


async def run_single_call(prompt: str, traj_path: Path = None, max_tokens: int = None):
    """One-shot, no tools, temperature-0-equivalent (claude -p has no
    temperature knob; determinism comes from max_turns=1 + a fully
    specified prompt). Used by A0/A/A2's generation steps and by
    advanced/generator.py."""
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
    if traj_path:
        traj_path.parent.mkdir(parents=True, exist_ok=True)
        with open(traj_path, "w") as f:
            for m in messages:
                f.write(json.dumps(m) + "\n")
    return {"wall_s": round(time.time() - t0, 2), "predicted": extract_json(final_text or ""), **meta}
