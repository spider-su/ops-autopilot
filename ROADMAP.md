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
