"""Shared normalization + match rule (PLAN.md invariant #4).

Single source of truth, imported by BOTH the dev-loop scoring
(advanced/tuner.py, advanced/diagnose.py) and the frozen-test grader
(eval/grade_test.py) — and by the Phase-1 pre-test gate. A value or citation
match computed two different ways in two different places is exactly the
kind of inconsistency that makes a reported delta indefensible.
"""

import re

_STRIP_CHARS = re.compile(r"[\$₪,\s]")
_LEADING_NUMBER = re.compile(r"^-?\d+(\.\d+)?")


def normalize_value(raw) -> str:
    """Strip currency symbols/thousands separators/whitespace, casefold."""
    s = _STRIP_CHARS.sub("", str(raw))
    return s.casefold()


def values_match(predicted, expected) -> bool:
    """Numeric equality on the LEADING number if both have one (so "4 hours"
    matches "4", "$750" matches "750 usd") — a full-string float() cast would
    reject any answer carrying a unit word, which real answers do; else exact
    normalized string match."""
    np, ne = normalize_value(predicted), normalize_value(expected)
    mp, me = _LEADING_NUMBER.match(np), _LEADING_NUMBER.match(ne)
    if mp and me:
        return float(mp.group()) == float(me.group())
    return np == ne


def chunk_ids_match(predicted, expected) -> bool:
    """Exact, case-sensitive match — chunk ids are a controlled machine format."""
    return str(predicted) == str(expected)


def grounded_match(predicted_value, predicted_chunk_id, expected_value, expected_chunk_id) -> bool:
    """Joint match: both the value and the citation must be correct."""
    return values_match(predicted_value, expected_value) and chunk_ids_match(
        predicted_chunk_id, expected_chunk_id
    )
