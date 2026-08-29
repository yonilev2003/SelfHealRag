#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Runs the four fair baselines (A0/A/A2/B) over the frozen test split.
# Requires ANTHROPIC_API_KEY. Each arm's results land in results/<arm>_test.json
# and a per-case results/<arm>_test.csv; a receipt is appended to
# results/test_run_log.md on every invocation (invariant #8).
: "${ANTHROPIC_API_KEY:?Set ANTHROPIC_API_KEY before running the baseline (see README)}"

for ARM in A0 A A2 B; do
  echo "=== Arm $ARM (test split) ==="
  python3 eval/run_eval.py --arm "$ARM" --split test
done
