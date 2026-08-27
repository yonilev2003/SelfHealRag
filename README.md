# micro1 Frontier Engineering Challenge — [fill in problem name after kickoff]

Solo entry for the [micro1 Frontier Engineering Challenge 2026](https://www.hackerearth.com/community/challenges/hackathon/micro1-frontier-engineering-challenge-2026/) (HackerEarth), Aug 28–31, 2026.

## Event facts

| | |
|---|---|
| Window | Aug 28, 18:00 IL time → Aug 31, 02:59 IL time |
| Theme | Creativity (problem released at kickoff) |
| Format | Individual, online, judged on the work — not background/institution/employer |
| Judging | Correct → Reproducible → Testable → Clearly explained |
| Tie-break order | Agent Solution & Engineering → Reproducibility → Measured Improvement → End-to-End Quality |

## What's pre-built vs. built during the window

Everything up to the `pre-kickoff` git tag is scaffolding written *before* the problem
was released: environment, standard commands, the deploy-confirmation hook, the shape
of the scoring harness, the CI workflow, and the agent Workflows that drive the actual
build. None of it solves the actual problem — it couldn't, since the problem wasn't
known yet. Everything after that tag, under `baseline/` and `advanced/`, was written
during the 3-day window. This split is what the Rule Book asks for ("make clear what
existed before and what you added").

## Structure

```
.
├── baseline/                    # first correct, working solution
├── advanced/                    # measurable improvement over baseline — see CHANGELOG.md
├── eval/score.py                # rubric-based scoring: baseline vs advanced, a number not a vibe
├── trajectories/                # raw agent session logs (disclosure requirement)
├── scripts/                     # setup / run_baseline / run_advanced / collect_trajectories
├── .claude/                     # Claude Code project config + the deploy-confirmation hook
│   └── workflows/                #   hackathon-sprint.js + hackathon-fix.js — the agent
│                                  #   orchestration this entry is actually built with
├── .github/workflows/ci.yml     # runs setup → baseline → advanced → eval on every push
└── PROBLEM.md                   # the kickoff problem statement goes here
```

## Setup

```bash
make setup
```

## Run

```bash
make baseline   # runs baseline/
make advanced   # runs advanced/
make eval       # scores both, prints the delta
```

## Reproducing in a clean environment

1. `git clone` this repo
2. `make setup`
3. `make baseline && make advanced && make eval`

CI (`.github/workflows/ci.yml`) runs this exact sequence on every push, so a green
build is an independent, third-party confirmation of reproducibility — not just a
claim in this README.

[Fill in once the stack is chosen: exact OS/runtime versions, any external services
or API keys needed. Note: the event does not provide credits or keys — the stack is
brought and funded independently.]

**Runtime:** [fill in: wall-clock time for `make setup && make baseline && make advanced
&& make eval` on a clean checkout]
**Cost:** [fill in: dollar cost of that same clean run — API usage, any paid services]

## How this was actually built: the agent workflow

This entry is built with Claude Code's Workflow tool, not just ad-hoc prompting —
see `.claude/workflows/` for the scripts and `CLAUDE.md` for how/when they're invoked:

- **`hackathon-sprint`** — run once, right after kickoff: extract requirements from
  `PROBLEM.md` → judge-panel over candidate baseline approaches → implement
  `baseline/` → multi-lens adversarial verify (correctness / edge-cases /
  reproducibility) → judge-panel over improvement directions → implement
  `advanced/` → multi-lens adversarial verify + regression check → run `eval/score.py`
  → write up `CHANGELOG.md`.
- **`hackathon-fix`** — used for mid-sprint hardening rounds: parallel bug-hunters,
  each finding adversarially refuted before a fix is applied, looping until two
  consecutive rounds turn up nothing new.

Since "Agent Solution & Engineering" is the #1 tie-break criterion, this is treated
as a first-class part of the submission, not incidental tooling.

## Agent trajectories

Raw Claude Code session logs live in `trajectories/`. See `trajectories/README.md`
for how they were captured — copied as-is, not reformatted or cleaned up.

## Video (≤5 min)

[link once recorded]

## Ownership note

Submitted under the event's participation agreement (micro1 holds rights to use
submissions, including for model training — see the official Rule Book for exact
terms, not summarized here).
