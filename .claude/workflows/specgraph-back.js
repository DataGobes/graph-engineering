export const meta = {
  name: 'specgraph-back',
  description: 'Spec-driven graph, back half: plan, implement, check with a fix loop, merge into the wave branch',
  whenToUse: 'Run with the args printed by `python -m specgraph next <repo>` when it says specgraph-back',
  phases: [
    { title: 'Plan', detail: 'plan.md and tasks.md per story, in its own worktree' },
    { title: 'Implement', detail: 'code and tests per story' },
    { title: 'Check', detail: 'independent check per acceptance criterion; fix loop' },
    { title: 'Merge', detail: 'merge passed stories into the wave branch' },
  ],
}

// args: {wave, wave_branch, integration_branch, repo, specs_dir, context, worktrees, setup: [cmd], check: [cmd],
//        max_fix_rounds, stories: [{id, title, path, depends_on}]}
const A = args
const wt = s => `${A.worktrees}/${s.id}`
const br = s => `specgraph/${s.id}`
const docs = s => `${wt(s)}/${A.specs_dir}/${s.id}`
const contextList = A.context.join(', ')
const setupCmds = A.setup.length ? A.setup.join(' && ') : '(none)'
const checkCmds = A.check.join(' && ')

const IN_WT = s => `Work only in the git worktree ${wt(s)} on branch ${br(s)}. Do not touch ${A.repo} itself or other worktrees.
Project context files (relative to the worktree): ${contextList}. Story file: ${s.path}.`

const CHECK = {
  type: 'object',
  properties: {
    passed: { type: 'boolean', description: 'true only if every check command passed and every criterion is met' },
    commands_green: { type: 'boolean' },
    criteria: {
      type: 'array',
      items: {
        type: 'object',
        properties: { id: { type: 'string' }, pass: { type: 'boolean' }, evidence: { type: 'string' } },
        required: ['id', 'pass', 'evidence'],
      },
    },
    problems: { type: 'array', items: { type: 'string' }, description: 'each a concrete, fixable problem' },
  },
  required: ['passed', 'commands_green', 'criteria', 'problems'],
}

const plan = s => agent(
  `You plan one backlog story.

First create its worktree: git -C ${A.repo} worktree add ${wt(s)} -b ${br(s)} ${A.wave_branch}
(If ${wt(s)} already exists, reuse it.)

${IN_WT(s)}
Read ${A.specs_dir}/${s.id}/spec.md, questions.md and answers.md (the product owner's answers win over the spec), then the code.

Write ${docs(s)}/plan.md: files to add or change, data contracts, and a test plan that maps each acceptance criterion (AC-n) to at least one offline test.
Write ${docs(s)}/tasks.md: ordered steps, each small, each with a "done when" line.
If answers.md changes the spec, update spec.md to match.
Commit these files on ${br(s)} with message "${s.id}: plan".`,
  { label: `plan:${s.id}`, phase: 'Plan' })

const implement = s => agent(
  `You implement one backlog story by following its tasks.

${IN_WT(s)}
Read ${A.specs_dir}/${s.id}/spec.md, answers.md, plan.md, tasks.md.
Setup, once: cd ${wt(s)} && ${setupCmds}
Do the tasks in order. Write the tests from the plan. Tests must run offline.
Run until green: cd ${wt(s)} && ${checkCmds}
Tick each task in tasks.md as you finish it. Commit on ${br(s)} with messages starting "${s.id}: ".
Do not change files outside the story's scope, and do not edit other stories' specs.
Return a short summary: what you built and anything you could not finish.`,
  { label: `implement:${s.id}`, phase: 'Implement' })

const check = (s, round) => agent(
  `You independently check one implemented story. You did not write it. Do not edit any file.

${IN_WT(s)}
1. Run: cd ${wt(s)} && ${checkCmds}
2. Read the story file and ${A.specs_dir}/${s.id}/spec.md and answers.md. Read the diff: git -C ${wt(s)} diff ${A.wave_branch}...HEAD
3. For every acceptance criterion AC-n, decide if the code meets it, and give evidence: the test that proves it, or what is wrong.
   Also run the CLI by hand where a criterion is about CLI behaviour, using offline inputs only.
4. List concrete problems, including scope drift (changes the spec does not ask for) and story criteria the spec missed.

passed = every command green and every criterion met.`,
  { label: `check:${s.id}:r${round}`, phase: 'Check', schema: CHECK })

const fix = (s, verdict, round) => agent(
  `You fix the problems an independent check found in one story.

${IN_WT(s)}
Problems:
${verdict.problems.map(p => `- ${p}`).join('\n')}
Failing criteria: ${verdict.criteria.filter(c => !c.pass).map(c => `${c.id} (${c.evidence})`).join('; ') || 'none'}

Fix them, keep the spec as the source of truth, run until green: cd ${wt(s)} && ${checkCmds}
Commit on ${br(s)} with message "${s.id}: fix round ${round}".`,
  { label: `fix:${s.id}:r${round}`, phase: 'Check' })

const checkLoop = async s => {
  let round = 0
  let verdict = await check(s, round)
  while (verdict && !verdict.passed && round < A.max_fix_rounds) {
    round += 1
    await fix(s, verdict, round)
    verdict = await check(s, round)
  }
  return { id: s.id, passed: !!(verdict && verdict.passed), rounds: round, criteria: verdict ? verdict.criteria : [], problems: verdict ? verdict.problems : ['check failed to run'] }
}

const done = await pipeline(A.stories, plan, (_, s) => implement(s), (_, s) => checkLoop(s))
const outcome = done.map((r, i) => r || { id: A.stories[i].id, passed: false, rounds: 0, criteria: [], problems: ['pipeline failed'] })

// Barrier: merging needs every story's outcome, in dependency order.
const passed = A.stories.filter(s => outcome.find(o => o.id === s.id).passed)
let merged = []
if (passed.length) {
  const res = await agent(
    `You merge finished story branches into the wave branch.

In ${A.repo}: git checkout ${A.wave_branch}
Merge in this order, each with git merge --no-ff: ${passed.map(br).join(', ')}
Resolve any conflict so both stories keep working. Then run: cd ${A.repo} && ${setupCmds} && ${checkCmds}
If a merge cannot be made green, abort that merge (git merge --abort, or reset to before it) and leave it out.
Then remove the worktrees of merged stories: git -C ${A.repo} worktree remove --force <path>, for ${passed.map(wt).join(', ')}.
Return the ids you merged.`,
    { label: 'merge', phase: 'Merge', schema: { type: 'object', properties: { merged: { type: 'array', items: { type: 'string' } } }, required: ['merged'] } })
  merged = res ? res.merged : []
}

const stories = outcome.map(o => ({ ...o, merged: merged.includes(o.id) }))
log(stories.map(s => `${s.id}: ${s.passed ? 'passed' : 'failed'} after ${s.rounds} fix round(s), ${s.merged ? 'merged' : 'not merged'}`).join('; '))
return { kind: 'back', wave: A.wave, stories }
