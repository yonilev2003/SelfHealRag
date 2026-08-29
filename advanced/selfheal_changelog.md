# SelfHeal RAG — self-improvement changelog (written by the loop itself)

## Round 0 (baseline config {'k': 3, 'hybrid_date_boost': False, 'use_verifier': False, 'use_memory': True})
- accuracy: 17/24
- failures by category: {'retrieval_miss': 2, 'memory_correction_missed': 5}

  - Wrote memory correction for `benefits.gym_stipend_usd` = '100' (source: TICKET-5108), motivated by dev case(s) ['memory_correction-04'].
  - Wrote memory correction for `it.hardware_request_sla_days` = '2' (source: AUDIT-1147), motivated by dev case(s) ['memory_correction-05'].
  - Wrote memory correction for `sales.deal_approval_threshold_usd` = '75000' (source: TICKET-2287), motivated by dev case(s) ['memory_correction-06'].
  - Wrote memory correction for `legal.nda_duration_years` = '5' (source: AUDIT-0764), motivated by dev case(s) ['memory_correction-07'].
  - Wrote memory correction for `eng.oncall_rotation_pay_multiplier` = '2.0x' (source: TICKET-4890), motivated by dev case(s) ['memory_correction-08'].
## Round 1 — KEPT
- plurality: memory_correction_missed
- action: consulted the correction-signal feed for 5 case(s), wrote 5 new memory entries
- dev accuracy: 21/24 (delta +4 vs previous 17)
- new config: {'k': 3, 'hybrid_date_boost': False, 'use_verifier': False, 'use_memory': True}

## Round 2 — REVERTED
- plurality: retrieval_miss
- action tried: k 3 -> 5
- dev accuracy with change: 22/24 (delta +1, below the +2 keep threshold)
- config unchanged: {'k': 3, 'hybrid_date_boost': False, 'use_verifier': False, 'use_memory': True}

## Round 3 — REVERTED
- plurality: retrieval_miss
- action tried: k 3 -> 5
- dev accuracy with change: 22/24 (delta +1, below the +2 keep threshold)
- config unchanged: {'k': 3, 'hybrid_date_boost': False, 'use_verifier': False, 'use_memory': True}


## Final
- final config: {'k': 3, 'hybrid_date_boost': False, 'use_verifier': False, 'use_memory': True}
- final dev accuracy: 21/24
- rounds run: 3
