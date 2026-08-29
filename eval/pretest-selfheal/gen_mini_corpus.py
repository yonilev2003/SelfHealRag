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

# --- Scale-up for gate run 2 (CHECKPOINT_1.md recommendation) -------------
# Run 1 (12 chunks) gave A0/B nothing to lose track of -- both hit a clean
# 6/6 ceiling. This is NOT the coded harden() recipe (a few extra decoys in
# the SAME 12-chunk corpus); it's the diagnosed real fix: scale, so context
# degradation / retrieval competition / entity-tracking-across-multiple-
# simultaneous-revisions have room to actually show up, closer to what the
# real 248-chunk Phase-2 corpus will look like. The 6 probes and their
# target facts (the original 8 docs) are UNCHANGED -- ground truth is
# identical, only the surrounding noise grows.

# Two DECOY supersession pairs (different entities than any probe targets)
# so several "policy got revised" episodes run concurrently -- stresses
# whether a system tracks the CORRECT entity's current value, not just
# "the most recent-sounding excerpt it saw".
DECOY_DOCS = [
    ("support_sla_v1.md", [
        ("support-sla-v1-c01", "support.sla_response_hours", "24", "2026-01-20", None,
         "## Support SLA Policy\n\nAll customer support tickets are triaged by "
         "the on-duty support engineer within one business day."),
        ("support-sla-v1-c02", "support.sla_response_hours", "24", "2026-01-20", None,
         "Tickets must receive a first response from a support engineer "
         "within 24 hours of submission."),
    ]),
    ("support_sla_v2.md", [
        ("support-sla-v2-c01", "support.sla_response_hours", "12", "2026-04-10", "support-sla-v1-c01",
         "## Support SLA Policy (Updated)\n\nTo improve customer satisfaction "
         "scores, response targets have been tightened. This policy "
         "supersedes the January SLA policy (effective 2026-01-20)."),
        ("support-sla-v2-c02", "support.sla_response_hours", "12", "2026-04-10", "support-sla-v1-c01",
         "Tickets must now receive a first response from a support engineer "
         "within 12 hours of submission."),
    ]),
    ("compliance_retention_v1.md", [
        ("compliance-retention-v1-c01", "compliance.data_retention_months", "24", "2026-02-01", None,
         "## Customer Data Retention\n\nCustomer account data, including "
         "order history and support tickets, is subject to a defined "
         "retention period after account closure."),
        ("compliance-retention-v1-c02", "compliance.data_retention_months", "24", "2026-02-01", None,
         "Data is retained for 24 months after account closure, after which "
         "it is permanently deleted from production systems."),
    ]),
    ("compliance_retention_v2.md", [
        ("compliance-retention-v2-c01", "compliance.data_retention_months", "36", "2026-07-20", "compliance-retention-v1-c01",
         "## Customer Data Retention\n\nCustomer account data, including "
         "order history and support tickets, is subject to a defined "
         "retention period after account closure."),
        ("compliance-retention-v2-c02", "compliance.data_retention_months", "36", "2026-07-20", "compliance-retention-v1-c01",
         "Data is retained for 36 months after account closure, after which "
         "it is permanently deleted from production systems."),
    ]),
]

