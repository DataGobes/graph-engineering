export const meta = {
  name: 'topo3-verify',
  description: 'Topology 3: per-file reviewers pipelined into an independent skeptic per finding',
  whenToUse: 'Pipeline + adversarial verify run for the three-topologies experiment. args: {root, files: [...]}',
  phases: [
    { title: 'Review', detail: 'one agent per file, same prompt as topology 2' },
    { title: 'Verify', detail: 'one skeptic per finding, may read the whole package' },
  ],
}

const FINDING = {
  type: 'object',
  required: ['file', 'line', 'description'],
  properties: {
    file: { type: 'string', description: 'path like shop/money.py' },
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

const RULES = `Report only real defects: code that misbehaves for some input, or that contradicts its own docstring or comments. No style, typing or naming remarks. Report each defect once, at the line of the faulty code. Name files as shop/<name>.py.`

// No barrier: a file's findings start verification as soon as that file's review is done.
const results = await pipeline(
  args.files,
  f => agent(
    `Review ONE file for bugs: ${args.root}/${f}. Read only this file; do not open any other file. ${RULES}`,
    { label: `review:${f}`, phase: 'Review', schema: FINDINGS },
  ),
  (review, f) => parallel((review ? review.findings : []).map((finding, i) => () =>
    agent(
      `A reviewer claims this is a bug in the package at ${args.root}:\n${JSON.stringify(finding)}\n\n` +
      `Try to REFUTE it. Read the code and anything it calls or is called by. ` +
      `It is real only if you can name a concrete input or call that misbehaves, or a clear contradiction with its docstring or comments. ` +
      `If you are unsure, answer real=false. Read only files inside ${args.root}.`,
      { label: `verify:${f}#${i + 1}`, phase: 'Verify', schema: VERDICT },
    ).then(v => ({ ...finding, verdict: v })))),
)
const all = results.filter(Boolean).flat().filter(Boolean)
const kept = all.filter(f => f.verdict && f.verdict.real)
log(`${all.length} raw findings, ${kept.length} survived verification`)
return {
  topology: 'verify',
  agents: args.files.length + all.length,
  raw: all.length,
  rejected: all.filter(f => !(f.verdict && f.verdict.real)),
  findings: kept,
}
