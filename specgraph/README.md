# specgraph

A spec-driven graph that works through a backlog of markdown stories. Each story goes through
specify, clarify, the product owner's answers, plan, implement, check (with a fix loop) and merge.

- `specgraph/` is a small Python CLI with no dependencies. It reads the target repo's
  `.specgraph/config.json` and stories, computes waves from story dependencies, keeps
  `specs/<id>/status.json`, and prints the input for the next workflow run.
- `../.claude/workflows/specgraph-front.js` runs specify and clarify.
- `../.claude/workflows/specgraph-back.js` runs plan, implement, check, fix and merge.

The design is in the Claude Doc "Spec-driven graph for greenrun: design".

## Loop

```
python -m specgraph plan   <repo>                    # waves and phases
python -m specgraph next   <repo> --prepare [--only ID ...]
#   -> run the named workflow with the printed args
python -m specgraph record <repo> result.json [--tokens N]
#   -> commits specs/<id>/status.json; repeat `next`
```

`next` says `await_answers` when a story has blocking questions: fill `specs/<id>/answers.md`
(replace each TODO), then run `next` again. It says `open_pr` when the wave branch is ready.

## Config

| Key | Meaning |
|---|---|
| `stories` | glob for story files, relative to the repo |
| `id_pattern` | regex whose first group is the story id, matched on the file name |
| `context` | files every agent reads first |
| `depends_on` | `{id: [ids]}`; a story's own front matter `depends_on: [..]` wins. None at all = file order |
| `setup`, `check` | shell commands to build and to decide green |
| `base_branch`, `integration_branch` | where work starts; waves land on `<integration>-w<n>` then merge into it |
| `worktree_dir` | where story worktrees go (default: next to the repo) |
| `max_parallel`, `max_fix_rounds` | limits |

Tests: `python -m pytest -q` in this folder.
