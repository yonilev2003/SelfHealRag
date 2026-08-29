#!/usr/bin/env python3
"""Phase 2 (PLAN.md rev 4): the real SelfHeal RAG corpus generator.

Deterministic, stdlib-only, seed 42 (no randomness actually used -- content
is fully hand-specified, matching the mini pretest's approach, so a re-run
is byte-identical by construction). Produces:
  - data/corpus/*.md          the policy handbook (what every arm can read)
  - data/fact_registry.json   ORACLE (eval-only; ALSO holds the true current
                              value for memory_correction entities, whose
                              corpus text deliberately states a stale one)
  - data/correction_signals.json   ~10 synthetic ticket/audit texts, ONE per
                              memory_correction entity; NEVER read by any
                              baseline arm -- only advanced/diagnose.py

Five fact categories (feeding the 40 probes generate_probes.py builds on
top of this):
  ATOMIC            -- 8 simple, non-versioned facts.
  CONTRADICTION      -- 12 entities with 2 (or 3, for one 3-hop chain) dated
                        versions; 9 resolved via explicit "supersedes"
                        language, 3 implicit (later effective_date only).
  NEAR_DUP          -- 8 target entities each paired with a lexically
                        similar but distinct decoy entity.
  MULTI_HOP         -- 4 entities whose answer requires combining 2 (three
                        of them) or 3 (one of them) separate component facts.
  MEMORY_CORRECTION -- 8 entities: the corpus states a stale value; the true
                        current value is only findable in a correction
                        signal document.
Plus a generic noise layer (additional unrelated department docs) for
realistic distractor density.

Chunk header format matches the mini pretest exactly:
<!-- chunk_id: X entity_key: Y effective_date: YYYY-MM-DD supersedes_id: Z -->
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CORPUS_DIR = REPO / "data" / "corpus"
GENERATOR_VERSION = "1.0"

# ============================================================================
# 1. ATOMIC facts -- 8 simple, non-versioned, single-source-of-truth facts.
# ============================================================================
ATOMIC = [
    ("hr_bereavement_leave", "hr.bereavement_leave_days", "5", "2026-01-01",
     "People & Benefits", "Bereavement Leave",
     "Employees may take paid bereavement leave following the death of an "
     "immediate family member, in addition to any unused PTO."),
    ("it_offboarding_sla", "it.offboarding_access_revoke_hours", "4", "2026-01-01",
     "IT & Security", "Offboarding Access Revocation",
     "When an employee's departure is confirmed, IT revokes all system "
     "access within a fixed window of the employee's last working day."),
    ("finance_per_diem", "finance.travel_per_diem_usd", "75", "2026-01-01",
     "Finance", "Domestic Travel Per Diem",
     "Employees traveling domestically for business receive a daily meal "
     "and incidentals allowance, no receipts required below this amount."),
    ("legal_ip_assignment", "legal.ip_assignment_scope", "work-related",
     "2026-01-01", "Legal", "IP Assignment Scope",
     "The standard employment agreement assigns the company ownership of "
     "inventions and work product created within the scope of employment."),
    ("sales_quota_reset", "sales.quota_reset_cadence", "quarterly", "2026-01-01",
     "Sales", "Quota Reset Cadence",
     "Sales quotas are set and reset on a fixed recurring cadence, "
     "published by RevOps at the start of each cycle."),
    ("eng_code_review_min", "eng.code_review_min_approvals", "1", "2026-01-01",
     "Engineering", "Code Review Requirements",
     "Pull requests to the main branch require a minimum number of "
     "approving reviews from a codeowner before merge."),
    ("facilities_desk_ratio", "facilities.desk_booking_ratio", "1.5", "2026-01-01",
     "Facilities", "Hybrid Desk Booking Ratio",
     "The downtown office provisions bookable desks at a fixed ratio to "
     "headcount, reflecting the company's hybrid attendance pattern."),
    ("support_csat_target", "support.csat_target_pct", "90", "2026-01-01",
     "Support", "CSAT Target",
     "The support organization tracks a customer satisfaction target for "
     "resolved tickets, reviewed monthly by the support leadership team."),
]

# ============================================================================
# 2. CONTRADICTION -- 12 entities, dated versions. 9 explicit, 3 implicit.
#    One explicit entity extended to a 3rd version (3-hop chain, test-only
#    trap subtype per invariant #3).
# ============================================================================
# (entity_key, dept, title, [(value, eff_date, explicit_supersede_text_or_None), ...])
CONTRADICTION = [
    ("it.vpn_session_timeout_hours", "IT & Security", "VPN Access Policy", [
        ("8", "2026-01-10", None),
        ("4", "2026-05-01", "This policy supersedes the January VPN policy (effective 2026-01-10)."),
    ]),
    ("hr.pto_accrual_days_per_month", "People & Benefits", "PTO Accrual", [
        ("1.25", "2026-01-05", None),
        ("1.5", "2026-04-15", "This policy supersedes the PTO accrual policy dated 2026-01-05."),
    ]),
    ("finance.expense_report_deadline_days", "Finance", "Expense Report Deadline", [
        ("30", "2026-01-01", None),
        ("14", "2026-06-01", "This supersedes the expense reporting deadline in effect since 2026-01-01."),
    ]),
    ("it.password_rotation_days", "IT & Security", "Password Rotation", [
        ("90", "2026-01-01", None),
        ("180", "2026-05-20", "This policy supersedes the password rotation requirement dated 2026-01-01."),
    ]),
    ("sales.deal_discount_max_pct", "Sales", "Maximum Discretionary Discount", [
        ("10", "2026-01-01", None),
        ("15", "2026-06-10", "This supersedes the discount policy published 2026-01-01."),
    ]),
    ("hr.remote_work_days_per_week", "People & Benefits", "Remote Work Days", [
        ("2", "2026-01-01", None),
        ("3", "2026-07-01", "This policy supersedes the remote work policy dated 2026-01-01."),
    ]),
    ("eng.oncall_rotation_days", "Engineering", "On-Call Rotation Length", [
        ("14", "2026-01-01", None),
        ("7", "2026-05-15", "This supersedes the on-call rotation policy from 2026-01-01."),
    ]),
    ("support.first_response_sla_hours", "Support", "First Response SLA", [
        ("24", "2026-01-20", None),
        ("12", "2026-04-10", "This policy supersedes the January SLA policy (effective 2026-01-20)."),
    ]),
    ("finance.refund_cap_usd", "Finance", "Customer Refund Cap", [
        ("500", "2026-01-05", None),
        ("750", "2026-06-15", None),  # 3-hop chain base: v1->v2 implicit
        ("900", "2026-08-01", None),  # v2->v3 implicit -- the 3-hop test-only trap
    ]),
    # implicit pairs (no "supersedes" text at all -- later effective_date only)
    ("compliance.data_retention_months", "Compliance", "Customer Data Retention", [
        ("24", "2026-02-01", None),
        ("36", "2026-07-20", None),
    ]),
    ("it.laptop_refresh_years", "IT & Security", "Laptop Refresh Cycle", [
        ("4", "2026-01-01", None),
        ("3", "2026-06-01", None),
    ]),
    ("legal.contractor_nda_years", "Legal", "Contractor NDA Duration", [
        ("2", "2026-01-01", None),
        ("5", "2026-05-01", None),
    ]),
]
# indices into CONTRADICTION that are EXPLICIT (have supersede text on v2+)
# vs IMPLICIT: the refund_cap chain (index 8) is implicit at each hop (its
# own 3-hop mechanic covers that); the last 3 entries (9,10,11) are the
# simple 2-version implicit pairs.

# ============================================================================
# 3. NEAR_DUP -- 8 target entities, each paired with a lexically similar
#    but semantically distinct decoy (different department/entity).
# ============================================================================
NEAR_DUP = [
    ("sales.client_dinner_cap_usd", "200", "Sales", "Client Dinner Expense Cap",
     "Sales representatives may expense up to this amount per client dinner, with an itemized receipt.",
     "eng.team_lunch_cap_usd", "150", "Engineering", "Team Lunch Expense Cap",
     "Engineering managers may expense up to this amount per team lunch, with an itemized receipt."),
    ("hr.new_parent_leave_weeks", "12", "People & Benefits", "New Parent Leave",
     "Employees welcoming a new child via birth or adoption receive paid leave at this length.",
     "hr.caregiver_leave_weeks", "4", "People & Benefits", "Family Caregiver Leave",
     "Employees caring for a family member with a serious health condition receive paid leave at this length."),
    ("it.badge_access_hours_standard", "16", "IT & Security", "Standard Badge Access Hours",
     "Standard employee badges grant building access during this many hours per day.",
     "it.badge_access_hours_contractor", "10", "IT & Security", "Contractor Badge Access Hours",
     "Contractor badges grant building access during this many hours per day, escorted outside that window."),
    ("finance.po_auto_approve_usd", "1000", "Finance", "Purchase Order Auto-Approval",
     "Purchase orders below this amount are automatically approved without manager sign-off.",
     "finance.expense_auto_approve_usd", "50", "Finance", "Expense Report Auto-Approval",
     "Individual expense line items below this amount are automatically approved without manager review."),
    ("support.escalation_response_minutes", "30", "Support", "Escalation Response Time",
     "Escalated (P1) tickets receive an acknowledgment from a support lead within this window.",
     "support.standard_response_minutes", "240", "Support", "Standard Response Time",
     "Standard (P3) tickets receive a first response from the queue within this window."),
    ("sales.commission_accelerator_pct", "12", "Sales", "Commission Accelerator Rate",
     "Account executives earn commission at this rate on revenue above 100% of quota.",
     "sales.commission_base_pct", "8", "Sales", "Base Commission Rate",
     "Account executives earn commission at this rate on revenue up to 100% of quota."),
    ("eng.incident_postmortem_days", "5", "Engineering", "Incident Postmortem Deadline",
     "A written postmortem is due within this many business days of a SEV1/SEV2 incident's resolution.",
     "eng.incident_page_response_minutes", "15", "Engineering", "Incident Page Response Time",
     "The on-call engineer must acknowledge a production page within this many minutes."),
    ("legal.vendor_contract_review_days", "10", "Legal", "Vendor Contract Review SLA",
     "Standard vendor contracts submitted for legal review are turned around within this many business days.",
     "legal.customer_contract_review_days", "5", "Legal", "Customer Contract Review SLA",
     "Customer-facing order forms submitted for legal review are turned around within this many business days."),
]

# ============================================================================
# 4. MULTI_HOP -- 4 entities requiring combining 2 (x3) or 3 (x1) component
#    facts, each a small standalone chunk, to compute the final answer.
# ============================================================================
# (result_entity_key, question_context, [(component_entity_key, component_fact_text, component_value)], compute_note)
MULTI_HOP = [
    ("derived.total_onboarding_budget_usd",
     "New senior engineer onboarding budget",
     [("onboarding.base_equipment_budget_usd", "The standard new-hire equipment budget (laptop, monitor, peripherals) is $1,800.", "1800"),
      ("onboarding.senior_tier_bonus_usd", "Senior-level hires (L5+) receive an additional $700 equipment allowance for role-specific hardware.", "700")],
     "2500"),  # 1800+700
    ("derived.total_pto_days_5yr_tenure",
     "Total annual PTO for an employee with 5 years of tenure",
     [("hr.base_pto_days", "The standard annual PTO allowance for all employees is 15 days.", "15"),
      ("hr.tenure_bonus_pto_days_per_5yr", "Employees receive 3 additional PTO days for every 5 years of tenure completed.", "3")],
     "18"),  # 15+3
    ("derived.max_travel_reimbursement_usd",
     "Maximum reimbursable amount for a 3-night domestic conference trip",
     [("finance.travel_per_diem_usd", "Employees traveling domestically for business receive a $75/day meal and incidentals allowance.", "75"),
      ("finance.conference_lodging_cap_usd_per_night", "Conference lodging is reimbursed up to $220 per night at the conference hotel rate.", "220")],
     "885"),  # 75*3 + 220*3 = 225+660=885 (approx model, documented in the answer key as sum of both rates * 3 nights)
    ("derived.total_relocation_package_usd",
     "Total relocation package for an out-of-state new hire (3-hop)",
     [("relocation.moving_stipend_usd", "New hires relocating more than 250 miles receive a $3,000 moving stipend.", "3000"),
      ("relocation.temp_housing_weeks", "Relocating new hires are eligible for up to 4 weeks of temporary housing, valued at $400/week.", "1600"),
      ("relocation.travel_reimbursement_usd", "One round-trip flight and mileage for the relocation move is reimbursed up to $500.", "500")],
     "5100"),  # 3000+1600+500
]

# ============================================================================
# 5. MEMORY_CORRECTION -- 8 entities. Corpus states a STALE value; the true
#    current value is only in a correction_signals.json entry.
# ============================================================================
# (entity_key, dept, title, stale_value, stale_eff_date, corpus_body,
#  true_value, signal_id, signal_text)
MEMORY_CORRECTION = [
    ("eng.oncall_stipend_usd", "Engineering", "On-Call Stipend", "200", "2026-01-01",
     "Engineers on the production on-call rotation receive an additional weekly stipend on top of regular salary.",
     "250", "TICKET-4521",
     "Ticket #4521 (Finance, resolved): Approved raising the Engineering on-call weekly stipend from $200 to $250, "
     "effective this pay period, per the Q3 comp review. Please route future on-call pay questions to this ticket "
     "until the handbook is updated."),
    ("support.weekend_shift_diff_pct", "Support", "Weekend Shift Differential", "10", "2026-01-01",
     "Support agents working scheduled weekend shifts receive a shift differential on top of their base hourly rate.",
     "15", "AUDIT-0912",
     "HR audit note (AUDIT-0912): Weekend shift differential for support agents was increased from 10% to 15% "
     "following the union-adjacent pay parity review; payroll has already implemented this, handbook update pending."),
    ("facilities.parking_reimbursement_usd", "Facilities", "Parking Reimbursement", "80", "2026-01-01",
     "Employees who drive to the downtown office may expense monthly parking up to a set cap.",
     "120", "TICKET-3390",
     "Ticket #3390 (Facilities, resolved): Downtown garage rates increased; monthly parking reimbursement cap "
     "raised from $80 to $120 to match, approved by Facilities lead. Handbook page still shows the old figure."),
    ("benefits.gym_stipend_usd", "People & Benefits", "Wellness Stipend", "60", "2026-01-01",
     "Employees may expense a monthly wellness stipend toward a gym membership or fitness class subscription.",
     "100", "TICKET-5108",
     "Ticket #5108 (Benefits vendor change): Switching wellness vendors; new monthly stipend cap is $100 "
     "(up from $60) starting next cycle, per the signed vendor agreement. Docs team notified but not yet updated."),
    ("it.hardware_request_sla_days", "IT & Security", "Hardware Request SLA", "5", "2026-01-01",
     "Requests for additional or replacement hardware submitted through the IT ticketing system are fulfilled "
     "within a target number of business days.",
     "2", "AUDIT-1147",
     "IT ops audit (AUDIT-1147): After the new hardware vendor contract, fulfillment SLA improved from 5 "
     "business days to 2. Support macros already updated; employee handbook page is stale."),
    ("sales.deal_approval_threshold_usd", "Sales", "Deal Approval Threshold", "50000", "2026-01-01",
     "Deals above a set annual contract value require sign-off from a sales director before the quote is sent.",
     "75000", "TICKET-2287",
     "Ticket #2287 (Sales Ops, resolved): VP Sales approved raising the director-approval threshold from "
     "$50,000 to $75,000 ACV to reduce approval bottlenecks, effective immediately. Handbook not yet updated."),
    ("legal.nda_duration_years", "Legal", "Standard NDA Term", "3", "2026-01-01",
     "The company's standard mutual non-disclosure agreement template specifies a confidentiality period.",
     "5", "AUDIT-0764",
     "Legal template audit (AUDIT-0764): Standard NDA confidentiality term extended from 3 to 5 years in the "
     "latest template revision (v4), approved by General Counsel. Old handbook reference to 3 years is outdated."),
    ("eng.oncall_rotation_pay_multiplier", "Engineering", "Holiday On-Call Multiplier", "1.5", "2026-01-01",
     "Engineers on-call during a recognized company holiday receive base on-call pay at a multiplier.",
     "2.0", "TICKET-4890",
     "Ticket #4890 (Comp review): Holiday on-call multiplier increased from 1.5x to 2.0x following the engineering "
     "retention review, approved by the CTO. Payroll updated; handbook page still says 1.5x."),
]

# ============================================================================
# 6. Generic noise -- additional unrelated department docs for realistic
#    distractor density (no probe targets this fact).
# ============================================================================
NOISE = [
    ("marketing.brand_review_cadence", "Marketing", "Brand Asset Review", "quarterly",
     "External-facing brand assets are reviewed on a recurring cadence by the marketing design lead."),
    ("legal.trademark_renewal_note", "Legal", "Trademark Portfolio", "n/a",
     "The company's registered trademarks are tracked in a portfolio maintained by outside counsel."),
    ("facilities.bike_storage_spots", "Facilities", "Bike Storage", "20",
     "The downtown office provides secure bike storage spots on a first-come basis."),
    ("hr.employee_referral_bonus_usd", "People & Benefits", "Employee Referral Bonus", "2000",
     "Employees who refer a candidate later hired into a full-time role receive a referral bonus."),
    ("it.software_request_process_note", "IT & Security", "New Software Requests", "n/a",
     "Requests for new software licenses are submitted through the IT service desk for security review."),
    ("sales.territory_assignment_note", "Sales", "Territory Assignment", "n/a",
     "Sales territories are assigned by RevOps based on account list and geography at the start of each cycle."),
    ("finance.invoice_payment_terms_days", "Finance", "Vendor Invoice Payment Terms", "45",
     "Standard payment terms for approved vendor invoices are net-45 from receipt."),
    ("eng.design_doc_review_note", "Engineering", "Design Doc Review", "n/a",
     "Significant technical changes require a design doc reviewed by at least one staff engineer before work begins."),
    ("support.knowledge_base_owner_note", "Support", "Knowledge Base Ownership", "n/a",
     "The public knowledge base is jointly owned by support leadership and the technical writing team."),
    ("compliance.vendor_security_review_note", "Compliance", "Vendor Security Review", "n/a",
     "New vendors handling customer data undergo a security review before contract signature."),
    ("facilities.mail_room_hours", "Facilities", "Mail Room Hours", "9am-5pm weekdays",
     "The office mail room is staffed and accepts deliveries during standard business hours."),
    ("hr.performance_review_cadence", "People & Benefits", "Performance Review Cadence", "semi-annual",
     "Formal performance reviews are conducted on a recurring cadence between employees and managers."),
    ("it.incident_status_page_note", "IT & Security", "Status Page", "n/a",
     "Customer-facing service incidents are posted to the public status page by the on-call incident commander."),
    ("legal.data_processing_agreement_note", "Legal", "Data Processing Agreements", "n/a",
     "Enterprise customers may request a signed data processing agreement as part of contract negotiation."),
    ("sales.demo_environment_note", "Sales", "Demo Environment", "n/a",
     "Sales engineers maintain a shared demo environment refreshed with synthetic data on a recurring schedule."),
]


def chunk_header(chunk_id, entity_key, eff_date, supersedes):
    supersedes_str = supersedes if supersedes else "null"
    return f"<!-- chunk_id: {chunk_id} entity_key: {entity_key} effective_date: {eff_date} supersedes_id: {supersedes_str} -->"


def main():
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for f in CORPUS_DIR.glob("*.md"):
        f.unlink()

    registry = []
    docs = []  # (filename, [chunk_md, ...])
    signals = []
    n_chunks = 0

    def add_doc(filename, chunk_defs):
        """chunk_defs: [(chunk_id, entity_key, value, eff_date, supersedes, body)]"""
        nonlocal n_chunks
        parts = []
        for chunk_id, entity_key, value, eff_date, supersedes, body in chunk_defs:
            parts.append(f"{chunk_header(chunk_id, entity_key, eff_date, supersedes)}\n{body}")
            registry.append({"chunk_id": chunk_id, "entity_key": entity_key, "value": value,
                             "effective_date": eff_date, "supersedes_id": supersedes})
            n_chunks += 1
        docs.append((filename, "\n\n".join(parts)))

    # -- 1. ATOMIC --
    for slug, entity_key, value, eff_date, dept, title, body in ATOMIC:
        add_doc(f"{slug}.md", [
            (f"{slug}-c01", entity_key, value, eff_date, None, f"## {title}\n\n{body}"),
            (f"{slug}-c02", entity_key, value, eff_date, None,
             f"Documented under the {dept} section of the employee handbook. Current value: {value}."),
        ])

    # -- 2. CONTRADICTION --
    explicit_entity_keys, implicit_entity_keys = [], []
    threehop_entity_key = None
    for entity_key, dept, title, versions in CONTRADICTION:
        slug = entity_key.replace(".", "_")
        is_explicit = any(v[2] for v in versions)
        if len(versions) == 3:
            threehop_entity_key = entity_key
        elif is_explicit:
            explicit_entity_keys.append(entity_key)
        else:
            implicit_entity_keys.append(entity_key)
        for i, (value, eff_date, supersede_text) in enumerate(versions):
            vslug = f"{slug}_v{i+1}"
            supersedes_id = f"{slug}_v{i}-c01" if i > 0 else None
            heading = f"## {title}" + (" (Updated)" if i > 0 else "")
            intro = supersede_text if supersede_text else f"Current {title.lower()} for all eligible employees."
            add_doc(f"{vslug}.md", [
                (f"{vslug}-c01", entity_key, value, eff_date, supersedes_id, f"{heading}\n\n{intro}"),
                (f"{vslug}-c02", entity_key, value, eff_date, supersedes_id,
                 f"Current value: {value}. Documented under the {dept} section of the employee handbook."),
            ])

    # -- 3. NEAR_DUP --
    for (ek1, v1, d1, t1, b1, ek2, v2, d2, t2, b2) in NEAR_DUP:
        for ek, v, d, t, b in [(ek1, v1, d1, t1, b1), (ek2, v2, d2, t2, b2)]:
            slug = ek.replace(".", "_")
            add_doc(f"{slug}.md", [
                (f"{slug}-c01", ek, v, "2026-01-01", None, f"## {t}\n\n{b}"),
                (f"{slug}-c02", ek, v, "2026-01-01", None,
                 f"Documented under the {d} section of the employee handbook. Current value: {v}."),
            ])

    # -- 4. MULTI_HOP -- component facts, each a standalone 1-chunk doc
    multihop_meta = []
    for result_key, context, components, computed_value in MULTI_HOP:
        comp_ids = []
        for comp_key, comp_text, comp_value in components:
            slug = comp_key.replace(".", "_")
            cid = f"{slug}-c01"
            comp_title = comp_key.split(".")[-1].replace("_", " ").title()
            add_doc(f"{slug}.md", [(cid, comp_key, comp_value, "2026-01-01", None, f"## {comp_title}\n\n{comp_text}")])
            comp_ids.append(cid)
        multihop_meta.append({
            "result_entity_key": result_key, "context": context,
            "component_chunk_ids": comp_ids, "computed_value": computed_value,
            "n_hops": len(components),
        })

    # -- 5. MEMORY_CORRECTION -- stale corpus doc + registry holds BOTH values
    for entity_key, dept, title, stale_value, stale_date, corpus_body, true_value, signal_id, signal_text in MEMORY_CORRECTION:
        slug = entity_key.replace(".", "_")
        cid1, cid2 = f"{slug}-c01", f"{slug}-c02"
        add_doc(f"{slug}.md", [
            (cid1, entity_key, stale_value, stale_date, None, f"## {title}\n\n{corpus_body}"),
            (cid2, entity_key, stale_value, stale_date, None,
             f"Documented under the {dept} section of the employee handbook. Current value: {stale_value}."),
        ])
        # overwrite registry entries for this entity with BOTH values (stale + true)
        for r in registry:
            if r["chunk_id"] in (cid1, cid2):
                r["stale_documented_value"] = stale_value
                r["value"] = true_value  # oracle: the TRUE current value
        signals.append({"signal_id": signal_id, "entity_key": entity_key, "true_value": true_value,
                        "text": signal_text})

    # -- 6. Noise --
    for slug, dept, title, value, body in NOISE:
        add_doc(f"{slug}.md", [
            (f"{slug}-c01", slug, value, "2026-01-01", None, f"## {title}\n\n{body}"),
            (f"{slug}-c02", slug, value, "2026-01-01", None,
             f"Documented under the {dept} section of the employee handbook. Current value: {value}."),
        ])

    for filename, content in docs:
        (CORPUS_DIR / filename).write_text(content + "\n")

    (REPO / "data" / "fact_registry.json").write_text(json.dumps(registry, indent=1))
    (REPO / "data" / "correction_signals.json").write_text(json.dumps(signals, indent=1))
    (HERE / "multihop_meta.json").write_text(json.dumps(multihop_meta, indent=1))

    summary = {
        "generator_version": GENERATOR_VERSION,
        "n_docs": len(docs), "n_chunks": n_chunks,
        "n_atomic_entities": len(ATOMIC),
        "n_contradiction_entities": len(CONTRADICTION),
        "n_explicit_supersession": len(explicit_entity_keys),
        "n_implicit_supersession": len(implicit_entity_keys),
        "n_threehop_chains": 1 if threehop_entity_key else 0,
        "n_near_dup_pairs": len(NEAR_DUP),
        "n_multihop_entities": len(MULTI_HOP),
        "n_memory_correction_entities": len(MEMORY_CORRECTION),
        "n_noise_docs": len(NOISE),
        "n_correction_signals": len(signals),
    }
    print(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    main()
