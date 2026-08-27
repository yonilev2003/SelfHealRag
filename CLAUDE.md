# Project context for Claude Code

## What this is
Solo submission for the micro1 Frontier Engineering Challenge (Aug 28–31 2026,
HackerEarth). The problem is unknown until kickoff — replace this section with the
actual problem statement the moment it drops, and keep it in sync as understanding
evolves. Paste (or link) the full problem statement into `PROBLEM.md` as soon as
it's released — the agent workflows below read it from there by default.

## Working mode
- Direction and the calls that matter come from me; you drive ~99% of the execution.
  Default to acting, not asking — except at the one gate below.
- Every solution exists in two versions: `baseline/` (first correct pass) and
  `advanced/` (measurable improvement, not a cosmetic diff). Don't collapse them
  into a single implementation.
- Every improvement claim needs a number from `eval/score.py`. "Better" isn't a
  claim — a delta is.
- Log each baseline→advanced decision in CHANGELOG.md as it's made, not
  reconstructed from memory at the end.

## The one hard gate
`.claude/settings.json` runs a PreToolUse hook that asks for confirmation before
anything that looks like a deploy/publish/release. Everything else should run
without stopping to ask — the point is speed everywhere except that one moment.

## Repo conventions
- `scripts/setup.sh`, `run_baseline.sh`, `run_advanced.sh`, `collect_trajectories.sh`
  are the only entry points — keep them working at every commit, so a stranger can
  reproduce this cold with `make setup && make baseline && make advanced && make eval`.
- Trajectories capture from Claude Code's own session logs — don't hand-edit
  `trajectories/raw/*.jsonl`.

## Agent workflows (the actual engineering process, not just the code)
`.claude/workflows/` holds two Workflow-tool scripts that encode how this entry is
meant to be built — this *is* the "Agent Solution & Engineering" artifact, not
incidental tooling, so keep it truthful to what actually ran:

- **`hackathon-sprint`** — the full pipeline for once the problem is known:
  extract requirements from `PROBLEM.md` → judge-panel over candidate baseline
  approaches → implement `baseline/` → multi-lens adversarial verify → judge-panel
  over improvement directions → implement `advanced/` → multi-lens adversarial
  verify + regression check → fill in `eval/score.py` and run it → write up
  `CHANGELOG.md`/`README.md`. Invoke once, right after kickoff, with
  `Workflow({name: "hackathon-sprint", args: {problemPath: "PROBLEM.md"}})`.
- **`hackathon-fix`** — a lighter loop-until-dry bug-hunt for mid-sprint iteration:
  parallel bug-hunters over `baseline/` or `advanced/`, each finding adversarially
  refuted before being fixed, looping until two consecutive rounds turn up nothing
  new. Use this instead of re-running the full sprint pipeline for a targeted round
  of hardening. `Workflow({name: "hackathon-fix", args: {target: "advanced",
  context: "eval says X is still failing on Y"}})`.

Both are pre-kickoff scaffolding: the phases and schemas are real, but the prompts
are necessarily generic until the actual problem is known. Adjust wording (not the
overall shape) once `PROBLEM.md` is filled in, if the problem calls for it.

See `TOOLKIT.md` for the fuller decision tree — which tool/skill/workflow fits a
given situation mid-sprint, not just these two entry points. If a new session is
picking this up cold, `HANDOFF_PROMPT.md` has the paste-ready context.

## What's being judged
Correct → Reproducible → Testable → Clearly explained.
Tie-break order: Agent Solution & Engineering → Reproducibility → Measured
Improvement → End-to-End Quality. Agent-driven engineering is the #1 tie-break
criterion — this file and the trajectory disclosure aren't overhead, they're part
of the entry.
