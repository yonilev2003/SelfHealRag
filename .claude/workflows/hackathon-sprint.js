export const meta = {
  name: 'hackathon-sprint',
  description: 'Understand the kickoff problem, then plan/implement/verify baseline and advanced solutions with a judge panel + adversarial review at each step.',
  whenToUse: 'Run once, right after the kickoff problem PDF is known and pasted into PROBLEM.md. Pass args: { problemPath?: string, panelSize?: number, stopAfter?: "plan"|"baseline"|"ideation" }. stopAfter returns early for a manual sanity check before the run continues into implementation/advanced -- catches a wrong direction early instead of after a full advanced build. "ideation" stops right after Advanced Ideation picks a direction and a 3-agent devil\'s-advocate panel majority-votes on whether to reconsider it -- the moment to actually weigh creativity/business-value tradeoffs before committing engineering time. Re-invoke with Workflow({..., resumeFromRunId}) to continue once satisfied: everything up to the stop point replays from cache instantly.',
  phases: [
    { title: 'Understand', detail: 'extract requirements, constraints, acceptance tests, edge cases, intended user + bottleneck from PROBLEM.md' },
    { title: 'Plan', detail: 'judge panel over candidate baseline approaches, then a devil\'s-advocate panel' },
    { title: 'Baseline', detail: 'implement the simplest fully-correct solution in baseline/' },
    { title: 'Baseline Verify', detail: 'multi-lens adversarial review + fix' },
    { title: 'Advanced Ideation', detail: 'judge panel over non-cosmetic improvement directions, scored on creativity + user value too, then a 3-agent devil\'s-advocate panel that majority-votes on whether to reconsider' },
    { title: 'Advanced Implement', detail: 'implement the winning improvement in advanced/, wire up eval/score.py' },
    { title: 'Advanced Verify', detail: 'multi-lens adversarial review + regression check + run eval' },
    { title: 'Document', detail: 'CHANGELOG.md, README.md, trajectories' },
  ],
}

const REQUIREMENTS_SCHEMA = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    intendedUser: { type: 'string' },
    userBottleneck: { type: 'string' },
    functionalRequirements: { type: 'array', items: { type: 'string' } },
    constraints: { type: 'array', items: { type: 'string' } },
    acceptanceCriteria: { type: 'array', items: { type: 'string' } },
    edgeCases: { type: 'array', items: { type: 'string' } },
    ambiguities: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'intendedUser', 'userBottleneck', 'functionalRequirements', 'acceptanceCriteria', 'edgeCases'],
}

const APPROACH_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    description: { type: 'string' },
    risks: { type: 'array', items: { type: 'string' } },
  },
  required: ['name', 'description'],
}

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    score: { type: 'number' },
    rationale: { type: 'string' },
  },
  required: ['score', 'rationale'],
}

const IMPLEMENTATION_REPORT_SCHEMA = {
  type: 'object',
  properties: {
    filesChanged: { type: 'array', items: { type: 'string' } },
    whatItDoes: { type: 'string' },
    howToRun: { type: 'string' },
    knownLimitations: { type: 'array', items: { type: 'string' } },
    testsRun: { type: 'array', items: { type: 'string' } },
    testsPassed: { type: 'boolean' },
  },
  required: ['filesChanged', 'whatItDoes', 'testsPassed'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    bugsFound: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          description: { type: 'string' },
          severity: { type: 'string' },
          fixed: { type: 'boolean' },
        },
        required: ['description', 'fixed'],
      },
    },
    overallVerdict: { type: 'string' },
  },
  required: ['bugsFound', 'overallVerdict'],
}

const IMPROVEMENT_IDEA_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    description: { type: 'string' },
    dimension: { type: 'string' },
    userValue: { type: 'string' },
    riskOfRegression: { type: 'string' },
  },
  required: ['name', 'description', 'dimension', 'userValue'],
}

const DEVILS_ADVOCATE_SCHEMA = {
  type: 'object',
  properties: {
    isThisTheObviousChoice: { type: 'boolean' },
    strongestCounterArgument: { type: 'string' },
    whatASharperCompetitorMightBuildInstead: { type: 'string' },
    recommendReconsidering: { type: 'boolean' },
  },
  required: ['isThisTheObviousChoice', 'strongestCounterArgument', 'recommendReconsidering'],
}

