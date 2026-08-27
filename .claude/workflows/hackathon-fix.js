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
if (!['baseline', 'advanced'].includes(target)) {
  throw new Error(`Invalid target "${target}" -- must be "baseline" or "advanced".`)
}
const context = (args && args.context) || '(none given -- use your judgment and CLAUDE.md)'

const MAX_ROUNDS = 8 // safety valve: bounds a 3-day time-boxed hackathon run regardless of convergence
const REFUTE_COOLDOWN_ROUNDS = 2 // rounds a refuted bug is suppressed before it's eligible to resurface

const seen = new Set() // descriptions of bugs confirmed fixed -- never re-reported
const refutedAt = new Map() // description -> round last refuted -- eligible again after cooldown
const fixed = []
let dryRounds = 0
let round = 0

while (dryRounds < 2 && round < MAX_ROUNDS) {
  round += 1
  const investigated = [...seen, ...refutedAt.keys()]
  const investigatedNote = investigated.length
    ? ` Already investigated earlier this run (don't re-report the same thing verbatim, but do flag it ` +
      `again with new evidence if it's still genuinely present): ${investigated.join('; ')}.`
    : ''
  phase('Find')
  const found = (await parallel(['correctness', 'edge-cases', 'reproducibility'].map(lens => () =>
    agent(
      `Hunt for bugs in ${target}/ through the ${lens} lens. Actually run scripts/run_${target}.sh ` +
      `yourself -- don't just read the code. Context on what's known to be failing or worth checking: ` +
      `${context}.${investigatedNote} Report concrete, reproducible bugs only, not style nits.`,
      { schema: BUGS_SCHEMA, phase: 'Find', label: `find-${lens}-r${round}` }
    )
  ))).filter(Boolean).flatMap(r => r.bugs)

  const fresh = found.filter(b => {
    if (seen.has(b.description)) return false
    const lastRefuted = refutedAt.get(b.description)
    return lastRefuted === undefined || (round - lastRefuted) >= REFUTE_COOLDOWN_ROUNDS
  })
  if (!fresh.length) {
    dryRounds += 1
    log(`Round ${round}: nothing new (${dryRounds}/2 dry)`)
    continue
  }
  dryRounds = 0
  log(`Round ${round}: ${fresh.length} new candidate bug(s)`)

  phase('Verify & Fix')
  const judged = await parallel(fresh.map(b => () =>
    parallel([1, 2].map(n => () =>
      agent(
        `Try to refute this bug report on ${target}/ by attempting to reproduce it yourself. Default to ` +
        `refuted=true if you cannot reproduce it. Bug: ${JSON.stringify(b)}`,
        { schema: REFUTE_SCHEMA, phase: 'Verify & Fix', label: `refute:r${round}:${n}:${b.description.slice(0, 40)}` }
      )
    )).then(votes => ({ bug: b, survives: votes.filter(Boolean).filter(v => !v.refuted).length >= 1 }))
  ))

  const real = judged.filter(Boolean).filter(r => r.survives).map(r => r.bug)
  const refuted = judged.filter(Boolean).filter(r => !r.survives).map(r => r.bug)
  refuted.forEach(b => refutedAt.set(b.description, round))

  if (real.length) {
    const fixReport = await agent(
      `Fix these confirmed bugs in ${target}/, then re-run scripts/run_${target}.sh to confirm the fix ` +
      `and check for regressions on anything already working: ${JSON.stringify(real)}`,
      { phase: 'Verify & Fix', label: `apply-fixes-r${round}` }
    )
    real.forEach(b => seen.add(b.description))
    fixed.push({ round, bugs: real, fixReport })
    log(`Round ${round}: fixed ${real.length} confirmed bug(s) in ${target}/`)
  } else {
    log(`Round ${round}: all candidate bugs refuted, none fixed`)
  }
}

return { target, roundsRun: round, totalCandidatesSeen: seen.size + refutedAt.size, fixed }
