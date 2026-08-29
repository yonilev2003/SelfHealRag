#!/usr/bin/env python3
"""Hard budget gate (invariant #6): reads results/*_test.json + *_dev.json
receipts (via the CSVs' cost isn't tracked there, so this reads the JSON
result files' total_cost_usd/wall_s directly), sums across all runs found,
and hard-fails (non-zero exit) if the total exceeds the kickoff-doc-derived
ceiling: 40 API-minutes, $15.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO / "results"
MAX_MINUTES = 40
MAX_USD = 15


def main():
    total_cost, total_wall = 0.0, 0.0
    files_checked = []
    for f in RESULTS_DIR.glob("*.json"):
        if f.name in ("dev_cache.json",):
            continue
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        for v in data.values():
            if isinstance(v, dict) and "total_cost_usd" in v:
                total_cost += v.get("total_cost_usd") or 0
                total_wall += v.get("wall_s") or 0
        files_checked.append(f.name)

    total_minutes = total_wall / 60
    ok = total_cost < MAX_USD and total_minutes < MAX_MINUTES
    print(json.dumps({"files_checked": files_checked, "total_cost_usd": round(total_cost, 2),
                      "total_minutes": round(total_minutes, 2), "max_usd": MAX_USD,
                      "max_minutes": MAX_MINUTES, "budget_ok": ok}, indent=1))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
