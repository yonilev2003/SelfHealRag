#!/usr/bin/env bash
set -euo pipefail
# Copies this project's Claude Code session logs into trajectories/raw for
# disclosure. Claude Code stores every session (interactive or headless) under
# ~/.claude/projects/<cwd-with-slashes-as-dashes>/<session-id>.jsonl — this is
# an internal, undocumented format, so we copy it as-is rather than reparsing it.
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENCODED="$(echo "$PROJECT_DIR" | sed 's/\//-/g')"
SRC="$HOME/.claude/projects/$ENCODED"
DEST="$(dirname "$0")/../trajectories/raw"
mkdir -p "$DEST"

if [ -d "$SRC" ]; then
  cp "$SRC"/*.jsonl "$DEST"/ 2>/dev/null && echo "Copied session logs from $SRC to $DEST" \
    || echo "No .jsonl session files found yet in $SRC"
else
  echo "No Claude Code project dir found at $SRC — check the encoded path matches your cwd."
fi

# If any part of the run was scripted/headless instead of interactive, capture
# those separately with:
#   claude -p "<prompt>" --output-format stream-json --verbose > trajectories/run.jsonl
