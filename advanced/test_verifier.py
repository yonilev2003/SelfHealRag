"""Unit tests for advanced/verifier.py against the real frozen corpus.
Run: python3 advanced/test_verifier.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_index import build_entity_index, load_corpus  # noqa: E402
from verifier import verify  # noqa: E402


def test_verifier():
    chunks = load_corpus()
    index = build_entity_index(chunks)
    cases = [
        # (predicted, expect_overridden, expect_value)
        ({"value": "8", "chunk_id": "it_vpn_session_timeout_hours_v1-c01"}, True, "4"),
        ({"value": "4", "chunk_id": "it_vpn_session_timeout_hours_v2-c01"}, False, "4"),
        ({"value": "4", "chunk_id": "it_vpn_session_timeout_hours_v2-c02"}, False, "4"),
        ({"value": "750", "chunk_id": "finance_refund_cap_usd_v2-c01"}, True, "900"),
        ({"value": "500", "chunk_id": "finance_refund_cap_usd_v1-c01"}, True, "900"),
        ({"value": "900", "chunk_id": "finance_refund_cap_usd_v3-c02"}, False, "900"),
        # atomic, single version -- verifier passes the predicted value through
        # unchanged (chain-currency checking isn't factual grading; a wrong
        # atomic-fact answer is the generator's error, not the verifier's job)
        ({"value": "10", "chunk_id": "hr_bereavement_leave_days-c01"}, False, "10"),
    ]
    failures = []
    for pred, expect_overridden, expect_value in cases:
        r = verify(chunks, pred, index)
        if r["overridden"] != expect_overridden or r["value"] != expect_value:
            failures.append(f"{pred}: got overridden={r['overridden']} value={r['value']!r}, "
                            f"expected overridden={expect_overridden} value={expect_value!r}")

    # multi-hop and memory citations pass through untouched
    r_mh = verify(chunks, {"value": "2500", "chunk_id": "a-c01+b-c01"}, index)
    assert r_mh["overridden"] is False and not r_mh["requires_human_review"]
    r_mem = verify(chunks, {"value": "250", "chunk_id": "MEMORY"}, index)
    assert r_mem["overridden"] is False and not r_mem["requires_human_review"]

    assert not failures, "\n".join(failures)
    print(f"PASS: {len(cases)}/{len(cases)} verifier cases + multi-hop/memory passthrough correct")


if __name__ == "__main__":
    test_verifier()