# Plain (non-versioned) noise topics -- realistic distractor density across
# other departments, each rendered as a context chunk + a value chunk
# (matching the real chunk-header pattern), no overlap with any probed fact.
NOISE_TOPICS = [
    ("security_badge", "sec.badge_access_hours", "IT & Security", "Badge Access Hours",
     "Building badge access for standard employees is enabled from 6am to "
     "10pm on weekdays.", "6am-10pm weekdays", "2026-01-01"),
    ("facilities_parking", "facilities.reserved_parking_spots", "Facilities", "Parking Allocation",
     "The downtown office garage reserves parking spots for employees who "
     "carpool with at least one colleague.", "12", "2026-01-01"),
    ("benefits_gym", "benefits.gym_stipend_usd", "People & Benefits", "Wellness Stipend",
     "Employees may expense a monthly wellness stipend toward a gym "
     "membership or fitness class subscription.", "60", "2026-01-01"),
    ("travel_mileage", "travel.mileage_rate_cents", "Finance", "Travel Mileage Reimbursement",
     "Employees driving a personal vehicle for approved business travel are "
     "reimbursed per mile driven.", "58", "2026-01-01"),
    ("onboarding_laptop", "it.onboarding_laptop_model", "IT & Security", "New Hire Equipment",
     "New hires are issued a standard-configuration laptop on their first "
     "day, selected from the current approved hardware list.", "14-inch model", "2026-01-01"),
    ("ops_oncall", "eng.oncall_rotation_weeks", "Engineering", "On-Call Rotation",
     "Backend engineers rotate through the production on-call schedule in "
     "fixed-length shifts, coordinated via the on-call calendar.", "1", "2026-01-01"),
    ("legal_nda", "legal.nda_duration_years", "Legal", "Standard NDA Terms",
     "The company's standard mutual non-disclosure agreement template "
     "specifies a confidentiality period for shared information.", "3", "2026-01-01"),
    ("marketing_brand", "marketing.brand_note", "Marketing", "Brand Voice Guidelines",
     "External communications should use plain, direct language and avoid "
     "jargon; the brand voice is described in detail in the design system "
     "handbook maintained by the marketing team.", "n/a", "2026-01-01"),
    ("hr_pto_buyout", "hr.pto_buyout_days_max", "People & Benefits", "PTO Buyout",
     "At year end, employees may request a cash buyout for a limited "
     "number of unused PTO days rather than rolling them over.", "5", "2026-01-01"),
    ("it_password_policy", "it.password_min_length", "IT & Security", "Password Requirements",
     "Corporate account passwords must meet a minimum length and "
     "complexity requirement enforced at the identity provider.", "12", "2026-01-01"),
    ("finance_expense_approval", "finance.expense_auto_approve_usd", "Finance", "Expense Auto-Approval",
     "Expense reports below a set threshold are automatically approved "
     "without manager review, provided a receipt is attached.", "50", "2026-01-01"),
    ("sales_commission", "sales.commission_rate_pct", "Sales", "Commission Structure",
     "Account executives earn a standard commission on closed-won deals, "
     "with accelerators above quarterly quota.", "8", "2026-01-01"),
    ("eng_oncall_pay", "eng.oncall_stipend_usd", "Engineering", "On-Call Stipend",
     "Engineers on the production on-call rotation receive an additional "
     "weekly stipend on top of regular salary.", "200", "2026-01-01"),
    ("hr_holiday_calendar", "hr.company_holidays_count", "People & Benefits", "Company Holidays",
     "The company observes a fixed set of paid holidays each calendar "
     "year, published on the HR intranet at the start of January.", "10", "2026-01-01"),
    ("it_hardware_request", "it.hardware_request_sla_days", "IT & Security", "Hardware Request SLA",
     "Requests for additional or replacement hardware submitted through "
     "the IT ticketing system are typically fulfilled within a set number "
     "of business days.", "5", "2026-01-01"),
    ("finance_budget_cycle", "finance.budget_review_cycle_months", "Finance", "Budget Review Cycle",
     "Department budgets are reviewed and reforecast on a recurring cycle "
     "throughout the fiscal year, coordinated by the finance business "
     "partner for each team.", "3", "2026-01-01"),
    ("legal_contract_review", "legal.contract_review_sla_days", "Legal", "Contract Review SLA",
     "Standard vendor contracts submitted for legal review are typically "
     "turned around within a set number of business days, longer for "
     "contracts requiring outside counsel.", "7", "2026-01-01"),
    ("hr_probation_period", "hr.probation_period_months", "People & Benefits", "New Hire Probation",
     "New hires complete an initial probation period during which "
     "performance and fit are formally reviewed with their manager.", "3", "2026-01-01"),
    ("it_vpn_client_version", "it.vpn_client_min_version", "IT & Security", "VPN Client Version",
     "Employees must run a minimum supported version of the corporate VPN "
     "client; older versions are blocked from connecting at the gateway.", "4.2", "2026-01-01"),
    ("sales_deal_size_threshold", "sales.deal_approval_threshold_usd", "Sales", "Deal Approval Threshold",
     "Deals above a set annual contract value require sign-off from a "
     "sales director before the quote is sent to the customer.", "50000", "2026-01-01"),
]


def build_noise_docs():
    docs = []
    for slug, entity_key, dept, title, context_body, value, eff_date in NOISE_TOPICS:
        docs.append((f"{slug}.md", [
            (f"{slug}-c01", entity_key, value, eff_date, None,
             f"## {title}\n\n{context_body}"),
            (f"{slug}-c02", entity_key, value, eff_date, None,
             f"This is documented under the {dept} section of the employee "
             f"handbook, current value: {value}."),
        ]))
    return docs


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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale-up", action="store_true",
                    help="Add decoy supersession pairs + noise docs (gate run 2, "
                         "per CHECKPOINT_1.md -- the one hardening attempt)")
    args = ap.parse_args()

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for f in CORPUS_DIR.glob("*.md"):
        f.unlink()

    all_docs = list(DOCS)
    if args.scale_up:
        all_docs += DECOY_DOCS + build_noise_docs()

    registry = []
    n_chunks = 0
    for filename, chunks in all_docs:
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
        "n_docs": len(all_docs), "n_chunks": n_chunks, "n_probes": len(PROBES),
        "staleness_probes": sum(1 for p in PROBES if p["category"] == "contradiction"),
        "scaled_up": args.scale_up,
    }, indent=1))


if __name__ == "__main__":
    main()