const problemPath = (args && args.problemPath) || 'PROBLEM.md'
const panelSize = (args && args.panelSize) || 2
const stopAfter = args && args.stopAfter // 'plan' | 'baseline' | 'ideation' | undefined (full run)

// 3 independent skeptics, each told to find the strongest reason a decision is
// wrong (not to be agreeable), majority-vote on whether to flag it. Used on
// consequential picks (which approach/idea to build) -- not blanket-applied to
// every prompt, since grilling implementation-detail writes (README, changelog)
// multiplies cost without adding real scrutiny.
async function grillDecision(description, phaseName, labelPrefix) {
  const verdicts = (await parallel([1, 2, 3].map(n => () =>
    agent(
      `Grill this decision as skeptically as possible -- your job is to find the strongest reason it's ` +
      `wrong, not to be agreeable or to rubber-stamp it. Decision: ${description}`,
      { schema: DEVILS_ADVOCATE_SCHEMA, phase: phaseName, label: `${labelPrefix}-grill-${n}` }
    )
  ))).filter(Boolean)
  const reconsiderVotes = verdicts.filter(v => v.recommendReconsidering).length
  return {
    verdicts,
    majorityRecommendsReconsidering: verdicts.length > 0 && reconsiderVotes > verdicts.length / 2,
    concerns: verdicts.map(v => v.strongestCounterArgument),
  }
}

phase('Understand')
const requirements = await agent(
  `Read the hackathon problem statement at ${problemPath} (and any linked starter materials or ` +
  `acceptance tests already in the repo). Read CLAUDE.md first for working conventions. Produce a ` +
  `structured extraction: functional requirements, explicit constraints (perf/runtime/determinism/` +
  `allowed dependencies), the acceptance-test format if one is specified, the hidden edge cases and ` +
  `failure modes this kind of problem is designed to probe (the challenge explicitly rewards handling ` +
  `"incomplete requirements, hidden dependencies, difficult edge cases, failure modes"), and any ` +
  `ambiguities that need a judgment call. Also identify the intended user in concrete terms (a specific ` +
  `role/person, not "developers" in the abstract) and their current bottleneck without this solution -- ` +
  `this directly feeds the README's required framing and is 15% of the judging rubric on its own.`,
  { schema: REQUIREMENTS_SCHEMA, phase: 'Understand' }
)
log(`Extracted ${requirements.functionalRequirements.length} requirement(s), ${requirements.edgeCases.length} edge case(s) flagged`)

phase('Plan')
const candidates = (await parallel(Array.from({ length: panelSize }, (_, i) => () =>
  agent(
    `Given these requirements: ${JSON.stringify(requirements)}\n` +
    `Propose ONE concrete baseline implementation approach (angle ${i + 1}/${panelSize}) -- the ` +
    `simplest path that is still fully correct against the acceptance criteria. Make this angle ` +
    `genuinely different from the others (e.g. brute-force/straightforward vs. library-leaning vs. ` +
    `minimal-dependency). Do not write code yet -- plan only.`,
    { schema: APPROACH_SCHEMA, phase: 'Plan', label: `approach-${i + 1}` }
  )
))).filter(Boolean)

const judgedApproaches = (await parallel(candidates.map((c, i) => () =>
  agent(
    `Judge this baseline approach against the requirements on correctness risk (lower risk = higher ` +
    `score), speed to implement, and edge-case coverage. Score 0-10.\n` +
    `Approach: ${JSON.stringify(c)}\nRequirements: ${JSON.stringify(requirements)}`,
    { schema: JUDGE_SCHEMA, phase: 'Plan', label: `judge-approach-${i + 1}` }
  ).then(v => ({ approach: c, verdict: v }))
))).filter(Boolean)

const winner = judgedApproaches.sort((a, b) => b.verdict.score - a.verdict.score)[0]
if (!winner) throw new Error('All baseline-approach judges failed -- rerun Plan phase')
log(`Selected baseline approach: ${winner.approach.name} (${winner.verdict.score}/10)`)

