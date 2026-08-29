"""Shared self-heal logic: given an entity_key with no persisted memory
entry, consult data/correction_signals.json (never the oracle) and, if a
signal exists, extract + persist a correction. ONE implementation, used by
BOTH advanced/tuner.py's offline dev-loop batch action AND
advanced/generator.py's live runtime path -- a real production SelfHeal RAG
self-heals continuously as it serves queries, not only during an offline
dev-tuning phase; gating this capability to dev-only entities would leave
the frozen test split's memory_correction cases permanently unfixable
purely because their entities were never in the dev sample (found live
when Phase 5's frozen run showed Arm C scoring identically to the static
baseline on every test memory_correction case -- see PROCESS.md).
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "eval"))
from llm_call import run_single_call  # noqa: E402

MEMORY_PATH = REPO / "advanced" / "memory.json"
SIGNAL_EXTRACTOR_TEMPLATE = (REPO / "prompts" / "signal_extractor.md").read_text()


def load_correction_signals() -> dict:
    signals = json.loads((REPO / "data" / "correction_signals.json").read_text())
    return {s["entity_key"]: s for s in signals}


def load_memory() -> dict:
    if MEMORY_PATH.exists():
        return json.loads(MEMORY_PATH.read_text())
    return {}


async def heal_entities(entity_keys, round_label="live") -> dict:
    """For each entity_key not already in memory, check correction_signals.json;
    if present, extract the value and persist it. Returns {entity_key: entry}
    for newly-written entries only. Thread-unsafe by design (single-process
    eval runs only)."""
    signals_by_entity = load_correction_signals()
    memory = load_memory()
    new_entries = {}
    for entity_key in entity_keys:
        if entity_key in memory or entity_key not in signals_by_entity:
            continue
        signal = signals_by_entity[entity_key]
        prompt = SIGNAL_EXTRACTOR_TEMPLATE.format(entity_key=entity_key, signal_text=signal["text"])
        res = await run_single_call(prompt)
        extracted = (res.get("predicted") or {}).get("value")
        if extracted is None:
            continue
        entry = {"value": extracted, "source_signal_id": signal["signal_id"], "round_added": round_label}
        memory[entity_key] = entry
        new_entries[entity_key] = entry
    if new_entries:
        MEMORY_PATH.write_text(json.dumps(memory, indent=1))
    return new_entries
