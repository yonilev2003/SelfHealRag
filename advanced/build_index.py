"""Parses RAW corpus markdown only (invariant #1 — never imports or reads
data/fact_registry.json or data/correction_signals.json). This is the ONE
shared chunk-loading/rendering module every arm (baselines included) uses,
so chunk text is byte-identical everywhere per invariant #5's fairness
requirement — baselines import load_corpus/render_chunk directly, they
don't re-implement parsing.

Also builds entity_index.json: entity_key -> [chunk_ids present in the
corpus], used by advanced/verifier.py for O(1) supersession-chain lookup.
Built here, from raw text, independent of the oracle.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO / "data" / "corpus"
INDEX_PATH = REPO / "advanced" / "entity_index.json"


def load_corpus(corpus_dir: Path = None) -> dict:
    """Returns {chunk_id: {entity_key, effective_date, supersedes_id, text}}."""
    corpus_dir = corpus_dir or CORPUS_DIR
    chunks = {}
    for f in sorted(corpus_dir.glob("*.md")):
        for block in f.read_text().split("<!-- chunk_id:")[1:]:
            header, _, body = block.partition("-->")
            parts = header.strip().split()
            chunk_id = parts[0]
            entity_key = parts[parts.index("entity_key:") + 1]
            eff_date = parts[parts.index("effective_date:") + 1]
            supersedes = parts[parts.index("supersedes_id:") + 1]
            chunks[chunk_id] = {
                "entity_key": entity_key, "effective_date": eff_date,
                "supersedes_id": None if supersedes == "null" else supersedes,
                "text": body.strip(),
            }
    return chunks


def render_chunk(chunk_id: str, chunk: dict) -> str:
    return (f"[chunk_id: {chunk_id}] [effective_date: {chunk['effective_date']}]\n"
            f"{chunk['text']}")


def build_entity_index(chunks: dict) -> dict:
    """entity_key -> [chunk_ids], sorted by effective_date ascending, so
    index[-1] is always the current (latest) chunk for that entity — this
    is what the verifier consults, built entirely from parsed headers."""
    by_entity = {}
    for cid, c in chunks.items():
        by_entity.setdefault(c["entity_key"], []).append(cid)
    for ek in by_entity:
        by_entity[ek].sort(key=lambda cid: chunks[cid]["effective_date"])
    return by_entity


def main():
    chunks = load_corpus()
    index = build_entity_index(chunks)
    INDEX_PATH.write_text(json.dumps(index, indent=1))
    print(json.dumps({"n_chunks": len(chunks), "n_entities": len(index)}, indent=1))


if __name__ == "__main__":
    main()
