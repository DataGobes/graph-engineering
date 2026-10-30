export const meta = {
  name: 'specgraph-front',
  description: 'Spec-driven graph, front half: specify and clarify each story of one wave',
  whenToUse: 'Run with the args printed by `python -m specgraph next <repo>` when it says specgraph-front',
  phases: [
    { title: 'Specify', detail: 'one agent per story writes spec.md' },
    { title: 'Clarify', detail: 'one agent per story writes questions.md and answers.md defaults' },
  ],
}

// args: {wave, wave_branch, repo, specs_dir, context: [paths], stories: [{id, title, path, depends_on}]}
const A = args
const dir = s => `${A.repo}/${A.specs_dir}/${s.id}`
const contextList = A.context.map(c => `${A.repo}/${c}`).join(', ')

const RULES = `Rules:
- Work only inside ${A.repo}. Write only the files named below; change nothing else and make no git commits.
- Read the story, the context files (${contextList}) and the code you need. Do not invent facts the backlog does not state.
- Plain, short sentences.`

const CLARIFY = {
  type: 'object',
  properties: {
    blocking_questions: { type: 'integer', description: 'questions that must be answered before planning' },
    other_questions: { type: 'integer', description: 'questions answered with a recorded default' },
  },
  required: ['blocking_questions', 'other_questions'],
}

const specify = s => agent(
  `You write the specification for one backlog story in ${A.repo}.

Story ${s.id} "${s.title}": ${A.repo}/${s.path}
It depends on: ${s.depends_on.length ? s.depends_on.join(', ') : 'nothing'}.

Write ${dir(s)}/spec.md with exactly these sections:
# ${s.id} spec
## Intent            two or three sentences: who, what, why
## Acceptance criteria   numbered AC-1, AC-2, ... Each one testable offline, and each names the story criterion it comes from
## Interfaces        CLI commands and flags, tables and columns, files, exit codes this story adds or changes
## Out of scope
## Assumptions       anything you had to assume; each will be checked in the clarify step

${RULES}`,
  { label: `specify:${s.id}`, phase: 'Specify' })

const clarify = s => agent(
  `You review a specification before anyone plans or codes it, acting for the product owner's time.

Story: ${A.repo}/${s.path}
Spec: ${dir(s)}/spec.md

Find what is ambiguous, contradictory or missing in the story and the spec: things where two reasonable developers would build different behaviour.
Mark a question "blocking" only when a wrong guess would change an acceptance criterion or an interface. Everything else is "default": propose the answer you would pick.

Write ${dir(s)}/questions.md: a numbered list, each item "[blocking]" or "[default]", the question, and one line on why it matters.
Write ${dir(s)}/answers.md: the same numbering. For a [default] item write "Default: <your answer>". For a [blocking] item write "TODO" (the product owner fills it in).
If there are no questions, write "No open questions." in both files.
You may fix plain mistakes in spec.md, but keep its sections.

${RULES}

Return the counts.`,
  { label: `clarify:${s.id}`, phase: 'Clarify', schema: CLARIFY })

const results = await pipeline(A.stories, specify, (_, s) => clarify(s))
const stories = A.stories.map((s, i) => ({ id: s.id, ...(results[i] || { failed: true }) }))
log(stories.map(s => `${s.id}: ${s.failed ? 'failed' : `${s.blocking_questions} blocking, ${s.other_questions} defaulted`}`).join('; '))
return { kind: 'front', wave: A.wave, stories: stories.filter(s => !s.failed) }
