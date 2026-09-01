# Roadmap

Future work based on the architecture and implementation review completed on 2026-08-30. Completed work
belongs in [`CHANGELOG.md`](CHANGELOG.md). Items are sized **S** (up to half a day), **M** (one to two
days), and **L** (multi-day).

## Priority queue

All previously queued roadmap items are complete. The next item should be added here only when a new
evidence-backed operational or architecture need is identified.

## Theme A - Monitoring reliability

| Item | Effort | Evidence and target outcome |
|---|---:|---|

## Theme B - App-of-apps lifecycle and ordering

| Item | Effort | Why |
|---|---:|---|

## Theme C - Releases, environments, and onboarding

| Item | Effort | Why |
|---|---:|---|

## Theme D - Workload reliability and security

| Item | Effort | Why |
|---|---:|---|

## Theme E - Secrets and operational safety

| Item | Effort | Why |
|---|---:|---|

## Theme F - Platform simplification

| Item | Effort | Why |
|---|---:|---|

## Theme G - Validation and documentation

| Item | Effort | Why |
|---|---:|---|

## Intentional Non-Goals

These capabilities are deliberately excluded. The repository is scoped to serve a single-operator homelab
without growing into a multi-tenant platform.

### Policy Enforcement

- **No Kyverno policy layer.** CI validation via `scripts/validate.ps1` catches schema, image, and
  AppProject violations before Git. For a single operator, manual validation is sufficient and avoids
  runtime policy complexity. Reconsider if operators multiply or untrusted deployments are accepted.

### Storage Operations

- **No Ceph RBD snapshots.** Workloads are stateless except PostgreSQL; PVCs are either backed by a
  single application (PostgreSQL, Prometheus, Alertmanager) or unused. Monthly PostgreSQL dump-based
  backup provides point-in-time recovery. Reconsider if durable multi-tenant stateful workloads are
  added.

### Observability

- **Limited Argo CD observability.** Manual Argo UI inspection is sufficient for 2-5 applications; each
  Application independently reports sync and health. Reconsider deep metrics/alerting if scaling beyond
  5 applications or if multi-operator access requires audit trails.

### Testing

- **No application-specific test suite.** Unit and integration tests belong in application repositories,
  not in this cluster repository. Repository validation checks schema, policy, and Kubernetes manifest
  compliance. Workload behavior testing is out of scope for cluster operations.

### Cost Tracking

- **No cost tracking or resource attribution.** Proxmox licensing is static; Ceph hardware cost is
  amortized across the entire homelab. Cost per application is irrelevant for hobby infrastructure.
  Reconsider if this cluster serves chargeback or capacity planning across multiple cost centers.

## Explicitly deferred

- **ApplicationSet migration.** With only a few applications, explicit Application resources remain
  easier to understand. Reconsider when duplication or application count becomes material.
- **A general platform framework.** Keep onboarding conventions small and homelab-specific; do not add
  abstractions without at least two real consumers.
- **High-availability PostgreSQL.** Backups and tested recovery take priority over introducing a
  database operator for a single-owner homelab.

## How to use this file

- Implement one bounded roadmap item per change when practical.
- Recheck live evidence before acting on observations that can drift.
- Move shipped work to `CHANGELOG.md`.
- Update the canonical architecture or operations document when a stable boundary changes.
- Keep findings, accepted tradeoffs, and completed work distinct.
