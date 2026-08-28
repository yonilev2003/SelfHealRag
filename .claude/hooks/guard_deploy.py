#!/usr/bin/env python3
"""PreToolUse hook: ask for confirmation before anything that deploys, publishes,
or ships. Everything else passes through untouched — one precise gate, not
friction everywhere. Wired to the Bash matcher only, in .claude/settings.json.

Uses Claude Code's structured hookSpecificOutput / permissionDecision mechanism:
"ask" pauses for human confirmation in the UI; printing nothing + exit 0 leaves
the normal permission flow untouched for everything else.

Matching is token-aware (via shlex) rather than a substring search over the
raw command text, so a trigger word only counts when it's actually an
invoked command/subcommand -- not when it's part of a filename, directory,
branch name, --flag value, or quoted text (a commit message, a grep target).
"""
import json
import re
import shlex
import sys

# Words that only count as a real invocation when they appear as their own
# shell token (e.g. `npm run deploy`), not as a substring of RELEASE.md,
# src/deploy, --grep=release, or inside a quoted commit message.
BARE_WORD_TRIGGERS = {"deploy", "publish", "release"}

# Multi-token command invocations, matched as consecutive tokens within a
# single pipeline segment (so `docker push` doesn't fire on an unrelated
# `docker` ... `push-notes.sh` pairing, etc).
TOKEN_SEQUENCE_PATTERNS = [
    ["git", "push"],
    ["docker", "push"],
    ["docker-compose", "push"],
    ["docker", "compose", "push"],
    ["kubectl", "apply"],
    ["kubectl", "create"],
    ["kubectl", "rollout"],
    ["kubectl", "set", "image"],
    ["terraform", "apply"],
    ["railway", "up"],
    ["npm", "publish"],
    ["twine", "upload"],
    ["gh", "release", "create"],
    ["pulumi", "up"],
    ["aws", "s3", "sync"],
]

SHELL_OPERATORS = {"&&", "||", ";", "|"}

# Checks that need a wildcard/substring match (flags, remote targets) rather
# than fixed adjacent tokens. Applied to the command with quoted, multi-word
# string arguments blanked out, so quoted text (commit messages, grep
# targets, etc.) can't trigger them.
WILDCARD_PATTERNS = [
    r"\bvercel\b.*--prod",
    r"\brsync\b.*(prod|production)",
    r"\brsync\b.*\S+@[\w.-]+:",  # rsync to a remote user@host target
    r"\bcurl\b.*api\.github\.com.*/releases",  # release via raw API, not gh CLI
]


def _tokenize(command):
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()  # unbalanced quotes etc. -- best effort


def _segments(tokens):
    """Split tokens into pipeline segments on shell operators, so argv[0]
    checks (e.g. heroku) look at what's actually being invoked."""
    segments = [[]]
    for t in tokens:
        if t in SHELL_OPERATORS:
            segments.append([])
        else:
            segments[-1].append(t)
    return [s for s in segments if s]


def _blank_quoted(command, tokens):
    """Reconstruct the command with quoted multi-word arguments replaced by a
    placeholder, so wildcard regexes can't match words that only appear
    inside a commit message, grep target, etc."""
    return " ".join("QUOTED_ARG" if " " in t else t for t in tokens)


def _matches(command):
    tokens = _tokenize(command)
    lower_tokens = [t.lower() for t in tokens]

    if any(t in BARE_WORD_TRIGGERS for t in lower_tokens):
        return True

    for seg in _segments(lower_tokens):
        if seg[0] == "heroku":
            return True
        for seq in TOKEN_SEQUENCE_PATTERNS:
            n = len(seq)
            for i in range(len(seg) - n + 1):
                if seg[i:i + n] == seq:
                    return True

    sanitized = _blank_quoted(command, tokens)
    return any(re.search(p, sanitized, re.IGNORECASE) for p in WILDCARD_PATTERNS)


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # can't parse it -> don't block on a guess

    command = payload.get("tool_input", {}).get("command", "")
    if _matches(command):
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
