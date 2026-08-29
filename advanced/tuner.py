"""Phase 4 self-improvement dev loop (PLAN.md). Round protocol: clean
24-case dev run (cache-aware) -> classify -> plurality category -> mapped
action -> KEEP iff dev accuracy improves by >=2 cases, else revert (logged).
Memory writes are KEPT unconditionally (confirmed against a real signal,
never reverted even if the round's other knob change is). Stop: 2
consecutive no-improvement rounds or 8 rounds.

Scope note (disclosed, not silent): the glossary-entry and query-rewrite-
rule actions described in PLAN.md's action mapping are cut for this build
(pre-agreed cut-order item) -- retrieval_miss's mapped action here is
limited to the k-bump ladder {5,7,10}. If retrieval_miss recurs after k=10
is exhausted, it counts as no-improvement per the "exhausted actions" rule,
same as the full mapping would specify.
"""

import asyncio
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "advanced"))
sys.path.insert(0, str(REPO / "eval"))
from build_index import load_corpus  # noqa: E402
from verifier import load_entity_index  # noqa: E402
from run_case import run_case  # noqa: E402
from diagnose import diagnose_round, find_correction_signals  # noqa: E402
from llm_call import run_single_call  # noqa: E402
from match import values_match  # noqa: E402

MEMORY_PATH = REPO / "advanced" / "memory.json"
AUDIT_MEMORY_PATH = REPO / "advanced" / "audit_memory.json"
CHANGELOG_PATH = REPO / "advanced" / "selfheal_changelog.md"
CACHE_PATH = REPO / "results" / "dev_cache.json"
SIGNAL_EXTRACTOR_TEMPLATE = (REPO / "prompts" / "signal_extractor.md").read_text()

DEFAULT_CONFIG = {"k": 3, "hybrid_date_boost": False, "use_verifier": False, "use_memory": True}
K_LADDER = [5, 7, 10]
MAX_ROUNDS = 8
STOP_AFTER_NO_IMPROVEMENT = 2


def config_hash(config: dict) -> str:
    key = json.dumps({**config, "memory_version": _memory_version()}, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _memory_version() -> int:
    if MEMORY_PATH.exists():
        return len(json.loads(MEMORY_PATH.read_text()))
    return 0


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache: dict):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=1))


async def run_dev_round(chunks: dict, entity_index: dict, dev_split: list, config: dict, cache: dict) -> dict:
    ch = config_hash(config)
    results = {}
    for probe in dev_split:
        cache_key = f"{probe['probe_id']}::{ch}"
        if cache_key in cache:
            results[probe["probe_id"]] = cache[cache_key]
            continue
        res = await run_case(chunks, probe["question"], entity_index=entity_index, k=config["k"],
                             hybrid_date_boost=config["hybrid_date_boost"],
                             use_verifier=config["use_verifier"], use_memory=config["use_memory"])
        results[probe["probe_id"]] = res
        cache[cache_key] = res
    save_cache(cache)
    return results


async def apply_memory_action(case_ids: list, dev_split_by_id: dict, changelog_lines: list) -> int:
    """Consults correction_signals.json for each failing memory_correction
    case's entity_key; extracts + persists a correction for each match.
    Returns the number of new memory entries written."""
    entity_keys = [dev_split_by_id[cid]["entity_key"] for cid in case_ids]
    matches = find_correction_signals(entity_keys)
    memory = json.loads(MEMORY_PATH.read_text()) if MEMORY_PATH.exists() else {}
    n_new = 0
    for entity_key, signal in matches.items():
        if entity_key in memory:
            continue
        prompt = SIGNAL_EXTRACTOR_TEMPLATE.format(entity_key=entity_key, signal_text=signal["text"])
        res = await run_single_call(prompt)
        extracted = (res.get("predicted") or {}).get("value")
        if extracted is None:
            continue
        memory[entity_key] = {"value": extracted, "source_signal_id": signal["signal_id"],
                              "round_added": len(changelog_lines)}
        motivating = [cid for cid in case_ids if dev_split_by_id[cid]["entity_key"] == entity_key]
        changelog_lines.append(
            f"  - Wrote memory correction for `{entity_key}` = {extracted!r} "
            f"(source: {signal['signal_id']}), motivated by dev case(s) {motivating}."
        )
        n_new += 1
    MEMORY_PATH.write_text(json.dumps(memory, indent=1))
    return n_new


def next_k(current_k: int, tried_k: set) -> int | None:
    """Next untried rung of the ladder, regardless of whether earlier
    attempts were kept or reverted -- a reverted k=5 must not be retried
    forever; the ladder should advance to k=7 next. Returns None once
    every rung {5,7,10} has been tried."""
    for k in K_LADDER:
        if k not in tried_k and k != current_k:
            return k
    return None


