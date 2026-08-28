#!/usr/bin/env python3
"""Phase 1 (PLAN.md) mini-corpus generator: 8 docs, 2 supersession pairs
(1 explicit, 1 implicit) + 1 near-dup trap, for the pre-test gate.

Fully hand-specified (no seed/randomness needed) but written as a script so
the process is reproducible and disclosed like everything else. This is a
throwaway pilot artifact, NOT the real Phase-2 corpus — chunk-header format
(`<!-- chunk_id: X entity_key: Y effective_date: YYYY-MM-DD -->`) is a working
prototype for the real generate_corpus.py.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS_DIR = HERE / "corpus"

# (doc_filename, [(chunk_id, entity_key, value, effective_date, supersedes_id, body_md)])
DOCS = [
    ("hr_remote_work.md", [
        ("hr-remote-v1-c01", "hr.remote_work_days_per_week", "3", "2026-01-01", None,
         "## Remote Work Policy\n\nEmployees may work remotely up to 3 days per "
         "week, subject to manager approval and team coverage requirements."),
    ]),
    ("it_equipment_refresh.md", [
        ("it-equip-v1-c01", "it.equipment_refresh_years", "3", "2026-01-01", None,
         "## Equipment Refresh Cycle\n\nCompany-issued laptops and monitors are "
         "refreshed every 3 years, or sooner in case of hardware failure."),
    ]),
    ("it_vpn_v1.md", [
        ("it-vpn-v1-c01", "it.vpn_session_timeout_hours", "8", "2026-01-10", None,
         "## VPN Access Policy\n\nAll employees must use the corporate VPN when "
         "accessing internal systems remotely."),
        ("it-vpn-v1-c02", "it.vpn_session_timeout_hours", "8", "2026-01-10", None,
         "VPN sessions automatically time out after 8 hours of inactivity and "
         "require re-authentication via SSO."),
    ]),
    ("it_vpn_v2.md", [
        ("it-vpn-v2-c01", "it.vpn_session_timeout_hours", "4", "2026-05-01", "it-vpn-v1-c01",
         "## VPN Access Policy (Updated)\n\nFollowing a security review, VPN "
         "session limits have been tightened. This policy supersedes the "
         "January VPN policy (effective 2026-01-10)."),
        ("it-vpn-v2-c02", "it.vpn_session_timeout_hours", "4", "2026-05-01", "it-vpn-v1-c01",
         "VPN sessions now automatically time out after 4 hours of inactivity "
         "and require re-authentication via SSO."),
    ]),
    ("finance_refund_v1.md", [
        ("finance-refund-v1-c01", "finance.refund_cap_usd", "500", "2026-01-05", None,
         "## Customer Refund Policy\n\nCustomer service representatives may "
         "approve refunds up to $500 without manager sign-off."),
        ("finance-refund-v1-c02", "finance.refund_cap_usd", "500", "2026-01-05", None,
         "Refunds above this amount require a finance manager's written "
         "approval before processing."),
    ]),
    ("finance_refund_v2.md", [
        ("finance-refund-v2-c01", "finance.refund_cap_usd", "750", "2026-06-15", "finance-refund-v1-c01",
         "## Customer Refund Policy\n\nCustomer service representatives may "
         "approve refunds up to $750 without manager sign-off."),
        ("finance-refund-v2-c02", "finance.refund_cap_usd", "750", "2026-06-15", "finance-refund-v1-c01",
         "Refunds above this amount require a finance manager's written "
         "approval before processing."),
    ]),
    ("sales_expense_cap.md", [
        ("sales-expense-v1-c01", "sales.client_dinner_cap_usd", "200", "2026-01-01", None,
         "## Sales Team Expense Policy\n\nSales representatives may expense up "
         "to $200 per client dinner, with an itemized receipt."),
    ]),
    ("eng_expense_cap.md", [
        ("eng-expense-v1-c01", "eng.team_lunch_cap_usd", "150", "2026-01-01", None,
         "## Engineering Team Expense Policy\n\nEngineering managers may expense "
         "up to $150 per team lunch, with an itemized receipt."),
    ]),
]

PROBES = [
    {"probe_id": "mini-01", "question": "What is the current VPN session timeout, in hours?",
     "expected_value": "4", "expected_chunk_id": "it-vpn-v2-c02",
     "category": "contradiction", "trap_subtype": "explicit_supersession"},
    {"probe_id": "mini-02", "question": "How many hours before a VPN session times out under the current policy?",
     "expected_value": "4", "expected_chunk_id": "it-vpn-v2-c02",
     "category": "contradiction", "trap_subtype": "explicit_supersession"},
    {"probe_id": "mini-03", "question": "What is the current customer refund cap, in USD, that a rep can approve without manager sign-off?",
     "expected_value": "750", "expected_chunk_id": "finance-refund-v2-c01",
     "category": "contradiction", "trap_subtype": "implicit_supersession"},
    {"probe_id": "mini-04", "question": "What is the Sales team's expense cap for a client dinner, in USD?",
     "expected_value": "200", "expected_chunk_id": "sales-expense-v1-c01",
     "category": "near_dup", "trap_subtype": "none"},
    {"probe_id": "mini-05", "question": "How many days per week can employees work remotely?",
     "expected_value": "3", "expected_chunk_id": "hr-remote-v1-c01",
     "category": "atomic", "trap_subtype": "none"},
    {"probe_id": "mini-06", "question": "Every how many years is company IT equipment refreshed?",
     "expected_value": "3", "expected_chunk_id": "it-equip-v1-c01",
     "category": "atomic", "trap_subtype": "none"},
]


def main():
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for f in CORPUS_DIR.glob("*.md"):
        f.unlink()

    registry = []
    n_chunks = 0
    for filename, chunks in DOCS:
        parts = []
        for chunk_id, entity_key, value, eff_date, supersedes, body in chunks:
            supersedes_str = supersedes if supersedes else "null"
            parts.append(
                f"<!-- chunk_id: {chunk_id} entity_key: {entity_key} "
                f"effective_date: {eff_date} supersedes_id: {supersedes_str} -->\n{body}\n"
            )
            registry.append({
                "chunk_id": chunk_id, "entity_key": entity_key, "value": value,
                "effective_date": eff_date, "supersedes_id": supersedes,
            })
            n_chunks += 1
        (CORPUS_DIR / filename).write_text("\n".join(parts))

    (HERE / "fact_registry.json").write_text(json.dumps(registry, indent=1))
    (HERE / "probes.json").write_text(json.dumps(PROBES, indent=1))

    print(json.dumps({
        "n_docs": len(DOCS), "n_chunks": n_chunks, "n_probes": len(PROBES),
        "staleness_probes": sum(1 for p in PROBES if p["category"] == "contradiction"),
    }, indent=1))


if __name__ == "__main__":
    main()
