# Documentation

Use this index to load only the context needed for a task. A current manifest remains the source of
truth for exact deployed configuration; these documents define stable intent, boundaries, and
repeatable procedures.

## Root documents

- [`../README.md`](../README.md): project purpose, current scope, and quick start.
- [`../AGENTS.md`](../AGENTS.md): concise working rules and context router.
- [`../ROADMAP.md`](../ROADMAP.md): future work and current priorities only.
- [`../CHANGELOG.md`](../CHANGELOG.md): completed work and documentation history.

## Architecture

- [`architecture/overview.md`](architecture/overview.md): app-of-apps hierarchy, repository boundaries,
  environments, dependency flow, and external traffic.

## Operations

- [`operations/bootstrap.md`](operations/bootstrap.md): one-time Argo bootstrap, secret prerequisites,
  and recovery checks.
- [`operations/postgres-restore.md`](operations/postgres-restore.md): tested monthly backup restore
  procedure and disposable-target safety boundary.
- [`operations/application-onboarding.md`](operations/application-onboarding.md): supported workflow and
  acceptance checklist for a new workload.
- [`operations/monitoring.md`](operations/monitoring.md): monitoring components, collection behavior,
  alerting boundary, persistence, and live verification.

## Development

- [`development/validation.md`](development/validation.md): local documentation, Helm, and Kustomize
  checks.
- [`development/agent-workflow.md`](development/agent-workflow.md): safe workflow for coding agents and
  operational evidence.

## Documentation rules

- One fact has one canonical home; other documents link to it.
- The root README summarizes the repository and routes readers to deeper documentation.
- Stable component and dependency boundaries belong in `architecture/`.
- Repeatable cluster administration and onboarding procedures belong in `operations/`.
- Engineering and agent procedures belong in `development/`.
- Future work belongs in `ROADMAP.md`; completed work belongs in `CHANGELOG.md`.
- Exact versions, resource limits, hosts, and flags should be read from manifests instead of duplicated
  across several documents unless a procedure depends on them.
- Never include real credentials, tokens, kubeconfig data, or Secret payloads in documentation.
