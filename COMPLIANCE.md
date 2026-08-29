# Compliance checklist — kickoff document → build gates

Every requirement derived from the 10-page kickoff PDF (transcribed in
`PROBLEM.md`), mapped to the concrete artifact/gate that satisfies it. This file
is a working gate: nothing ships while a MUST row is unchecked. Derived
2026-08-28; source hash `be811a1d…88fc4`.

## A. Problem framing (p.1, pp.8–10)

| # | Requirement | Gate / artifact |
|---|---|---|
| A1 | Specific, meaningful problem **the participant understands** | README opening; concept chosen with domain steer (data/analytics, business, AI evaluation) |
| A2 | README explicitly answers the four questions: who has the problem / what bottleneck / does the agent solve it well / can another person reproduce | README structured with these four questions as literal headings (mirrors how all three appendix examples are structured) |
| A3 | "Something a real person would want to use" | Final artifact is a usable deliverable (file a person keeps), not a chat transcript |

## B. Agent solution (p.2, p.5)

| # | Requirement | Gate / artifact |
|---|---|---|
| B1 | Capabilities chosen **purposefully**; judges ask which design choice improved the solution | Each component has a written necessity claim + a measured ablation or changelog delta backing it |
| B2 | Purposeful choices > number of components | 3–4 load-bearing components max; no decorative agents |
| B3 | Technically sound | CI green; eval harness deterministic; seeds fixed |

## C. Baseline & fairness (p.2)

| # | Requirement | Gate / artifact |
|---|---|---|
| C1 | Simple baseline = reasonable basic handling (direct prompt / general agent with basic tools / script / manual process) | Baseline = one direct `claude -p` call, same model, same task framing |
| C2 | **Same task and evaluation cases** for baseline and final | `eval/run_eval.py` runs both arms over the identical case list |
| C3 | **Explain any meaningful difference in resources available to each arm** | README "Baseline fairness" section: same model, same input documents, same output schema and taxonomy; only the agentic machinery differs — differences enumerated explicitly |
| C4 | Final baseline comparison shows overall improvement size; changelog explains where it came from | Results table + changelog cross-references |

## D. Changelog (p.3)

| # | Requirement | Gate / artifact |
|---|---|---|
| D1 | Entry per important experiment: what tried, why, result **with same eval method**, decision | CHANGELOG.md table: Stage / What & why / Evidence (metric values) / Decision |
| D2 | **Include experiments later removed** + what they taught | ≥1 genuinely attempted-and-removed experiment with its real numbers (also required in the video, see F4) |
| D3 | Starts from the simple baseline, journey to final | First row = baseline result; last row = final + main contribution identified |

## E. Evaluation (p.4)

| # | Requirement | Gate / artifact |
|---|---|---|
| E1 | **One primary metric** reflecting what success means **to the user** | Single named primary metric, defined in README before results |
| E2 | Define what a good final result looks like **before** running the evaluation | Success definition written in eval README/docstring before first scored run (commit history proves ordering) |
| E3 | Same cases both arms; **share complete results** | Per-case results table (all cases, including failures) committed as `results/*.json` + rendered table |
| E4 | ≥10 cases | Target 12–15 cases |
| E5 | **One challenging case + explain what it revealed** | Dedicated hard case; README/changelog section "What the hard case revealed" |
| E6 | Suggested secondary rows: **human time per task, cost per task** | Results table includes measured human-time estimate and per-task API cost rows for both arms |
| E7 | If format fits poorly, propose own rubric for judges | If used, documented scoring rubric in eval README |

## F. Deliverables (p.7)

| # | Requirement | Gate / artifact |
|---|---|---|
| F1 | Full code + everything required to run, **including the instructions that shape each agent** | All agent prompts/system prompts are files in the repo (not inline strings buried in code) |
| F2 | README: intended user, current bottleneck, why valuable | README opening (= A2) |
| F3 | Clearly labeled Improvement Changelog; close with **main failure mode + hot take** | CHANGELOG.md ends with "Main failure mode" + "Hot take" sections, empirically grounded |
| F4 | Video ≤5 min: problem+baseline → one realistic execution start-to-finish → final comparison → changelog briefly → **change that contributed most + one removed experiment** | VIDEO_SCRIPT.md follows this exact beat structure; final video checked against it |
| F5 | Reproduction guide: clean environment, exact commands for solution/baseline/eval, data required, expected output, **versions, approximate runtime and cost** | README repro section with pinned versions + measured runtime + measured $ cost |
| F6 | **Trajectories for every agent**: instructions → tool responses → feedback shaping next step → retries and human checkpoints | `trajectories/` with per-agent JSONL (stream-json) + MANIFEST explaining how to read each one; includes retry/verification-failure examples |

## G. Ground rules (p.6)

| # | Requirement | Gate / artifact |
|---|---|---|
| G1 | Clear pre-competition vs added split | `pre-kickoff` scaffold commits vs work after `49a647a`; README section documents the split |
| G2 | Licenses/terms respected | Only public-domain / synthetic data; pip/npm deps under permissive licenses; repo itself carries an MIT `LICENSE` |
| G3 | **Consequential actions sandboxed + human approval before they happen** | Solution never sends/files/pays anything automatically; output is a review artifact; deploy-guard hook active |
| G4 | **Qualified human reviewer for solutions that could significantly affect someone** | The design goal is confidence-gated autonomy, not blanket human review (a system that needs a human on every output isn't self-healing) — `advanced/verifier.py` flags `requires_human_review: true` on the one case that actually is a real, live correction (a stale-citation override); a configurable human-in-the-loop *exception* path for low-confidence/high-impact memory corrections, and a separate risk-based human-*evaluation* sampling layer, are named as roadmap in `PRODUCTION_ROADMAP.md` §4 — neither is claimed as shipped. README Section 6 states this distinction plainly rather than overclaiming a review gate that doesn't exist in code. |
| G5 | Public or synthetic data only | Fully synthetic, deterministically generated corpus vendored in-repo |
| G6 | No credentials/private info in submission | `.env` gitignored; pre-zip secret scan; zip audit |
| G7 | **Every claim connected to submitted evidence** | Every number in README/CHANGELOG traceable to a committed `results/*.json`; no unmeasured superlatives |
| G8 | Judges get enough access to run and reproduce | Anthropic API key is the only external requirement; documented |

## H. Submission form (event site)

| # | Requirement | Gate / artifact |
|---|---|---|
| H1 | Title — clear, descriptive | Drafted at packaging |
| H2 | Description — formatting + links allowed | Drafted at packaging; links to video + repo |
| H3 | Video URL | Hosted link produced at video stage |
| H4 | Source zip ≤ 50 MB | `scripts/package_submission` size check < 50 MB |

## Deadline

Aug 30, 23:59 UTC (Aug 31, 02:59 IL). No extensions. Internal target: full
submission package ready by Aug 30, ~18:00 UTC, leaving buffer.
