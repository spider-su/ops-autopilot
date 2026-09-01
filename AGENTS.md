# AGENTS.md

This is a declarative Argo CD GitOps repository. Keep this file concise and load the canonical document
for the task instead of treating all repository notes as equal sources of truth.

## Working rules

- Inspect `git status` before editing and preserve unrelated changes.
- Treat review requests as read-only unless implementation is explicitly requested.
- Never commit credentials, generated Secret data, kubeconfig content, or local `.env` files.
  Encrypted secrets use SOPS/age; add new secrets to `secrets/` with `.sops.yaml` extension.
- Argo CD reads remote Git. Do not claim a local change is deployed until it is committed, pushed,
  reconciled, and live-verified.
- Keep `applications/` reusable and environment differences in cluster wiring or environment values.
- Production and development Applications use `main`; environment-specific values remain in their
  respective cluster wiring. Do not deploy development values to production unintentionally.
- PostgreSQL is shared in the `postgres` namespace. Do not introduce a second development PostgreSQL
  deployment without an explicit architecture decision.
- Production images must be pinned to registry-resolved SHA-256 digests with `pullPolicy: IfNotPresent`;
  development values remain mutable. All workload charts require `values.schema.json` with strict validation.
- Use pinned versions for production images and upstream Helm charts.
- New resources must target correct AppProject: `platform-app` for platform/infrastructure, `base-app` for
  workload namespaces and namespaced resources. AppProject destinations are validated during `git push`.
- Validate the complete requested edit batch with `scripts/validate.ps1` after implementation.
  The validator checks Markdown links, Helm schemas, image immutability, policy compliance,
  Kubernetes schemas, and Kustomize rendering. All checks must pass before commit.
- Distinguish manifest rendering, Argo sync state, workload health, and user-visible behavior; one does
  not prove the others.

## Context router

- Repository purpose and quick start: [`README.md`](README.md)
- Documentation source-of-truth map: [`docs/README.md`](docs/README.md)
- App-of-apps boundaries and dependency flow:
  [`docs/architecture/overview.md`](docs/architecture/overview.md)
- Bootstrap, credentials, and external network prerequisites:
  [`docs/operations/bootstrap.md`](docs/operations/bootstrap.md)
- New workload onboarding:
  [`docs/operations/application-onboarding.md`](docs/operations/application-onboarding.md)
- Monitoring behavior and verification:
  [`docs/operations/monitoring.md`](docs/operations/monitoring.md)
- Local validation and evidence expectations:
  [`docs/development/validation.md`](docs/development/validation.md)
- Agent workflow: [`docs/development/agent-workflow.md`](docs/development/agent-workflow.md)
- Project review (technical assessment): [`docs/review.md`](docs/review.md)
- Deployment decision (your infrastructure fit): [`docs/deployment-decision.md`](docs/deployment-decision.md)
- Design decisions and intentional constraints: [`docs/architecture/DESIGN-DECISIONS.md`](docs/architecture/DESIGN-DECISIONS.md)
- Planned improvements: [`ROADMAP.md`](ROADMAP.md)
- Completed work: [`CHANGELOG.md`](CHANGELOG.md)
