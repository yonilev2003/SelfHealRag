# Problem statement — micro1 Agentic Workflows Hackathon

Full transcription of the kickoff document (`micro1 — First Hackathon` PDF, 10
pages), extracted with the `pdf` skill on 2026-08-28. This is the source of truth
for requirements; `.claude/workflows/hackathon-sprint.js` reads this file.

---

## The challenge (p.1)

Choose a problem worth solving and use agents to create something people would
genuinely find useful. Keep it practical, share what you learn and have fun.

Pick a specific and meaningful problem you understand. Use agents to solve it
and show through clear evidence that your solution improves the way the task is
handled today. Start by explaining who has the problem. Describe the bottleneck
they face and why solving it would be valuable in practice. The goal is to
create something a real person would want to use.

**Keep four questions in mind:**

1. Who has this problem?
2. What bottleneck makes it worth solving?
3. Does the agent solve it well?
4. Can another person reproduce the result?

## How agents can help (p.2)

Use whichever agent capabilities help solve the problem well. One solution may
improve when the agent receives better context or better tools. Another may use
memory to carry important information forward. Verification can catch errors
before they reach the user, while specialized skills can deepen the agent's
ability in a particular task. Some solutions may benefit from orchestration
across several agents.

Choose the approach that fits your problem. Judges focus on whether each design
choice improves the solution and helps the agent reach the goal reliably.
**Purposeful choices matter more than the number of components.**

## Show how the solution improved (p.2)

Create a simple baseline that represents a reasonable basic way to handle the
task before using your solution. For example:

- One direct prompt with basic instructions.
- One general purpose agent with basic tools.
- A simple script or template.
- The manual process people use today.

Keep the comparison fair by giving the baseline and final solution the same task
and evaluation cases. Explain any meaningful difference in the resources
available to each one. Use the final baseline comparison to show the size of the
overall improvement. Use the changelog to explain where that improvement came
from. Together, they tell the complete story of your solution.

## Tell the story with an improvement changelog (p.3)

Create a short changelog that tells the story of how your solution evolved.
Start with the simple baseline and follow the journey through to the final
result. Add one entry for every important experiment: what you tried and why,
the result using the same evaluation method whenever possible, and what you
decided to do next. **Include experiments you later removed** and explain what
they taught you about the problem.

Suggested changelog table (the progression is an example — replace with actual
changes):

| Stage | What you tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Baseline | Started with [basic approach] | [baseline result] | Established the starting point |
| Iteration 1 | Added a skill to address [issue] | [new result] | [kept, revised or removed] |
| Iteration 2 | Added verification after observing [failure] | [new result] | [kept, revised or removed] |
| Iteration 3 | Changed orchestration to improve [goal] | [new result] | [kept, revised or removed] |
| Final | Combined the changes that worked | [final result] | Identified the main contribution |

## How to evaluate your solution (p.4)

Choose **one primary metric** that reflects what success means to the user.
Before running the evaluation, define what a good final result looks like for
the intended user. Use the same cases for the baseline and final solution, then
share the complete results. **Ten or more cases is a good target** when the task
allows it. **Include one challenging case** and explain what it revealed.

Suggested results format:

| Metric | Simple baseline | Agent solution | Change |
|---|---|---|---|
| Primary outcome | [value] | [value] | [change] |
| Human time per task | [value] | [value] | [change] |
| Cost per task | [value] | [value] | [change] |

You run this evaluation yourself. If the format above fits your task poorly,
design your own clear scoring rubric and propose it, so the judges can use it to
assess your workflow.

## How judging works (p.5) — 100 points

| Criterion | Points | What strong work looks like |
|---|---|---|
| Problem & User Value | 15 | Solves a meaningful problem for a clearly defined user. *Who experiences the bottleneck and why does solving it matter?* |
| Agent Solution & Engineering | **30** | Agents used purposefully, technically sound. Better context or tools may improve one project; memory, verification, skills or orchestration another. *Which design choices helped the agent solve the problem?* |
| End to End Quality | **20** | A realistic, self-contained execution producing a final result the user can use, with the finish of something a person would sign their name to rather than an obvious AI-generated draft. *Would the intended user consider this output high quality?* |
| Measured Improvement | 15 | Gains over a fair baseline; changelog connects each iteration with evidence. *Which changes truly improved the outcome?* |
| Reproducibility | 15 | A clear path to run the solution and baseline and reach the main result from a clean environment. |
| Hot Take / Insights | 5 | Turns an observed failure mode into a practical lesson for building more reliable agents. |

## Ground rules (p.6)

1. You are welcome to build with tools and components you already know.
2. Make it clear what existed before the competition and what you added.
3. Use every tool and component according to its license and service terms.
4. Keep consequential actions controlled through a sandbox or simulation. Add
   human approval before the action happens.
5. Make a qualified human reviewer part of any solution that could significantly
   affect someone.
6. Choose a legal and ethical use case that treats people and their data
   responsibly.
7. Use information you are allowed to share. Public or synthetic data are
   usually the easiest options. Approved anonymous data also works.
8. Keep credentials and private information outside the submission.
9. Connect every claim about your results to the evidence you submit.
10. Give judges enough access to run the project and reproduce the main result.

## Final deliverables (p.7) — all four required

1. **Complete solution code and improvement changelog.** Full project and
   everything required to run it, including the instructions that shape each
   agent. README introduces the intended user, their current bottleneck, and why
   solving it is valuable. Clearly labeled Improvement Changelog; every
   meaningful iteration gets an entry connected to evidence. Close with the main
   failure mode and your hot take.
2. **Reproduction guide.** Written for someone starting from a clean
   environment: setup, exact commands for solution / baseline / evaluation,
   required data, expected output, versions, approximate runtime and cost.
3. **Solution video (≤ 5 minutes).** Begin with the problem and simple baseline,
   then walk through one realistic execution start to finish. Show the final
   comparison and briefly explain the changelog. Highlight the change that
   contributed most and one experiment you removed.
4. **Agent trajectories.** Representative trajectories for every agent used,
   easy to follow from agent instructions to final result: what the agent did,
   how its tools responded, the feedback that shaped its next step, retries and
   human checkpoints.

## Appendix — three worked examples (pp.8–10, for reference only)

The kickoff document illustrates the expected shape with three examples (avoid
cloning them directly; many teams will):

1. **Code analysis: is this repository actually good?** — buyer evaluating a
   private repo's quality before purchase; agent ranks approved codebases
   against qualified reviewers' shared-rubric ranking.
2. **Candidate evaluation: should we hire this person?** — recruiter
   consolidating CV/interviews/assessments; agent surfaces evidence and
   uncertainty, human makes the call.
3. **Podcast translation: can every version still feel like the same show?** —
   translation consistency across episodes/languages: speaker identity,
   recurring terms, tone, prior decisions.

## Submission form (from the event site)

- **Title** (required) — clear, descriptive.
- **Description** (required) — project/solution description, formatting + links allowed.
- **Video URL** (required) — link to demo/pitch video.
- **Source Code** (required) — upload zip/apk, **max 50 MB**.
- Options: Submit / Save as Draft.
