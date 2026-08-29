# V3 narration script — final, claim-audited

Audited chapter-by-chapter on 2026-08-29 against `REVIEW_FINDINGS.md`,
`advanced/*.py`, the baseline arm scripts, `results/ablations_summary.json`,
`results/results_table.json`, `README.md`, and `PRODUCTION_ROADMAP.md`. This
file is the source of truth for narration text — supersedes the copy in
`HANDOFF_PROMPT.md`. Changes vs. the pre-audit draft: Ch3 (dropped
"unrestricted... for as long as it wants" — Arm B is capped at 25 turns/8min),
Ch4 (dropped "not a lookup trick"; round 2: "continuously" -> "on each
query", since the check fires synchronously per query, not as a background
daemon), Ch5 (round 1 dropped "here it catches"; round 2: fully reframed as
a negative-result/evaluation-discipline story — the verifier is `use_verifier:
false` in the shipped `advanced/final_config.json`, and changed ZERO outputs
across every `results/C_*.json` file including the explicit ON ablation, so
narration now says exactly that instead of "always on"), Ch6 (scoped "that's
the entire difference" to the memory-correction category explicitly), Ch9
(round 1 dropped "knows when its own knowledge has expired"; round 2:
"proves the mechanism works" -> "demonstrates the mechanism on the frozen
evaluation" — n=3 confidence without overclaiming "proof"). Ch1, Ch2, Ch7,
Ch8 unchanged — audited clean both rounds.

Voice: Joel — "Natural and reassuring" (`6iwCQ4DWhL4B28msWWW8`, `eleven_v3`).
Picked on ElevenLabs' own voice metadata (warm/grounded/trust-and-authenticity
framing), confirmed acceptable by the user against the 10s test sample.
Locked — no further voice search.

---

**Chapter 1 — `beat0_hook.mp3`** (~12s)
> Your company changed the price to two hundred fifty dollars. Yesterday.
> [pause] Your AI still confidently tells every employee... two hundred.

**Chapter 2 — `beat1_evidence.mp3`** (~18s)
> Here's the evidence. On the left, the handbook — still says two hundred.
> On the right, the finance ticket that actually approved the raise — two
> hundred fifty. [pause] Nobody updated the handbook.

**Chapter 3 — `beat2_baselines.mp3`** (~24s)
> Two strong baselines. Same wrong answer. [pause] Full context — every
> document, one call — still two hundred. An agent free to search and read
> across those same documents, however it likes — also two hundred. [pause]
> More reading doesn't fix this, because the right answer simply isn't
> written down anywhere in the documents.

**Chapter 4 — `beat3_selfheal.mp3`** (~36s, 3 `[pause]` tags — timing follows
sub-reveal: wait-dots +5s, JSON reveal +12s, final answer +20s from beat start)
> Now watch what happens differently. [pause] The entity isn't in memory
> yet — so instead of guessing, SelfHeal checks a signal feed no baseline
> ever gets: a stand-in for the ticket system this bot was never connected
> to. [pause] Found it. Ticket 4521. Writing it to memory, right now, live.
> [pause] Final answer: two hundred fifty, cited as memory. This check
> runs on each query — not just once, during tuning.

**Chapter 5 — `beat4_verifier.mp3`** (~26s, reframed as evaluation
discipline, not a claimed contribution — verifier is OFF in
`advanced/final_config.json` and changed zero outputs on all 16 frozen-test
cases, confirmed across every `results/C_*.json` incl. the explicit
verifier-ON ablation)
> I also built a deterministic verifier for stale citations. [pause] No
> model call, no guessing. On this targeted revision case, it correctly
> replaces the stale citation with the current one. [pause] But here's the
> important part: on the frozen sixteen-case evaluation, it changed
> exactly zero outputs. So it's disabled in the shipped accuracy
> configuration. [pause] Not every component earns its place.

**Chapter 6 — `beat5_frozentest.mp3`** (~27s)
> Here's the proof, on sixteen test cases the system never saw during
> development. [pause] Every baseline: zero out of three, on the
> memory-correction category this was built for. SelfHeal: three for
> three. [pause] Flip memory off, change nothing else — back to zero, on
> those same three cases. One capability. For this category, that's the
> entire difference.

**Chapter 7 — `beat6_scale.mp3`** (~20s, unchanged)
> Think about the scale for a second. One employee getting the wrong number
> is an annoyance. [pause] Ten thousand employees getting it — that's not a
> bug anymore. That's an operating-system problem for your company's own
> knowledge.

**Chapter 8 — `beat7_lesson.mp3`** (~30s, unchanged — strongest chapter,
matches CHANGELOG.md's Hot Take almost verbatim)
> The first time I ran this frozen test, SelfHeal tied the baseline. Zero
> out of three, on the exact case it was built for. Not a crash — just a
> quiet, forgettable number, the kind you could rationalize away under
> deadline pressure. [pause] The bug: memory only ever learned from
> training-time data, never from what it was actually being asked, live.
> [pause] A good held-out test doesn't just measure whether you generalize
> — it catches you lying to yourself about scope. Silently.

**Chapter 9 — `beat8_closing.mp3`** (~27s, vision-framed)
> A RAG system that retrieves information is useful. [pause] A system that
> can recover when what it retrieves is contradicted by a newer signal —
> that's something I'd actually trust inside a company. [pause] The
> production vision is broader: organizational memory that can reason
> about versions, permissions, and conflicting knowledge. That part isn't
> built yet. This is the prototype that demonstrates the mechanism on the
> frozen evaluation.

---

Total ~240s provisional (word-count estimate) — replaced with real measured
durations once ElevenLabs generation completes; `video/beats.html`'s `beats`
array timeline gets trued up from provisional to real at that point.
