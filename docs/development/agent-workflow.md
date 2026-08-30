# Agent workflow

## Start safely

1. Read `AGENTS.md` and the one canonical document relevant to the task.
2. Inspect `git status` and preserve unrelated edits.
3. Determine whether the request is review-only or authorizes implementation.
4. Inspect remote-Git and live-cluster state separately when deployment evidence is required.

## Implement narrowly

- Make declarative changes in the owning layer: cluster composition, workload chart, or shared
  infrastructure.
- Do not insert real credentials into manifests, commands, logs, or reports.
- Do not use destructive Argo replace or Kubernetes deletion as a routine repair technique.
- Keep review findings in `ROADMAP.md` until implementation is explicitly authorized.
- Update the canonical document when a stable architecture or procedure changes.

## Validate

Run:

```powershell
& .\scripts\validate.ps1
```

For operational changes, add focused live checks appropriate to the resource. A useful evidence chain
is:

```text
local render
  -> commit and push
     -> Argo sync
        -> Kubernetes resource health
           -> endpoint or user-visible behavior
```

Report the furthest layer actually verified. Do not label an unexecuted or blocked layer as passing.

## Finish

- Summarize changed files and the behavior they document or implement.
- State validation commands and actual results.
- Keep incomplete work, environmental blockers, and optional recommendations distinct.
- Record shipped platform changes in `CHANGELOG.md` and remove completed work from `ROADMAP.md`.
