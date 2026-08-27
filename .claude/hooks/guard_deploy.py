#!/usr/bin/env python3
"""PreToolUse hook: ask for confirmation before anything that deploys, publishes,
or ships. Everything else passes through untouched — one precise gate, not
friction everywhere. Wired to the Bash matcher only, in .claude/settings.json.

Uses Claude Code's structured hookSpecificOutput / permissionDecision mechanism:
"ask" pauses for human confirmation in the UI; printing nothing + exit 0 leaves
the normal permission flow untouched for everything else.
"""
import json
import re
import sys

DEPLOY_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bdeploy\b",
    r"\bpublish\b",
    r"\brelease\b",
    r"\bdocker\s+push\b",
    r"\bkubectl\s+(apply|create)\b",
    r"\bterraform\s+apply\b",
    r"\bvercel\b.*--prod",
    r"\brailway\s+up\b",
    r"\bheroku\b",
    r"\bnpm\s+publish\b",
    r"\btwine\s+upload\b",
    r"\bgh\s+release\s+create\b",
    r"\brsync\b.*(prod|production)",
]


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # can't parse it -> don't block on a guess

    command = payload.get("tool_input", {}).get("command", "")
    if any(re.search(pattern, command, re.IGNORECASE) for pattern in DEPLOY_PATTERNS):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    f"Looks like a deploy/publish step: `{command}`. "
                    "Confirm before it runs."
                ),
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
