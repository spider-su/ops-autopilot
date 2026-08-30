# Roadmap

Future work based on the architecture and implementation review completed on 2026-08-30. Completed work
belongs in [`CHANGELOG.md`](CHANGELOG.md). Items are sized **S** (up to half a day), **M** (one to two
days), and **L** (multi-day).

## Priority queue

- [ ] **P0 - Restore trustworthy monitoring:** repair node-exporter reachability on two nodes, align
  collection intervals with enabled queries and rules, remove k3s-inapplicable alerts, and configure an
  intentional notification path.
- [ ] **P1 - Complete encrypted secret migration:** connect SOPS/age decryption to Argo CD and migrate
  all operator-managed Secret payloads without committing plaintext.
- [ ] **P1 - Test PostgreSQL backup restore:** restore the retained monthly dump into a disposable
  PostgreSQL instance and document the verified procedure.
- [ ] **P2 - Harden workload contracts:** add pod/container security contexts, compatible quotas, and
  least-privilege networking.
- [ ] **P3 - Remove unused platform surface:** retain only components with a documented consumer and
  ownership model.

## Theme A - Monitoring reliability

| Item | Effort | Evidence and target outcome |
|---|---:|---|
| Repair node-exporter target reachability | M | Prometheus observed timeouts for `192.168.1.201:9100` and `192.168.1.203:9100`, while only `192.168.1.202:9100` was up. Diagnose node firewall/routing/listener reachability and verify all targets from Prometheus. |
| Add application metrics discovery contracts | M | NetworkPolicy ingress from `monitoring` does not create scrape targets. Define ServiceMonitor/PodMonitor conventions and expose metrics only for apps that implement them. |
| Tune Grafana startup/readiness from evidence | S | Recent readiness and liveness failures occurred during startup. Keep the extended liveness allowance, inspect readiness semantics, and tune based on measured startup behavior. |

## Theme B - App-of-apps lifecycle and ordering

| Item | Effort | Why |
|---|---:|---|

## Theme C - Releases, environments, and onboarding

| Item | Effort | Why |
|---|---:|---|
| Automate application promotion | M | Add a controlled CI or dependency-update workflow that publishes an immutable image reference and changes the GitOps repository through review. |

## Theme D - Workload reliability and security

| Item | Effort | Why |
|---|---:|---|
| Add pod and container security contexts | M | Define non-root execution where supported, dropped capabilities, no privilege escalation, seccomp, and read-only root filesystems where compatible. |

## Theme E - Secrets and operational safety

| Item | Effort | Why |
|---|---:|---|
| Remove Secret scaffolds after migration | S | Prevent Argo from creating invalid empty credentials before the operator or secret controller supplies data. |
| Add secret scanning | S | Block committed environment files, Secret payloads, private keys, tokens, and high-confidence credentials. |
| Document credential rotation and recovery | M | Cover Ceph, PostgreSQL, applications, Grafana, notification receivers, and GitOps decryption keys without recording their values. |

## Theme F - Platform simplification

| Item | Effort | Why |
|---|---:|---|
| Tune Ceph CSI provisioner replicas | M | Both CSI charts currently run three multi-container provisioner Pods. Measure failure tolerance and resource cost before selecting a lower homelab replica count. |
| Reassess SmartApp redundancy | S | Two nginx replicas, a PDB, and topology spreading may be appropriate, but should reflect an actual availability requirement rather than template inheritance. |

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
