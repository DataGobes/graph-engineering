export const meta = {
  name: 'topo2-fanout',
  description: 'Topology 2: one isolated reviewer per file, then one merger (fan-out / fan-in)',
  whenToUse: 'Fan-out run for the three-topologies experiment. args: {root, files: ["money.py", ...]}',
  phases: [
    { title: 'Review', detail: 'one agent per file, sees only that file' },
    { title: 'Merge', detail: 'one agent dedups the combined list' },
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

const RULES = `Report only real defects: code that misbehaves for some input, or that contradicts its own docstring or comments. No style, typing or naming remarks. Report each defect once, at the line of the faulty code. Name files as shop/<name>.py.`

phase('Review')
// Barrier on purpose: the merger needs every reviewer's list at once to dedup.
const perFile = await parallel(args.files.map(f => () =>
  agent(
    `Review ONE file for bugs: ${args.root}/${f}. Read only this file; do not open any other file. ${RULES}`,
    { label: `review:${f}`, phase: 'Review', schema: FINDINGS },
  )))
const combined = perFile.filter(Boolean).flatMap(r => r.findings)
log(`${combined.length} raw findings from ${args.files.length} reviewers`)

phase('Merge')
const merged = await agent(
  `Here are bug findings from independent per-file reviewers:\n${JSON.stringify(combined, null, 2)}\n\n` +
  `Merge them into one list: remove exact or near duplicates (same defect reported twice), keep everything else unchanged. ` +
  `Do not add new findings and do not judge whether a finding is correct. You do not need to read any files.`,
  { label: 'merge', phase: 'Merge', schema: FINDINGS },
)
return { topology: 'fanout', agents: args.files.length + 1, raw: combined.length, findings: merged ? merged.findings : combined }
