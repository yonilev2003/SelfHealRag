#!/usr/bin/env python3
"""Phase 2 (PLAN.md rev 4): freeze the dev/test split. Run ONCE, before any
retriever/verifier/tuner code exists (temporal discipline, invariant #2).

Exact partition (PLAN.md rev 4, realized against the actual 40 probes
generate_corpus.py/generate_probes.py built): atomic 5/3, contradiction
7/5 (3 implicit + the 3-hop chain + 1 explicit forced into test), near_dup
5/3, multi_hop 2/2 (the 3-hop forced into test), memory_correction 5/3.
= 24 dev / 16 test.

Structural novelty (invariant #3): the implicit-supersession probes, the
3-hop chain (both contradiction's and multi_hop's), and the entire
memory_correction category are trap subtypes/mechanisms a system could only
have seen in dev if the SAME entity happened to land there -- since every
probe here targets a distinct entity (no paraphrase-pairs), every test
case is, by construction, an entity the tuning loop never touched in dev.
This is a stronger form of held-out novelty than paraphrase-only splits
would give, noted honestly here since PLAN.md's exact "reworded in test"
language doesn't literally apply to a design with 1 probe/entity.
"""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PROBES_DIR = REPO / "data" / "probes"
SCRATCH_ALL_PROBES = Path(
    "/tmp/claude-0/-home-user-hackathonaug28-08-26/0a84ed52-68de-563b-a9ee-13411cba2061/scratchpad/all_probes.json"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    probes = json.loads(SCRATCH_ALL_PROBES.read_text())
    assert len(probes) == 40

    by_cat = {}
    for p in probes:
        by_cat.setdefault(p["category"], []).append(p)
    for cat in by_cat:
        by_cat[cat].sort(key=lambda p: p["probe_id"])  # deterministic order

    dev, test = [], []

    def split_cat(cat, n_test, force_test_predicate=None):
        items = by_cat[cat]
        forced = [p for p in items if force_test_predicate and force_test_predicate(p)]
        rest = [p for p in items if p not in forced]
        n_more = n_test - len(forced)
        assert n_more >= 0, f"{cat}: forced ({len(forced)}) exceeds n_test ({n_test})"
        test_items = forced + rest[:n_more]
        dev_items = rest[n_more:]
        test.extend(test_items)
        dev.extend(dev_items)

    split_cat("atomic", 3)
    split_cat("contradiction", 5,
              force_test_predicate=lambda p: p["trap_subtype"] in ("implicit_supersession", "3hop_chain"))
    split_cat("near_dup", 3)
    split_cat("multi_hop", 2, force_test_predicate=lambda p: p["trap_subtype"] == "3hop")
    split_cat("memory_correction", 3)

    dev_ids, test_ids = {p["probe_id"] for p in dev}, {p["probe_id"] for p in test}
    assert dev_ids.isdisjoint(test_ids), "dev/test overlap!"
    assert dev_ids | test_ids == {p["probe_id"] for p in probes}, "dev/test doesn't cover all probes!"
    assert len(dev) == 24 and len(test) == 16, f"got dev={len(dev)} test={len(test)}, expected 24/16"

    PROBES_DIR.mkdir(parents=True, exist_ok=True)
    dev_sorted = sorted(dev, key=lambda p: p["probe_id"])
    test_sorted = sorted(test, key=lambda p: p["probe_id"])
    (PROBES_DIR / "dev_split.json").write_text(json.dumps(dev_sorted, indent=1))
    (PROBES_DIR / "test_split.locked.json").write_text(json.dumps(test_sorted, indent=1))

    dev_hash = sha256_file(PROBES_DIR / "dev_split.json")
    test_hash = sha256_file(PROBES_DIR / "test_split.locked.json")
    (PROBES_DIR / "dev_split.sha256").write_text(dev_hash + "\n")
    (PROBES_DIR / "test_split.locked.sha256").write_text(test_hash + "\n")
    registry_hash = sha256_file(REPO / "data" / "fact_registry.json")

    by_cat_counts = {"dev": {}, "test": {}}
    for p in dev_sorted:
        by_cat_counts["dev"][p["category"]] = by_cat_counts["dev"].get(p["category"], 0) + 1
    for p in test_sorted:
        by_cat_counts["test"][p["category"]] = by_cat_counts["test"].get(p["category"], 0) + 1

    summary = {
        "n_dev": len(dev), "n_test": len(test),
        "dev_split_sha256": dev_hash, "test_split_locked_sha256": test_hash,
        "fact_registry_sha256": registry_hash,
        "by_category": by_cat_counts,
        "test_trap_subtypes": sorted({p["trap_subtype"] for p in test_sorted}),
        "hero_case_probe_id": next(p["probe_id"] for p in test_sorted
                                   if p["entity_key"] == "eng.oncall_stipend_usd"),
    }
    (HERE / "split_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    main()