const planGrill = await grillDecision(
  `Chose baseline approach "${winner.approach.name}" (${JSON.stringify(winner.approach)}) over ` +
  `${judgedApproaches.length - 1} other candidate(s): ${JSON.stringify(judgedApproaches.map(j => j.approach.name))}. ` +
  `Requirements: ${JSON.stringify(requirements)}.`,
  'Plan', 'plan'
)
log(`Plan grill: ${planGrill.majorityRecommendsReconsidering ? 'MAJORITY SAYS RECONSIDER -- ' + planGrill.concerns[0] : 'majority OK to proceed'}`)

if (stopAfter === 'plan') {
  log('stopAfter="plan": stopping for a manual check before implementation starts. Re-invoke with ' +
    'the same args (drop stopAfter, or set it to "baseline") plus resumeFromRunId to continue -- ' +
    'Understand/Plan replay from cache instantly.')
  return { requirements, winner, judgedApproaches, planGrill }
}

phase('Baseline')
const baselineReport = await agent(
  `Implement this approach as the baseline solution, inside baseline/. Requirements: ` +
  `${JSON.stringify(requirements)}. Approach: ${JSON.stringify(winner.approach)}. Follow CLAUDE.md ` +
  `conventions. Make it runnable via scripts/run_baseline.sh and add any dependency installs it needs ` +
  `to scripts/setup.sh. Optimize for correctness over elegance -- that's what advanced/ is for. Update ` +
  `baseline/README.md with what it does and how to run it.`,
  { schema: IMPLEMENTATION_REPORT_SCHEMA, phase: 'Baseline' }
)

phase('Baseline Verify')
// Report-only and concurrent, then a single sequential fix pass -- concurrent
// lenses must not all edit baseline/ at once (lost updates / clobbered fixes).
const baselineVotes = (await parallel(['correctness', 'edge-cases', 'reproducibility'].map(lens => () =>
  agent(
    `Adversarially review the baseline solution through the ${lens} lens. Actually run ` +
    `scripts/run_baseline.sh yourself and feed it the trickiest inputs implied by these requirements ` +
    `and edge cases -- don't just read the code.` +
    (lens === 'reproducibility'
      ? ` For the reproducibility lens specifically: delete any local caches/build artifacts/venvs and ` +
        `re-run scripts/setup.sh + scripts/run_baseline.sh from a clean state; flag hardcoded absolute ` +
        `paths, unpinned dependency versions, or output that differs across two runs.`
      : '') +
    ` Requirements: ${JSON.stringify(requirements)}. Implementation report: ` +
    `${JSON.stringify(baselineReport)}. Report bugs only -- do not edit any files.`,
    { schema: VERDICT_SCHEMA, phase: 'Baseline Verify', label: `verify-${lens}` }
  )
))).filter(Boolean)
const baselineBugs = baselineVotes.flatMap(v => v.bugsFound)
log(`Baseline verify: ${baselineBugs.length} issue(s) found across ${baselineVotes.length} lens(es)`)
if (baselineBugs.length) {
  await agent(
    `Fix these bugs found in baseline/, then re-run scripts/run_baseline.sh to confirm the fixes and ` +
    `check for regressions on anything already working: ${JSON.stringify(baselineBugs)}`,
    { phase: 'Baseline Verify', label: 'baseline-apply-fixes' }
  )
}

if (stopAfter === 'baseline') {
  log('stopAfter="baseline": stopping for a manual check before Advanced Ideation. Re-invoke with the ' +
    'same args (drop stopAfter) plus resumeFromRunId to continue -- everything through Baseline Verify ' +
    'replays from cache instantly.')
  return { requirements, winner, baselineReport, baselineBugsFound: baselineBugs.length }
}

