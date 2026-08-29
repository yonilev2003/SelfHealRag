#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Runs the Phase-4 self-improvement dev loop (if advanced/final_config.json
# doesn't exist yet), then Arm C (SelfHeal RAG, final tuned config) over the
# frozen test split. Requires ANTHROPIC_API_KEY.
: "${ANTHROPIC_API_KEY:?Set ANTHROPIC_API_KEY before running the advanced solution (see README)}"

if [ ! -f advanced/final_config.json ]; then
  echo "=== Phase 4: self-improvement dev loop ==="
  python3 advanced/build_index.py
  python3 advanced/tuner.py
fi

echo "=== Arm C (test split, final tuned config) ==="
python3 eval/run_eval.py --arm C --split test
