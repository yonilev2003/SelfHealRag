#!/usr/bin/env python3
"""`make verify-no-leak` (invariant #1). Static checks over advanced/ and
baseline/ source code (docstrings/comments stripped first, so this flags
actual code, not documentation ABOUT the invariant):
  (a) grep for fact_registry|test_split|all_probes|correction_signals in
      real code lines. `correction_signals` is permitted ONLY in
      advanced/memory_writer.py (the one sanctioned consultation point,
      shared by tuner.py's offline action and generator.py's live
      self-heal) and in import statements naming its functions (e.g.
      `from memory_writer import heal_entities` elsewhere) -- calling a
      function through its own module is not opening the file directly.
  (b) source may reference data/ only via explicit filenames -- any
      glob/listdir/iterdir/os.walk targeting data/ is a violation
  (c) re-hash test_split.locked.json, dev_split.json, and
      fact_registry.json against the digests recorded inline in
      PROCESS.md (not only the co-located .sha256 files)

Exits non-zero on any violation, printing exactly what was found.
"""

import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCAN_DIRS = [REPO / "advanced", REPO / "baseline"]
FORBIDDEN = re.compile(r"fact_registry|test_split|all_probes|correction_signals")
DATA_GLOB_RE = re.compile(r"\b(glob\.glob|os\.listdir|Path\.iterdir|\.iterdir\(\)|os\.walk)\s*\([^)]*[\"']?data[/\\]?[\"']?")
DOCSTRING_RE = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'')
IMPORT_LINE_RE = re.compile(r"^\s*from\s+\S+\s+import\s+")


def strip_docstrings_and_comments(text: str) -> str:
    text = DOCSTRING_RE.sub("", text)
    lines = []
    for line in text.split("\n"):
        code = line.split("#", 1)[0]
        lines.append(code)
    return "\n".join(lines)


def main():
    violations = []
    for d in SCAN_DIRS:
        for f in sorted(d.rglob("*.py")):
            if f.name.startswith("test_"):
                continue
            raw = f.read_text()
            code = strip_docstrings_and_comments(raw)
            for line_no, line in enumerate(code.split("\n"), 1):
                for m in FORBIDDEN.finditer(line):
                    token = m.group()
                    if token == "correction_signals":
                        if f.name == "memory_writer.py":
                            continue  # the one sanctioned consultation point
                        if IMPORT_LINE_RE.match(line) or "heal_entities" in line or "load_correction_signals" in line:
                            continue  # importing/calling the function, not opening the file
                    violations.append(f"{f.relative_to(REPO)}:{line_no}: forbidden token {token!r} — {line.strip()}")
                for m in DATA_GLOB_RE.finditer(line):
                    violations.append(f"{f.relative_to(REPO)}:{line_no}: wildcard/listing against data/: {m.group()!r}")

    process_md = (REPO / "PROCESS.md").read_text()
    for name, path in [
        ("data/probes/dev_split.json", REPO / "data" / "probes" / "dev_split.json"),
        ("data/probes/test_split.locked.json", REPO / "data" / "probes" / "test_split.locked.json"),
        ("data/fact_registry.json", REPO / "data" / "fact_registry.json"),
    ]:
        if not path.exists():
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash not in process_md:
            violations.append(f"{name}: sha256 {actual_hash} not found in PROCESS.md "
                              f"(modified after freeze, or hash drifted)")

    if violations:
        print("VIOLATIONS FOUND:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    print("No violations found.")


if __name__ == "__main__":
    main()
