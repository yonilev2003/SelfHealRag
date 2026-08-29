# PROCESS.md — temporal-discipline ledger

Append-only record of what was frozen when, and the SHA-256 digests that make
freeze claims verifiable independent of the co-located `.sha256` files (per
`PLAN.md` invariant #1/#2). Every entry is dated and, once committed, never
edited — corrections are new entries.

## Log

### 2026-08-28 — Phase 0 complete
- Archived `eval/generate.py`, `eval/BUSINESS_RULES.md`, `eval/data/pilot/`
  to `archive/ledgerguard-pretest/` (untouched, as generated/run).
  `results/pretest/` and `trajectories/pretest/` left in place (disclosure
  requirement — not reshuffled retroactively).
- Purged stale "micro1 Frontier Engineering Challenge / HackerEarth" framing
  from README.md and HANDOFF_PROMPT.md (this repo's actual event is the
  micro1 Agentic Workflows Hackathon per `CLAUDE.md`/`PROBLEM.md`).
- CHANGELOG.md rewritten with the real Stage-table structure and the
  LedgerGuard removed-experiment entry (real numbers, not placeholders).

### 2026-08-28 — Phase 1 build: live-fire finding on the Arm-B sandbox
While building `eval/sandbox_guard.py` (the PreToolUse path-containment hook
for Arm B, PLAN.md invariant #1), a live smoke test surfaced a real gap
**before** it could reach the frozen corpus: with only `allowed_tools=["Read",
"Grep","Glob"]` set (no `disallowed_tools`), a real agent session
successfully invoked `Bash({'command': 'pwd; ls'})` — `allowed_tools` is a
*pre-approval allowlist*, not a hard restriction; unlisted tools still ran
under the default (unset) permission mode. Our PreToolUse hook only inspects
`file_path`/`path`/`pattern` keys, so a live Bash call would have bypassed it
entirely (`cat`, `find`, arbitrary shell). **Fix:** `disallowed_tools=["Bash",
"Write","Edit","MultiEdit","NotebookEdit","WebFetch","WebSearch","Task",
"ToolSearch"]` added explicitly to Arm B's options — re-verified live: the
same prompt that previously ran Bash now correctly reports no Bash tool is
available. `eval/test_sandbox_guard.py` (7 unit cases) covers the hook's own
path logic; this finding is about the SDK's tool-gating semantics, which no
unit test of the hook alone would have caught — logged here as the reason
`disallowed_tools` is load-bearing, not redundant, in the final Arm-B config.

### 2026-08-28 — Phase 2: corpus/probes/split FROZEN

**What a good result looks like for the intended user (E2 — written BEFORE
any scored run):** an SMB data/analytics team lead should be able to trust
that when a policy fact changes — whether the handbook was updated
(supersession) or not yet (a diagnosed-but-undocumented correction) — the
system's answer reflects the CURRENT truth, with a citation the lead can
verify in one click. A good result means: (a) on `contradiction`/`near_dup`/
`multi_hop`/`atomic` cases, at least matching what a careful single agent
with basic tools already achieves (per Phase 1, that bar is high — near
6/6); (b) on `memory_correction` cases, categorically beating every
baseline, since no baseline can access the correction signal at all — this
is the category the whole rev-4 retarget is built to win, and where the
primary metric's real signal lives.

**Realized corpus (vs. PLAN.md rev-4 estimates, deviations documented, not
hidden):** 81 docs / 153 chunks (vs. the ~34/248 estimate — smaller,
deliberately: the memory-correction proof is categorical, not scale-
dependent, per the Phase-1 finding, so a leaner corpus keeps the budget
comfortable without weakening the claim). 8 explicit-supersession entities
(not 9) + 3 implicit + 1 three-hop chain = 12 contradiction entities,
matching the total even though the explicit/implicit split differs by one
from the original estimate. Probe authoring was hand-crafted, not
Claude-paraphrased (PLAN.md's original wording) — a disclosed, deliberate
choice for determinism and precision under the event's time budget.

**Artifacts + hashes (independently re-verifiable, per `eval/split_summary.json`):**
- `data/fact_registry.json` — sha256 `1bcba7da822d099558eaae5f15471e22422d344d6c6eb99151f9435d629e5624`
- `data/probes/dev_split.json` (24 cases) — sha256 `f0ed240d6c870177459d519361b759d187f1ef677d80f8770f85f122fcc05c02`
- `data/probes/test_split.locked.json` (16 cases) — sha256 `a420693954f0ecba9cdfb07d25c98845dd04ca343a31c4092d4d7a995e358dd9`
- `data/correction_signals.json` — 8 entries, one per `memory_correction` entity, never read by any baseline arm.

**Split by category (dev/test):** atomic 5/3, contradiction 7/5 (3 implicit
+ the 3-hop chain forced into test, per invariant #3), near_dup 5/3,
multi_hop 2/2 (the 3-hop forced into test), memory_correction 5/3.
dev ∩ test = ∅ and dev ∪ test = all 40 probes, asserted in
`eval/split_and_lock.py` and re-verified above.

**Hero case (pre-registered by construction, per invariant #2):**
`memory_correction-01` (`eng.oncall_stipend_usd`) — the Engineering
on-call weekly stipend, corpus states $200 (stale), true current value
$250 per `TICKET-4521`, discoverable only in `correction_signals.json`.

**Structural novelty note:** every probe targets a distinct entity (no
paraphrase-pairs per entity in this design) — so every category held out
to test (implicit supersession, both 3-hop mechanics, the entire
memory_correction category) is, by construction, an entity the Phase-4
tuning loop never touches in dev. This satisfies invariant #3's intent
(structurally novel test cases) via entity-level held-out-ness rather than
paraphrase-level held-out-ness — noted as a deviation from PLAN.md's exact
wording, not silently substituted.

**`all_probes.json`** was never committed to git — written only to the
session scratchpad by `generate_probes.py`, per invariant #1's rev-3 fix.

**No solution code exists at this commit** (`advanced/`, `baseline/` are
still empty aside from the Phase-1 pretest scaffolding already archived).

*(Phase 3+ entries are appended here as each phase completes — never
backfilled from memory.)*
