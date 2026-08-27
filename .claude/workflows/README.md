# Agent workflows

These are `Workflow`-tool scripts (Claude Code), not shell scripts — invoke them
from inside a Claude Code session, not from a terminal. See `CLAUDE.md` for when
to use which.

- `hackathon-sprint.js` — full understand → plan → baseline → verify → advanced →
  verify → document pipeline. Run once, right after the problem drops:
  ```
  Workflow({ name: "hackathon-sprint", args: { problemPath: "PROBLEM.md" } })
  ```
  For a manual sanity check before the run commits to a direction (worth doing on
  a 3-day clock, where a wrong early call is expensive to discover late), pass
  `stopAfter: "plan"` (stops after the approach is picked, before any code is
  written) or `stopAfter: "baseline"` (stops after baseline is implemented and
  verified, before Advanced Ideation starts). Look at what it produced, then
  re-invoke with `Workflow({ scriptPath, resumeFromRunId })` and no `stopAfter`
  (or the next one) to continue — everything up to the stop point replays from
  cache instantly, nothing reruns.
- `hackathon-fix.js` — loop-until-dry bug-hunt + adversarial-verify for a targeted
  hardening pass mid-sprint, instead of re-running the whole pipeline:
  ```
  Workflow({ name: "hackathon-fix", args: { target: "advanced", context: "eval says X is still failing on Y" } })
  ```

Both scripts are pre-kickoff scaffolding: the phase structure, judge-panel /
adversarial-verify patterns, and JSON schemas are real and ready to run, but the
prompt wording is necessarily generic since the actual problem isn't known yet.
Once `PROBLEM.md` is filled in, skim the prompts and tighten wording if the
specific problem calls for it — the shape of the pipeline shouldn't need to change.

This session's workflow-size guideline (see `/config` → "Dynamic workflow size")
controls concurrency and default panel sizes; both scripts default to small
(2-way) judge panels to stay reasonable under the default "medium" guideline —
widen them (e.g. 3-5 candidates) if the sprint budget allows more thoroughness.

**Model/context:** neither script hardcodes a model (no `opts.model` on any
`agent()` call), so every sub-agent inherits whatever model/effort this session is
actually running — no adjustment needed if the problem turns out to be long or
unusually hard. Large inputs (a big `PROBLEM.md`, attached data files) are also
already handled by construction: each `agent()` call reads files itself with its
own tools, and only small structured JSON summaries (the schemas defined at the
top of each script) get threaded between phases — raw problem text/data never
gets inlined into a downstream prompt.

**Timeouts:** the `agent()`/`parallel()` primitives don't expose a per-call
timeout, so there's no knob to bound one sub-agent's runtime directly. What is
bounded: `hackathon-fix.js` has a hard `MAX_ROUNDS` ceiling regardless of
convergence, `hackathon-sprint.js` is a fixed number of phases with no loops, and
`.github/workflows/ci.yml` has `timeout-minutes` so a hung CI run can't burn the
whole window. If a single `agent()` call is taking too long interactively, use
`TaskStop`/`/workflows` to cancel and re-invoke with a narrower prompt.
