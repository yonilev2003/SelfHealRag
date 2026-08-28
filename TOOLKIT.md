# Toolkit — which tool for which situation

A decision tree for the 3-day window, keyed to what you're actually trying to do
right now. Written for whichever agent session is driving at the time — this file
plus `CLAUDE.md` is meant to be enough context to pick up mid-sprint with no other
memory.

## Kickoff — getting the problem into the repo

- Problem arrives as a PDF → use the **`pdf`** skill to extract the full text
  (and any tables — constraints, scoring rubrics, sample I/O are often tabular).
  Don't summarize by eye; extract completely, then paste into `PROBLEM.md`.
- Problem arrives as plain text/a webpage → paste directly into `PROBLEM.md`, no
  skill needed.
- Starter materials/datasets linked from the PDF → pull them down before running
  the sprint workflow, so the `Understand` phase can actually read them.
- Once `PROBLEM.md` is filled in: `Workflow({ name: "hackathon-sprint", args: {
  problemPath: "PROBLEM.md", stopAfter: "plan" } })` — see
  `.claude/workflows/README.md` for the checkpoint flow.

## Planning & judgment calls

- A decision only a human can make (scope tradeoff, which of two valid readings
  of an ambiguous requirement to take) → `AskUserQuestion`. Don't use it for
  things you can reasonably decide yourself — the whole point of this setup is
  speed everywhere except the one hard gate (see below).
- Need docs for an unfamiliar library/API → `WebSearch` / `WebFetch`.
- Need to check what's available beyond the core toolset (GitHub, Hugging Face,
  a deploy target, etc.) → `ToolSearch` with a relevant keyword before assuming
  something isn't possible.
- **Creativity/business-value is genuinely at risk of being under-exercised** —
  everything pre-kickoff is process/tooling, not product judgment. That's why
  `hackathon-sprint.js`'s Advanced Ideation reserves a seat for a deliberately
  creative/differentiated idea (not just technical variety) and scores every
  idea partly on how well it serves `requirements.intendedUser`'s actual
  bottleneck, not just a technical metric.
- **"Grill" panels** — 3 independent skeptics, each told to find the strongest
  reason a decision is wrong (not to agree), majority-vote whether to flag it.
  Applied to the two consequential picks in `hackathon-sprint.js` (which
  baseline approach, which advanced direction) — not blanket-applied to every
  prompt, since grilling implementation-detail writes (README wording, changelog
  prose) would multiply cost without adding real scrutiny. `hackathon-fix.js`
  runs a lighter, single-agent version of this once per bug-hunt round
  (interrogating the round's own thoroughness, not just the bugs it found).
  A "MAJORITY SAYS RECONSIDER" log line is a real signal, not noise — read it
  at the `stopAfter` checkpoint, don't just skim past it.
- **Competitor comparison** — deliberately not built pre-kickoff: there's
  nothing concrete to compare against yet, and this is an individual event (no
  visibility into other entrants' private submissions). Once the real problem
  is known, a lightweight version is straightforward to add: a `WebSearch`-based
  agent surveying public writeups of similar past agentic-hackathon problems to
  flag "this is the obvious/expected solution" before committing engineering
  time to it — wire it in as an extra Advanced Ideation angle if it seems worth
  the cost once there's an actual problem to react to.

## Implementation

- Baseline/advanced build + verify, start to finish → `hackathon-sprint` workflow
  (full run, or resumed from a `stopAfter` checkpoint).
- Targeted bug hunt mid-sprint — eval regressed, a judge-simulated edge case
  failed, or just want another hardening pass without redoing everything →
  `hackathon-fix` workflow (`args: { target: "baseline"|"advanced", context }`).
- A one-off research/exploration task that doesn't need full multi-agent
  orchestration (e.g. "where in this codebase does X happen") → `Agent` tool
  directly (`Explore` for pure search, `general-purpose` otherwise).
- Post-implementation cleanup (reuse, simplification, efficiency) → `simplify`
  skill. Deeper correctness/bug review → `code-review` skill.
- Anything touching credentials, user data, or external input parsing →
  `security-review` skill before calling it done — the Rule Book requires
  treating people/data responsibly, and this is graded, not just good hygiene.

## Running & verifying

- See it actually work (browser, CLI, whatever the problem calls for) → `run`
  skill.
- Local reproduction check → `make setup && make baseline && make advanced &&
  make eval` — the exact sequence CI runs on every push.
- Confirm reproducibility from a genuinely clean state, not just "it ran once
  in this container" → the `reproducibility` lens inside `hackathon-sprint.js`'s
  Baseline Verify phase already does this (clean caches/venvs, re-run from
  scratch); re-run it manually if something about the environment changed.

## Documentation & submission

- A results chart/comparison worth showing → `dataviz` skill for the visual
  design, then `Artifact` to publish it if it's worth a link (e.g. in the video
  or README) rather than a static image.
- `CHANGELOG.md` → update as each baseline→advanced decision is made, per
  `CLAUDE.md` — not reconstructed from memory at the end. This file is graded
  directly ("Measured Improvement", "Clearly explained").
- Trajectories → `make trajectories` periodically through the sprint, not just
  once at the end, so nothing is lost if the session changes or crashes.
- Video (≤5 min) → nothing in this environment records screen/audio. Use
  `VIDEO_SCRIPT.md` as the shot list and record locally, once the real numbers
  exist to show.

## Guardrails (apply throughout)

- Anything that looks like deploy/publish/release triggers a confirmation
  prompt (`.claude/hooks/guard_deploy.py`) — expected behavior, not a bug; it's
  a deliberate friction point per `CLAUDE.md`.
- Stuck on the same error after 2 failed fix attempts → stop, show the real
  error log, and ask instead of trying a 3rd variation alone (see `CLAUDE.md`
  → Hard gates). Applies inside workflow runs too, not just interactively.
- Never hand-edit `trajectories/raw/*.jsonl` — copy-only, so disclosure stays
  faithful to what actually ran.
- Secrets: local `.env` (gitignored) + GitHub repo secrets in CI — see
  `.env.example` and the comment in `scripts/setup.sh`.
- Every improvement claim needs a number from `eval/score.py`. If `CRITERIA` is
  still empty, `make eval` always reports delta 0 — filling it in with real,
  independently-testable checks derived from the problem's acceptance criteria
  is part of Advanced Implement, not an afterthought.