async def main():
    if not MEMORY_PATH.exists():
        MEMORY_PATH.write_text("{}")
    chunks = load_corpus()
    entity_index = load_entity_index()
    dev_split = json.loads((REPO / "data" / "probes" / "dev_split.json").read_text())
    dev_split_by_id = {p["probe_id"]: p for p in dev_split}
    cache = load_cache()

    config = dict(DEFAULT_CONFIG)
    audit_memory = []
    changelog = ["# SelfHeal RAG — self-improvement changelog (written by the loop itself)\n"]
    tried_hybrid, tried_verifier_for, tried_k = False, set(), {DEFAULT_CONFIG["k"]}
    no_improve_streak = 0
    round_num = 0

    results = await run_dev_round(chunks, entity_index, dev_split, config, cache)
    diag = diagnose_round(dev_split, results)
    best_accuracy = diag["n_correct"]
    changelog.append(f"## Round 0 (baseline config {config})\n- accuracy: {best_accuracy}/{diag['n_total']}\n"
                     f"- failures by category: {diag['failure_counts_by_taxonomy']}\n")
    audit_memory.append({"round": 0, "config": dict(config), "dev_accuracy": best_accuracy,
                         "failure_counts_by_taxonomy": diag["failure_counts_by_taxonomy"],
                         "case_ids_by_taxonomy": diag["case_ids_by_taxonomy"], "kept": True})

    while round_num < MAX_ROUNDS and no_improve_streak < STOP_AFTER_NO_IMPROVEMENT:
        round_num += 1
        plurality = diag["plurality_category"]
        if plurality is None:
            changelog.append(f"## Round {round_num}\n- no failures remain; stopping.\n")
            break

        case_ids = diag["case_ids_by_taxonomy"][plurality]
        trial_config = dict(config)
        action_desc = ""
        memory_written = 0

        if plurality == "memory_correction_missed":
            memory_written = await apply_memory_action(case_ids, dev_split_by_id, changelog)
            action_desc = f"consulted the correction-signal feed for {len(case_ids)} case(s), wrote {memory_written} new memory entries"
        elif plurality == "retrieval_miss":
            nk = next_k(config["k"], tried_k)
            if nk is None:
                changelog.append(f"## Round {round_num}\n- plurality={plurality} but k-ladder exhausted; no-improvement.\n")
                no_improve_streak += 1
                continue
            tried_k.add(nk)
            trial_config["k"] = nk
            action_desc = f"k {config['k']} -> {nk}"
        elif plurality in ("stale_value_uncaught", "hallucinated_citation"):
            if not config["use_verifier"]:
                trial_config["use_verifier"] = True
                action_desc = "verifier OFF -> ON"
            elif not tried_hybrid:
                trial_config["hybrid_date_boost"] = True
                tried_hybrid = True
                action_desc = "hybrid_date_boost OFF -> ON"
            else:
                changelog.append(f"## Round {round_num}\n- plurality={plurality}, actions exhausted; no-improvement.\n")
                no_improve_streak += 1
                continue
        elif plurality == "wrong_override":
            if not tried_hybrid:
                trial_config["hybrid_date_boost"] = True
                tried_hybrid = True
                action_desc = "hybrid_date_boost OFF -> ON (wrong_override mitigation)"
            else:
                changelog.append(f"## Round {round_num}\n- plurality={plurality}, actions exhausted; no-improvement.\n")
                no_improve_streak += 1
                continue
        else:  # wrong_value_other -- no mapped action
            changelog.append(f"## Round {round_num}\n- plurality={plurality}, no mapped action; no-improvement.\n")
            no_improve_streak += 1
            continue

        trial_results = await run_dev_round(chunks, entity_index, dev_split, trial_config, cache)
        trial_diag = diagnose_round(dev_split, trial_results)
        delta = trial_diag["n_correct"] - best_accuracy

        # Memory writes are kept unconditionally; other knob changes need a
        # >=2-case improvement (invariant: min-effect-size guard).
        keep = (memory_written > 0) or (delta >= 2)
        if keep:
            config = trial_config
            best_accuracy = trial_diag["n_correct"]
            diag = trial_diag
            no_improve_streak = 0
            changelog.append(
                f"## Round {round_num} — KEPT\n- plurality: {plurality}\n- action: {action_desc}\n"
                f"- dev accuracy: {trial_diag['n_correct']}/{trial_diag['n_total']} "
                f"(delta {delta:+d} vs previous {best_accuracy - delta if delta else best_accuracy})\n"
                f"- new config: {config}\n")
        else:
            no_improve_streak += 1
            changelog.append(
                f"## Round {round_num} — REVERTED\n- plurality: {plurality}\n- action tried: {action_desc}\n"
                f"- dev accuracy with change: {trial_diag['n_correct']}/{trial_diag['n_total']} "
                f"(delta {delta:+d}, below the +2 keep threshold)\n- config unchanged: {config}\n")
            diag = diagnose_round(dev_split, await run_dev_round(chunks, entity_index, dev_split, config, cache))

        audit_memory.append({"round": round_num, "config": dict(trial_config), "dev_accuracy": trial_diag["n_correct"],
                             "failure_counts_by_taxonomy": trial_diag["failure_counts_by_taxonomy"],
                             "case_ids_by_taxonomy": trial_diag["case_ids_by_taxonomy"], "kept": keep,
                             "action": action_desc})

    changelog.append(f"\n## Final\n- final config: {config}\n- final dev accuracy: {best_accuracy}/{len(dev_split)}\n"
                     f"- rounds run: {round_num}\n")

    AUDIT_MEMORY_PATH.write_text(json.dumps(audit_memory, indent=1))
    CHANGELOG_PATH.write_text("\n".join(changelog))
    (REPO / "advanced" / "final_config.json").write_text(json.dumps(config, indent=1))
    print(json.dumps({"final_config": config, "final_dev_accuracy": best_accuracy,
                      "n_dev": len(dev_split), "rounds_run": round_num}, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