phase('Advanced Ideation')
// panelSize - 1 candidates chase technical improvement dimensions; one seat is
// reserved for a genuinely creative/differentiated angle so the panel isn't
// purely incremental variations on the same theme -- creativity only gets
// exercised here, since baseline's job is "correct fast," not "novel."
const ideas = (await parallel(Array.from({ length: panelSize }, (_, i) => () => {
  const isCreativeSeat = i === panelSize - 1 && panelSize > 1
  return agent(
    `Baseline is done: ${JSON.stringify(baselineReport)}. Requirements: ${JSON.stringify(requirements)}. ` +
    `Intended user: ${requirements.intendedUser}. Their bottleneck: ${requirements.userBottleneck}.\n` +
    (isCreativeSeat
      ? `Propose ONE genuinely creative, differentiated improvement direction for advanced/ -- something a ` +
        `sharper competitor would build that a straightforward technical pass would miss. It must still be ` +
        `implementable in the remaining time and measurable via eval/score.py, but should be the kind of ` +
        `idea that makes the entry stand out, not an obvious next step.`
      : `Propose ONE concrete, non-cosmetic improvement direction for advanced/ (angle ${i + 1}/${panelSize}) ` +
        `-- e.g. correctness on more edge cases, performance/efficiency, reliability/failure handling, or ` +
        `broader coverage. Make it distinct from the other angles.`) +
    ` State explicitly how it serves the intended user's actual bottleneck, not just a technical metric.`,
    { schema: IMPROVEMENT_IDEA_SCHEMA, phase: 'Advanced Ideation', label: `idea-${i + 1}` }
  )
}))).filter(Boolean)

const judgedIdeas = (await parallel(ideas.map((idea, i) => () =>
  agent(
    `Judge this improvement idea given the baseline and requirements. Score 0-10 as a genuine composite of: ` +
    `expected impact vs. implementation risk, how creative/differentiated it is (not just an obvious next ` +
    `step), and how directly it serves the intended user's bottleneck ("${requirements.userBottleneck}") -- ` +
    `not just a technical metric. Explain the breakdown across these three in the rationale, don't just give ` +
    `a number.\nIdea: ${JSON.stringify(idea)}\nBaseline: ${JSON.stringify(baselineReport)}\n` +
    `Requirements: ${JSON.stringify(requirements)}`,
    { schema: JUDGE_SCHEMA, phase: 'Advanced Ideation', label: `judge-idea-${i + 1}` }
  ).then(v => ({ idea, verdict: v }))
))).filter(Boolean)

const bestIdea = judgedIdeas.sort((a, b) => b.verdict.score - a.verdict.score)[0]
if (!bestIdea) throw new Error('All advanced-idea judges failed -- rerun Advanced Ideation phase')
log(`Selected advanced direction: ${bestIdea.idea.name} (${bestIdea.verdict.score}/10)`)

const ideationGrill = await grillDecision(
  `Chose advanced direction "${bestIdea.idea.name}" (${JSON.stringify(bestIdea.idea)}) over ` +
  `${judgedIdeas.length - 1} other candidate(s): ${JSON.stringify(judgedIdeas.map(j => j.idea.name))}. ` +
  `Baseline: ${JSON.stringify(baselineReport)}. Intended user: ${requirements.intendedUser}, bottleneck: ` +
  `${requirements.userBottleneck}. Specifically address: does this serve the user's actual bottleneck, or is ` +
  `it a technical exercise disconnected from it? What would a sharper competitor build instead?`,
  'Advanced Ideation', 'ideation'
)
log(`Ideation grill: ${ideationGrill.majorityRecommendsReconsidering ? 'MAJORITY SAYS RECONSIDER -- ' + ideationGrill.concerns[0] : 'majority OK to proceed'}`)

if (stopAfter === 'ideation') {
  log('stopAfter="ideation": stopping for a manual check on the advanced direction + the grill panel\'s ' +
    'pushback, before implementation starts. Re-invoke with the same args (drop stopAfter) plus ' +
    'resumeFromRunId to continue -- everything so far replays from cache instantly.')
  return { requirements, winner, baselineReport, bestIdea, judgedIdeas, ideationGrill }
}

