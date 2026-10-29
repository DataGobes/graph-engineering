export const meta = {
  name: 'topo1-single',
  description: 'Topology 1: one agent reviews the whole package for bugs',
  whenToUse: 'Baseline run for the three-topologies experiment. args: {root: "<abs path to the shop package copy>"}',
  phases: [{ title: 'Review', detail: 'one agent, all files' }],
}

const FINDINGS = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'line', 'description'],
        properties: {
          file: { type: 'string', description: 'path like shop/money.py' },
          line: { type: 'integer', description: '1-based line of the faulty code' },
          description: { type: 'string', description: 'one sentence: what is wrong and why' },
        },
      },
    },
  },
}

const RULES = `Report only real defects: code that misbehaves for some input, or that contradicts its own docstring or comments. No style, typing or naming remarks. Report each defect once, at the line of the faulty code. Name files as shop/<name>.py. Read only files inside the directory you are given.`

phase('Review')
const result = await agent(
  `Review the Python package in ${args.root} (the directory named shop) for bugs. Read every file. ${RULES}`,
  { label: 'single-reviewer', phase: 'Review', schema: FINDINGS },
)
return { topology: 'single', agents: 1, findings: result ? result.findings : [] }
