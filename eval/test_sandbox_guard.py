"""Unit tests for eval/sandbox_guard.py — the real preventive control behind
the Arm-B sandbox (PLAN.md invariant #1). Run: python3 -m pytest eval/ -q
or: python3 eval/test_sandbox_guard.py

Verified live against a real claude-sonnet-5 agent session too (not just
these unit cases): with this hook wired as a PreToolUse hook and
allowed_tools=["Read","Grep","Glob"] (no Bash), the agent's own attempt to
read a path outside the sandbox root was refused before any tool executed.
These cases pin the mechanical boundary independent of model behavior.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sandbox_guard import make_guard_hook  # noqa: E402


def run(coro):
    return asyncio.run(coro)


def test_all_cases():
    tmp = Path(tempfile.mkdtemp(prefix="guard-test-"))
    (tmp / "allowed.txt").write_text("inside")
    (tmp.parent / "outside_secret.txt").write_text("outside")

    denied = []
    hook = make_guard_hook(str(tmp), denied)

    cases = [
        ("Read", {"file_path": str(tmp / "allowed.txt")}, "allow"),
        ("Read", {"file_path": "allowed.txt"}, "allow"),
        ("Read", {"file_path": "../outside_secret.txt"}, "deny"),
        ("Read", {"file_path": str(tmp.parent / "outside_secret.txt")}, "deny"),
        ("Grep", {"pattern": "secret", "path": ".."}, "deny"),
        ("Read", {"file_path": str(tmp / "subdir" / ".." / ".." / "outside_secret.txt")}, "deny"),
        ("Glob", {"pattern": "*.md"}, "allow"),  # no path key -> unchecked, allowed
    ]
    failures = []
    for tool, inp, expected in cases:
        out = run(hook({"tool_name": tool, "tool_input": inp}, "id", None))
        got = out.get("hookSpecificOutput", {}).get("permissionDecision", "allow")
        if got != expected:
            failures.append(f"{tool} {inp}: expected {expected}, got {got}")

    assert not failures, "\n".join(failures)
    assert len(denied) == 4, f"expected 4 denials logged, got {len(denied)}: {denied}"
    print(f"PASS: {len(cases)}/{len(cases)} guard-hook cases correct, {len(denied)} denials logged")


if __name__ == "__main__":
    test_all_cases()
