"""Real preventive filesystem-containment control for any Read/Grep/Bash-
capable agent arm (PLAN.md invariant #1's Arm-B sandbox).

`cwd` alone is a starting directory, not a boundary — an SDK `can_use_tool`
callback is also insufficient: `allowed_tools` entries that allow a whole
tool auto-approve before that callback is even consulted (confirmed via the
SDK's own `CanUseToolShadowedWarning`). A `PreToolUse` hook runs before every
tool call regardless of `allowed_tools` and can outright deny it — that is
the actual enforcement point.

This resolves the tool's path-like argument (`file_path`/`path`/`pattern`)
against `root` with `os.path.realpath` (following `..` and symlinks) and
denies anything that resolves outside `root`. Deliberately conservative: any
key it doesn't recognize as a path is left unchecked, so pair this with a
narrow `allowed_tools` list (no Bash — a corpus-QA task needs no code
execution) rather than relying on this hook alone as defense against an
arbitrary shell.
"""

import os


def make_guard_hook(root: str, denied_log: list):
    root = os.path.realpath(root)

    async def guard_path_hook(input_data, tool_use_id, context):
        tool_input = input_data.get("tool_input", {})
        for key in ("file_path", "path", "pattern"):
            value = tool_input.get(key)
            if not isinstance(value, str):
                continue
            resolved = os.path.realpath(value if os.path.isabs(value) else os.path.join(root, value))
            if not (resolved == root or resolved.startswith(root + os.sep)):
                denied_log.append({"tool": input_data.get("tool_name"), "arg": value, "resolved": resolved})
                return {"hookSpecificOutput": {
                    "hookEventName": "PreToolUse", "permissionDecision": "deny",
                    "permissionDecisionReason": f"path {resolved} resolves outside sandbox root {root}",
                }}
        return {}

    return guard_path_hook
