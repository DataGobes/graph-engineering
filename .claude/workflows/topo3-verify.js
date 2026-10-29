export const meta = {
  name: 'topo3-verify',
  description: 'Topology 3: per-file reviewers pipelined into an independent skeptic per finding',
  whenToUse: 'Pipeline + adversarial verify run for the three-topologies experiment. args: {root, units: [{name, files}]} or {root, files}',
  phases: [
    { title: 'Review', detail: 'one agent per unit, same prompt as topology 2' },
    { title: 'Verify', detail: 'one skeptic per finding, may read the whole package' },
  ],
}

const FINDING = {
  type: 'object',
  required: ['file', 'line', 'description'],
  properties: {
    file: { type: 'string', description: 'path from the package folder, like logi/geo/zones.py' },
    line: { type: 'integer', description: '1-based line of the faulty code' },
    description: { type: 'string', description: 'one sentence: what is wrong and why' },
  },
}
const FINDINGS = { type: 'object', required: ['findings'], properties: { findings: { type: 'array', items: FINDING } } }
const VERDICT = {
  type: 'object',
  required: ['real', 'reason'],
  properties: {
    real: { type: 'boolean', description: 'true only if you could not refute it' },
    reason: { type: 'string', description: 'the input that breaks it, or why it is not a bug' },
  },
}

const RULES = `Report only real defects: code that misbehaves for some input, or that contradicts its own docstring or comments. No style, typing or naming remarks. Report each defect once, at the line of the faulty code. Name each file by its path from the package folder, for example shop/money.py or logi/geo/zones.py.`

// A review unit is a set of files one reviewer sees. args.units = [{name, files}] (paths
// relative to root, e.g. one unit per sub-package); args.files = one unit per file (run 1).
const units = args.units || args.files.map(f => ({ name: f, files: [f] }))
const unitPrompt = u => u.files.length === 1
  ? `Review ONE file for bugs: ${args.root}/${u.files[0]}. Read only this file; do not open any other file. ${RULES}`
  : `Review these files for bugs, and only these: ${u.files.map(f => `${args.root}/${f}`).join(', ')}. Do not open any other file. ${RULES}`

// No barrier: a file's findings start verification as soon as that file's review is done.
const results = await pipeline(
  units,
  u => agent(
    unitPrompt(u),
    { label: `review:${u.name}`, phase: 'Review', schema: FINDINGS },
  ),
  (review, u) => parallel((review ? review.findings : []).map((finding, i) => () =>
    agent(
      `A reviewer claims this is a bug in the package at ${args.root}:\n${JSON.stringify(finding)}\n\n` +
      `Try to REFUTE it. Read the code and anything it calls or is called by. ` +
      `It is real only if you can name a concrete input or call that misbehaves, or a clear contradiction with its docstring or comments. ` +
      `Judge the code as if every OTHER bug in the package were already fixed: a defect that another bug currently makes unreachable is still real. ` +
      `If you are unsure, answer real=false. Read only files inside ${args.root}.`,
      { label: `verify:${u.name}#${i + 1}`, phase: 'Verify', schema: VERDICT },
    ).then(v => ({ ...finding, verdict: v })))),
)
const all = results.filter(Boolean).flat().filter(Boolean)
const kept = all.filter(f => f.verdict && f.verdict.real)
log(`${all.length} raw findings, ${kept.length} survived verification`)
return {
  topology: 'verify',
  agents: units.length + all.length,
  raw: all.length,
  rejected: all.filter(f => !(f.verdict && f.verdict.real)),
  findings: kept,
}
