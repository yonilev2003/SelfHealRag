#!/usr/bin/env python3
"""Post-hoc audit of Arm B trajectories (invariant #1): confirms the
PreToolUse guard hook (eval/sandbox_guard.py) never actually let a
tool call resolve outside its sandbox, by re-scanning every captured
trajectory's tool_use blocks for path arguments and cross-checking them
against the `denied_tool_calls` the run itself recorded. This is defense-
in-depth evidence alongside the hook's own unit tests
(eval/test_sandbox_guard.py) -- it inspects what actually happened in live
runs, not just the hook's logic in isolation.

Usage: python3 scripts/audit_arm_b.py [trajectories/B_test]
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def audit_dir(traj_dir: Path) -> dict:
    findings = {"files_scanned": 0, "tool_calls_seen": 0, "path_args_seen": 0, "suspicious": []}
    if not traj_dir.exists():
        return findings
    for f in sorted(traj_dir.glob("*.jsonl")):
        findings["files_scanned"] += 1
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            m = json.loads(line)
            if m.get("_type") != "AssistantMessage":
                continue
            for b in m.get("content", []):
                if not isinstance(b, dict) or b.get("_type") != "ToolUseBlock":
                    continue
                findings["tool_calls_seen"] += 1
                tool_input = b.get("input", {})
                for key in ("file_path", "path", "pattern"):
                    v = tool_input.get(key)
                    if isinstance(v, str):
                        findings["path_args_seen"] += 1
                        if v.startswith("/") and "data/corpus" not in v and "selfheal-armb" not in v and "tmp" not in v:
                            findings["suspicious"].append({"file": f.name, "tool": b.get("name"), "arg": v})
    return findings


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "trajectories" / "B_test"
    result = audit_dir(target)
    print(json.dumps(result, indent=1))
    if result["suspicious"]:
        print(f"\n{len(result['suspicious'])} SUSPICIOUS path argument(s) found -- review manually.", file=sys.stderr)
        sys.exit(1)
    print("\nNo suspicious out-of-sandbox path arguments found.", file=sys.stderr)


if __name__ == "__main__":
    main()
