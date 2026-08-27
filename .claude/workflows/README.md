# Agent workflows

These are `Workflow`-tool scripts (Claude Code), not shell scripts — invoke them
from inside a Claude Code session, not from a terminal. See `CLAUDE.md` for when
to use which.

- `hackathon-sprint.js` — full understand → plan → baseline → verify → advanced →
  verify → document pipeline. Run once, right after the problem drops:
  ```
  Workflow({ name: "hackathon-sprint", args: { problemPath: "PROBLEM.md" } })
  ```
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