phase('Advanced Implement')
const advancedReport = await agent(
  `Implement this improvement as the advanced solution in advanced/, building on the same problem ` +
  `understanding as baseline/ (don't edit baseline/). Idea: ${JSON.stringify(bestIdea.idea)}. ` +
  `Requirements: ${JSON.stringify(requirements)}. Make it runnable via scripts/run_advanced.sh. Fill in ` +
  `eval/score.py's CRITERIA with real, independently-testable checks derived from the acceptance ` +
  `criteria (${JSON.stringify(requirements.acceptanceCriteria)}) so \`make eval\` produces a real numeric ` +
  `delta, not the placeholder 0/0. Update advanced/README.md.`,
  { schema: IMPLEMENTATION_REPORT_SCHEMA, phase: 'Advanced Implement' }
)

phase('Advanced Verify')
// Report-only and concurrent, then a single sequential fix pass -- concurrent
// lenses must not all edit advanced/ at once (lost updates / clobbered fixes).
const advancedVotes = (await parallel(['correctness', 'regression-vs-baseline', 'edge-cases'].map(lens => () =>
  agent(
    `Adversarially review the advanced solution through the ${lens} lens. Actually run ` +
    `scripts/run_advanced.sh yourself. Requirements: ${JSON.stringify(requirements)}. Implementation ` +
    `report: ${JSON.stringify(advancedReport)}. For the regression-vs-baseline lens specifically: confirm ` +
    `advanced/ is still correct on everything baseline/ already handled (also re-run ` +
    `scripts/run_baseline.sh to compare). Report bugs only -- do not edit any files.`,
    { schema: VERDICT_SCHEMA, phase: 'Advanced Verify', label: `verify-${lens}` }
  )
))).filter(Boolean)
const advancedBugs = advancedVotes.flatMap(v => v.bugsFound)
log(`Advanced verify: ${advancedBugs.length} issue(s) found across ${advancedVotes.length} lens(es)`)
if (advancedBugs.length) {
  await agent(
    `Fix these bugs found in advanced/, then re-run scripts/run_advanced.sh to confirm the fixes and ` +
    `check for regressions on anything already working: ${JSON.stringify(advancedBugs)}`,
    { phase: 'Advanced Verify', label: 'advanced-apply-fixes' }
  )
}

const evalResult = await agent(
  `Run \`make setup && make baseline && make advanced && make eval\` from the repo root as one ` +
  `sequential check that today's documented reproduction path (see README.md) actually works ` +
  `end-to-end, and return the raw JSON output of \`make eval\` verbatim -- nothing else. If any step ` +
  `in that chain fails or exits non-zero, treat that as a phase failure: report the failing command ` +
  `and its output instead of fabricating a result.`,
  { phase: 'Advanced Verify', label: 'run-eval' }
)
log(`eval/score.py output: ${evalResult}`)

phase('Document')
const docReport = await agent(
  `Write up this sprint's results, replacing template placeholders (don't duplicate old entries):\n` +
  `1. Append filled-in [Baseline] and [Advanced] entries to CHANGELOG.md using: requirements=` +
  `${JSON.stringify(requirements)}, winningApproach=${JSON.stringify(winner.approach)}, ` +
  `baselineReport=${JSON.stringify(baselineReport)}, bestIdea=${JSON.stringify(bestIdea.idea)}, ` +
  `advancedReport=${JSON.stringify(advancedReport)}, evalResult=${evalResult}. Include the actual ` +
  `eval/score.py delta number, not a vibe. Consider the grill panel's strongest pushback on the advanced ` +
  `direction (${JSON.stringify(ideationGrill.concerns)}) as candidate material for the "what was tried and ` +
  `didn't work" / hot-take angle -- it's a real, adversarially-generated counter-case, not filler.\n` +
  `2. Fill in the top of README.md: problem name, exact setup/versions, AND open with the intended user ` +
  `(${requirements.intendedUser}) and their bottleneck (${requirements.userBottleneck}) -- this is 15% of ` +
  `the judging rubric ("Problem & user value"), not optional framing.\n` +
  `3. Run scripts/collect_trajectories.sh (or \`make trajectories\`) to capture this session's logs.\n` +
  `Return the list of every file you touched.`,
  { phase: 'Document' }
)

return {
  requirements, winner, planGrill, baselineReport, baselineVotes, bestIdea, ideationGrill,
  advancedReport, advancedVotes, evalResult, docReport,
}
