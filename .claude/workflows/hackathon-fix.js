export const meta = {
  name: 'hackathon-fix',
  description: 'Loop-until-dry bug-hunt + adversarial-verify hardening pass on baseline/ or advanced/, without re-running the full sprint pipeline.',
  whenToUse: 'Use mid-sprint for a targeted round of "find bugs, verify, fix" -- e.g. eval regressed, a reviewer/judge-simulated edge case failed, or you just want another hardening pass. Pass args: { target: "baseline"|"advanced", context?: string }.',
  phases: [
    { title: 'Find', detail: 'parallel bug-hunters across correctness / edge-cases / reproducibility lenses' },
    { title: 'Verify & Fix', detail: 'adversarially refute each finding, fix what survives' },
  ],
}

const BUGS_SCHEMA = {
  type: 'object',
  properties: {
    bugs: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          description: { type: 'string' },
          file: { type: 'string' },
          severity: { type: 'string' },
        },
        required: ['description'],
      },
    },
  },
  required: ['bugs'],
}

const REFUTE_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    rationale: { type: 'string' },
  },
  required: ['refuted', 'rationale'],
}

const target = (args && args.target) || 'baseline'
const context = (args && args.context) || '(none given -- use your judgment and CLAUDE.md)'

const seen = new Set()
const fixed = []
let dryRounds = 0
let round = 0

while (dryRounds < 2) {
  round += 1
  phase('Find')
  const found = (await parallel(['correctness', 'edge-cases', 'reproducibility'].map(lens => () =>
    agent(
      `Hunt for bugs in ${target}/ through the ${lens} lens. Actually run scripts/run_${target}.sh ` +
      `yourself -- don't just read the code. Context on what's known to be failing or worth checking: ` +
      `${context}. Report concrete, reproducible bugs only, not style nits.`,
      { schema: BUGS_SCHEMA, phase: 'Find', label: `find-${lens}-r${round}` }
    )
  ))).filter(Boolean).flatMap(r => r.bugs)

  const fresh = found.filter(b => !seen.has(b.description))
  if (!fresh.length) {
    dryRounds += 1
    log(`Round ${round}: nothing new (${dryRounds}/2 dry)`)
    continue
  }
  dryRounds = 0
  fresh.forEach(b => seen.add(b.description))
  log(`Round ${round}: ${fresh.length} new candidate bug(s)`)

  phase('Verify & Fix')
  const judged = await parallel(fresh.map(b => () =>
    parallel([1, 2].map(() => () =>
      agent(
        `Try to refute this bug report on ${target}/ by attempting to reproduce it yourself. Default to ` +
        `refuted=true if you cannot reproduce it. Bug: ${JSON.stringify(b)}`,
        { schema: REFUTE_SCHEMA, phase: 'Verify & Fix', label: `refute:${b.description.slice(0, 40)}` }
      )
    )).then(votes => ({ bug: b, survives: votes.filter(Boolean).filter(v => !v.refuted).length >= 1 }))
  ))

  const real = judged.filter(Boolean).filter(r => r.survives).map(r => r.bug)
  if (real.length) {
    const fixReport = await agent(
      `Fix these confirmed bugs in ${target}/, then re-run scripts/run_${target}.sh to confirm the fix ` +
      `and check for regressions on anything already working: ${JSON.stringify(real)}`,
      { phase: 'Verify & Fix', label: `apply-fixes-r${round}` }
    )
    fixed.push({ round, bugs: real, fixReport })
    log(`Round ${round}: fixed ${real.length} confirmed bug(s) in ${target}/`)
  } else {
    log(`Round ${round}: all candidate bugs refuted, none fixed`)
  }
}

return { target, roundsRun: round, totalCandidatesSeen: seen.size, fixed }
