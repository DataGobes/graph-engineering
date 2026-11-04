export const meta = {
  name: 'topo2-fanout',
  description: 'Topology 2: one isolated reviewer per file, then one merger (fan-out / fan-in)',
  whenToUse: 'Fan-out run for the three-topologies experiment. args: {root, units: [{name, files}]} or {root, files}',
  phases: [
    { title: 'Review', detail: 'one agent per unit (file or sub-package), sees only that unit' },
    { title: 'Merge', detail: 'one agent dedups the combined list' },
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

const RULES = `Report only real defects: code that misbehaves for some input, or that contradicts its own docstring or comments. No style, typing or naming remarks. Report each defect once, at the line of the faulty code. Name each file by its path from the package folder, for example shop/money.py or logi/geo/zones.py.`

// A review unit is a set of files one reviewer sees. args.units = [{name, files}] (paths
// relative to root, e.g. one unit per sub-package); args.files = one unit per file (run 1).
const units = args.units || args.files.map(f => ({ name: f, files: [f] }))
const unitPrompt = u => u.files.length === 1
  ? `Review ONE file for bugs: ${args.root}/${u.files[0]}. Read only this file; do not open any other file. ${RULES}`
  : `Review these files for bugs, and only these: ${u.files.map(f => `${args.root}/${f}`).join(', ')}. Do not open any other file. ${RULES}`

phase('Review')
// Barrier on purpose: the merger needs every reviewer's list at once to dedup.
const perUnit = await parallel(units.map(u => () =>
  agent(
    unitPrompt(u),
    { label: `review:${u.name}`, phase: 'Review', schema: FINDINGS },
  )))
const combined = perUnit.filter(Boolean).flatMap(r => r.findings)
log(`${combined.length} raw findings from ${units.length} reviewers`)

phase('Merge')
const merged = await agent(
  `Here are bug findings from independent per-file reviewers:\n${JSON.stringify(combined, null, 2)}\n\n` +
  `Merge them into one list: remove exact or near duplicates (same defect reported twice), keep everything else unchanged. ` +
  `Do not add new findings and do not judge whether a finding is correct. You do not need to read any files.`,
  { label: 'merge', phase: 'Merge', schema: FINDINGS },
)
return { topology: 'fanout', agents: units.length + 1, raw: combined.length, findings: merged ? merged.findings : combined }
