#!/usr/bin/env bash
set -euo pipefail

# Local dev: load ANTHROPIC_API_KEY from .env if present (gitignored; see
# .env.example). In CI the equivalent comes in as a GitHub Actions secret,
# already present in the environment -- no .env needed there.
if [ -f .env ]; then set -a; source .env; set +a; fi

echo "Installing Python dependencies (rank_bm25, claude-agent-sdk)..."
pip install --quiet rank_bm25 claude-agent-sdk

echo "Setup complete. Python: $(python3 --version). rank_bm25 + claude-agent-sdk installed."
echo "Note: make baseline / make advanced / make eval require ANTHROPIC_API_KEY."
