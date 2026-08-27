export const meta = {
  name: 'hackathon-sprint',
  description: 'Understand the kickoff problem, then plan/implement/verify baseline and advanced solutions with a judge panel + adversarial review at each step.',
  whenToUse: 'Run once, right after the kickoff problem PDF is known and pasted into PROBLEM.md. Pass args: { problemPath?: string, panelSize?: number }.',
  phases: [
    { title: 'Understand', detail: 'extract requirements, constraints, acceptance tests, edge cases from PROBLEM.md' },
    { title: 'Plan', detail: 'judge panel over candidate baseline approaches' },
    { title: 'Baseline', detail: 'implement the simplest fully-correct solution in baseline/' },
    { title: 'Baseline Verify', detail: 'multi-lens adversarial review + fix' },
    { title: 'Advanced Ideation', detail: 'judge panel over non-cosmetic improvement directions' },
    { title: 'Advanced Implement', detail: 'implement the winning improvement in advanced/, wire up eval/score.py' },
    { title: 'Advanced Verify', detail: 'multi-lens adversarial review + regression check + run eval' },
    { title: 'Document', detail: 'CHANGELOG.md, README.md, trajectories' },
  ],
}

const REQUIREMENTS_SCHEMA = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    functionalRequirements: { type: 'array', items: { type: 'string' } },
    constraints: { type: 'array', items: { type: 'string' } },
    acceptanceCriteria: { type: 'array', items: { type: 'string' } },
    edgeCases: { type: 'array', items: { type: 'string' } },
    ambiguities: { type: 'array', items: { type: 'string' } },
  },
  required: ['summary', 'functionalRequirements', 'acceptanceCriteria', 'edgeCases'],
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
    riskOfRegression: { type: 'string' },
  },
  required: ['name', 'description', 'dimension'],
}

const problemPath = (args && args.problemPath) || 'PROBLEM.md'
const panelSize = (args && args.panelSize) || 2

phase('Understand')
const requirements = await agent(
  `Read the hackathon problem statement at ${problemPath} (and any linked starter materials or ` +
  `acceptance tests already in the repo). Read CLAUDE.md first for working conventions. Produce a ` +
  `structured extraction: functional requirements, explicit constraints (perf/runtime/determinism/` +
  `allowed dependencies), the acceptance-test format if one is specified, the hidden edge cases and ` +
  `failure modes this kind of problem is designed to probe (the challenge explicitly rewards handling ` +
  `"incomplete requirements, hidden dependencies, difficult edge cases, failure modes"), and any ` +
  `ambiguities that need a judgment call.`,
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

phase('Advanced Ideation')
const ideas = (await parallel(Array.from({ length: panelSize }, (_, i) => () =>
  agent(
    `Baseline is done: ${JSON.stringify(baselineReport)}. Requirements: ${JSON.stringify(requirements)}. ` +
    `Propose ONE concrete, non-cosmetic improvement direction for advanced/ (angle ${i + 1}/${panelSize}) ` +
    `-- e.g. correctness on more edge cases, performance/efficiency, reliability/failure handling, or ` +
    `broader coverage. Make it distinct from the other angles.`,
    { schema: IMPROVEMENT_IDEA_SCHEMA, phase: 'Advanced Ideation', label: `idea-${i + 1}` }
  )
))).filter(Boolean)

const judgedIdeas = (await parallel(ideas.map((idea, i) => () =>
  agent(
    `Judge this improvement idea on expected impact vs. implementation risk, given the baseline and ` +
    `requirements. Score 0-10.\nIdea: ${JSON.stringify(idea)}\nBaseline: ${JSON.stringify(baselineReport)}\n` +
    `Requirements: ${JSON.stringify(requirements)}`,
    { schema: JUDGE_SCHEMA, phase: 'Advanced Ideation', label: `judge-idea-${i + 1}` }
  ).then(v => ({ idea, verdict: v }))
))).filter(Boolean)

const bestIdea = judgedIdeas.sort((a, b) => b.verdict.score - a.verdict.score)[0]
if (!bestIdea) throw new Error('All advanced-idea judges failed -- rerun Advanced Ideation phase')
log(`Selected advanced direction: ${bestIdea.idea.name} (${bestIdea.verdict.score}/10)`)

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
  `eval/score.py delta number, not a vibe.\n` +
  `2. Fill in the top of README.md (problem name, exact setup/versions) now that the problem is known.\n` +
  `3. Run scripts/collect_trajectories.sh (or \`make trajectories\`) to capture this session's logs.\n` +
  `Return the list of every file you touched.`,
  { phase: 'Document' }
)

return { requirements, winner, baselineReport, baselineVotes, bestIdea, advancedReport, advancedVotes, evalResult, docReport }
