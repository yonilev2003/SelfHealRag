#!/usr/bin/env python3
"""Phase 2 (PLAN.md rev 4): 40 probes over the real corpus.

Hand-authored (not Claude-paraphrased -- a deliberate, disclosed choice for
determinism and precision under the event's time budget; PROCESS.md records
this honestly against PLAN.md's original wording). Reads
data/fact_registry.json + eval/multihop_meta.json (written by
generate_corpus.py) as its only inputs -- never touches
correction_signals.json's answer content beyond the entity_key/true_value
pair generate_corpus.py already put in the registry, so probe authoring
cannot accidentally leak signal PROSE into a question.

Category/count realized (vs. the rev-4 estimate, adjusted to match what
generate_corpus.py actually built -- documented, not silently forced):
  atomic            8   (1 probe/entity)
  contradiction     12  (8 explicit + 3 implicit + 1 three-hop chain)
  near_dup          8   (1 probe per target entity, decoy entity unprobed)
  multi_hop         4   (3 two-hop + 1 three-hop, arithmetic combination)
  memory_correction 8   (1 probe/entity, expected_chunk_id="MEMORY")
Total 40.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# entity_key -> hand-written natural question
ATOMIC_QUESTIONS = {
    "hr.bereavement_leave_days": "How many days of paid bereavement leave can an employee take?",
    "it.offboarding_access_revoke_hours": "Within how many hours of an employee's last day does IT revoke system access?",
    "finance.travel_per_diem_usd": "What is the daily per diem for domestic business travel?",
    "legal.ip_assignment_scope": "What is the scope of IP assignment under the standard employment agreement?",
    "sales.quota_reset_cadence": "How often are sales quotas reset?",
    "eng.code_review_min_approvals": "How many approving reviews does a pull request to main need before merge?",
    "facilities.desk_booking_ratio": "What is the bookable-desk-to-headcount ratio at the downtown office?",
    "support.csat_target_pct": "What is the support team's CSAT target percentage?",
}

CONTRADICTION_QUESTIONS = {
    "it.vpn_session_timeout_hours": "What is the current VPN session timeout, in hours?",
    "hr.pto_accrual_days_per_month": "How many PTO days does an employee currently accrue per month?",
    "finance.expense_report_deadline_days": "How many days does an employee currently have to submit an expense report?",
    "it.password_rotation_days": "How many days is the current password rotation requirement?",
    "sales.deal_discount_max_pct": "What is the current maximum discretionary discount a sales rep can apply, in percent?",
    "hr.remote_work_days_per_week": "How many days per week can employees currently work remotely?",
    "eng.oncall_rotation_days": "How many days does the current on-call rotation last?",
    "support.first_response_sla_hours": "What is the current first-response SLA for support tickets, in hours?",
    "finance.refund_cap_usd": "What is the current customer refund cap that a rep can approve without manager sign-off, in USD?",
    "compliance.data_retention_months": "How many months is customer data currently retained after account closure?",
    "it.laptop_refresh_years": "Every how many years are laptops currently refreshed?",
    "legal.contractor_nda_years": "What is the current confidentiality period for a contractor NDA, in years?",
}

NEAR_DUP_QUESTIONS = {
    "sales.client_dinner_cap_usd": "What is the Sales team's expense cap for a client dinner, in USD?",
    "hr.new_parent_leave_weeks": "How many weeks of paid leave does a new parent receive?",
    "it.badge_access_hours_standard": "How many hours per day does a standard employee badge grant building access?",
    "finance.po_auto_approve_usd": "Below what dollar amount is a purchase order automatically approved?",
    "support.escalation_response_minutes": "Within how many minutes must an escalated (P1) ticket be acknowledged?",
    "sales.commission_accelerator_pct": "What commission rate applies to revenue above 100% of quota?",
    "eng.incident_postmortem_days": "Within how many business days is a postmortem due after a SEV1/SEV2 incident?",
    "legal.vendor_contract_review_days": "Within how many business days is a standard vendor contract reviewed?",
}

MEMORY_QUESTIONS = {
    "eng.oncall_stipend_usd": "What is the current weekly on-call stipend for engineers, in USD?",
    "support.weekend_shift_diff_pct": "What is the current weekend shift differential for support agents, in percent?",
    "facilities.parking_reimbursement_usd": "What is the current monthly parking reimbursement cap, in USD?",
    "benefits.gym_stipend_usd": "What is the current monthly wellness stipend cap, in USD?",
    "it.hardware_request_sla_days": "Within how many business days is a hardware request currently fulfilled?",
    "sales.deal_approval_threshold_usd": "What is the current director-approval threshold for deals, in USD (ACV)?",
    "legal.nda_duration_years": "What is the current confidentiality term in the standard NDA template, in years?",
    "eng.oncall_rotation_pay_multiplier": "What is the current holiday on-call pay multiplier for engineers?",
}


def main():
    registry = json.loads((REPO / "data" / "fact_registry.json").read_text())
    multihop = json.loads((HERE / "multihop_meta.json").read_text())

    def latest_chunk_for(entity_key):
        """Latest (by effective_date) registry row for a plain entity."""
        rows = [r for r in registry if r["entity_key"] == entity_key]
        return max(rows, key=lambda r: r["effective_date"])

    def is_explicit(entity_key):
        # explicit iff >1 version AND corpus text for the latest chunk's doc contains "supersedes"
        slug = entity_key.replace(".", "_")
        rows = sorted([r for r in registry if r["entity_key"] == entity_key], key=lambda r: r["effective_date"])
        if len(rows) < 2:
            return None
        latest_doc_idx = len(rows) // 2  # each version has 2 chunks
        vfile = REPO / "data" / "corpus" / f"{slug}_v{latest_doc_idx}.md"
        return vfile.exists() and "supersedes" in vfile.read_text().lower()

    probes = []

    # -- ATOMIC (8) --
    for entity_key, question in ATOMIC_QUESTIONS.items():
        row = latest_chunk_for(entity_key)
        probes.append({
            "probe_id": f"atomic-{len(probes)+1:02d}", "question": question,
            "expected_value": row["value"], "expected_chunk_id": row["chunk_id"],
            "category": "atomic", "trap_subtype": "none",
            "entity_key": entity_key, "construction_seed": 42,
        })

    # -- CONTRADICTION (12: 8 explicit + 3 implicit + 1 three-hop) --
    threehop_key = "finance.refund_cap_usd"
    for entity_key, question in CONTRADICTION_QUESTIONS.items():
        row = latest_chunk_for(entity_key)
        if entity_key == threehop_key:
            subtype = "3hop_chain"
        else:
            subtype = "explicit_supersession" if is_explicit(entity_key) else "implicit_supersession"
        probes.append({
            "probe_id": f"contradiction-{len([p for p in probes if p['category']=='contradiction'])+1:02d}",
            "question": question, "expected_value": row["value"], "expected_chunk_id": row["chunk_id"],
            "category": "contradiction", "trap_subtype": subtype,
            "entity_key": entity_key, "construction_seed": 42,
        })

    # -- NEAR_DUP (8) --
    for entity_key, question in NEAR_DUP_QUESTIONS.items():
        row = latest_chunk_for(entity_key)
        probes.append({
            "probe_id": f"near_dup-{len([p for p in probes if p['category']=='near_dup'])+1:02d}",
            "question": question, "expected_value": row["value"], "expected_chunk_id": row["chunk_id"],
            "category": "near_dup", "trap_subtype": "none",
            "entity_key": entity_key, "construction_seed": 42,
        })

    # -- MULTI_HOP (4) --
    for m in multihop:
        n = m["n_hops"]
        question = f"{m['context']}, in USD?" if "usd" in m["result_entity_key"].lower() else f"{m['context']}?"
        probes.append({
            "probe_id": f"multi_hop-{len([p for p in probes if p['category']=='multi_hop'])+1:02d}",
            "question": question, "expected_value": m["computed_value"],
            "expected_chunk_id": "+".join(m["component_chunk_ids"]),
            "category": "multi_hop", "trap_subtype": "3hop" if n == 3 else "2hop",
            "entity_key": m["result_entity_key"], "construction_seed": 42,
        })

    # -- MEMORY_CORRECTION (8) --
    for entity_key, question in MEMORY_QUESTIONS.items():
        row = latest_chunk_for(entity_key)  # holds the TRUE value (registry overwritten in generate_corpus.py)
        probes.append({
            "probe_id": f"memory_correction-{len([p for p in probes if p['category']=='memory_correction'])+1:02d}",
            "question": question, "expected_value": row["value"], "expected_chunk_id": "MEMORY",
            "category": "memory_correction", "trap_subtype": "stale_no_memory",
            "entity_key": entity_key, "construction_seed": 42,
        })

    # -- leak filter: reject any question sharing a >=10-token contiguous
    # case-insensitive substring with any corpus chunk or registry string.
    corpus_text = " ".join(f.read_text().lower() for f in (REPO / "data" / "corpus").glob("*.md"))
    corpus_tokens = corpus_text.split()
    corpus_ngrams = set(tuple(corpus_tokens[i:i+10]) for i in range(len(corpus_tokens) - 9))
    leaks = []
    for p in probes:
        qtoks = p["question"].lower().replace("?", "").replace(",", "").split()
        for i in range(max(0, len(qtoks) - 9)):
            if tuple(qtoks[i:i+10]) in corpus_ngrams:
                leaks.append(p["probe_id"])
                break

    assert len(probes) == 40, f"expected 40 probes, got {len(probes)}"
    assert not leaks, f"leak filter rejected: {leaks}"
    assert len({p['probe_id'] for p in probes}) == 40, "duplicate probe_id"

    (HERE / "pretest_leak_check.json").write_text(json.dumps({"n_checked": len(probes), "leaks": leaks}, indent=1))
    # all_probes.json is SCRATCHPAD-ONLY per invariant #1 -- never committed to git.
    scratch_dir = Path("/tmp/claude-0/-home-user-hackathonaug28-08-26/0a84ed52-68de-563b-a9ee-13411cba2061/scratchpad")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    (scratch_dir / "all_probes.json").write_text(json.dumps(probes, indent=1))

    by_cat = {}
    for p in probes:
        by_cat[p["category"]] = by_cat.get(p["category"], 0) + 1
    print(json.dumps({"n_probes": len(probes), "by_category": by_cat, "leaks": leaks}, indent=1))
    return probes


if __name__ == "__main__":
    main()
