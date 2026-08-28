"""Unit tests for eval/match.py — the single shared normalize/match rule
(PLAN.md invariant #4). Run: python3 eval/test_match.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from match import grounded_match, values_match  # noqa: E402

VALUE_CASES = [
    ("4", "4", True),
    ("4 hours", "4", True),
    ("$750", "750", True),
    ("750 USD", "$750", True),
    ("500.00", "500", True),
    ("3 days per week", "3", True),
    ("₪1,200", "1200", True),
    ("current policy: 4 hours", "4", False),  # leading text before the number -> no leading match, exact-string fallback correctly fails
    ("8", "4", False),
    ("not specified", "4", False),
    ("Approved", "Approved", True),
    ("approved", "Approved", True),
]


def test_values_match():
    failures = [f"{p!r} vs {e!r}: expected {want}, got {values_match(p, e)}"
                for p, e, want in VALUE_CASES if values_match(p, e) != want]
    assert not failures, "\n".join(failures)
    print(f"PASS: {len(VALUE_CASES)}/{len(VALUE_CASES)} values_match cases correct")


def test_grounded_match():
    assert grounded_match("4 hours", "chunk-a", "4", "chunk-a") is True
    assert grounded_match("4 hours", "chunk-b", "4", "chunk-a") is False  # right value, wrong citation
    assert grounded_match("8 hours", "chunk-a", "4", "chunk-a") is False  # right citation, wrong (stale) value
    print("PASS: grounded_match joint value+citation cases correct")


if __name__ == "__main__":
    test_values_match()
    test_grounded_match()
