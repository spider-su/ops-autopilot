# Roadmap

Future work based on the architecture and implementation review completed on 2026-08-30. Completed work
belongs in [`CHANGELOG.md`](CHANGELOG.md). Items are sized **S** (up to half a day), **M** (one to two
days), and **L** (multi-day).

## Priority queue

- [ ] **P0 - Restore trustworthy monitoring:** repair node-exporter reachability on two nodes, align
  collection intervals with enabled queries and rules, remove k3s-inapplicable alerts, and configure an
  intentional notification path.
- [ ] **P1 - Make secrets declarative:** replace empty Secret scaffolds and manual data injection with
  SOPS/age, Sealed Secrets, External Secrets, or another selected GitOps-compatible mechanism.
- [ ] **P1 - Add PostgreSQL backup and tested restore:** PVC durability and a PDB are not backups.
- [ ] **P2 - Harden workload contracts:** add pod/container security contexts, compatible quotas, and
  least-privilege networking.
- [ ] **P2 - Add continuous manifest validation:** run documentation, Helm, Kustomize, Kubernetes
  schema, secret, and immutable-image checks in CI.
- [ ] **P3 - Remove unused platform surface:** retain only components with a documented consumer and
  ownership model.

## Theme A - Monitoring reliability

| Item | Effort | Evidence and target outcome |
|---|---:|---|
| Repair node-exporter target reachability | M | Prometheus observed timeouts for `192.168.1.201:9100` and `192.168.1.203:9100`, while only `192.168.1.202:9100` was up. Diagnose node firewall/routing/listener reachability and verify all targets from Prometheus. |
| Select one coherent collection profile | M | Twenty targets used the global six-minute interval while three cAdvisor targets still used 10 seconds. Choose actionable monitoring or a deliberately passive profile and make endpoint overrides consistent. |
| Reconcile rule windows with scrape intervals | M | Enabled upstream rules and dashboards contain two- and five-minute ranges that cannot reliably calculate rates for six-minute samples. Lengthen windows or shorten intervals, then validate rule results. |
| Decide Prometheus and Alertmanager persistence | M | Both currently use ephemeral storage. Add RBD-backed claims if history and alert continuity must survive Pod recreation; explicitly document the ephemeral choice otherwise. |
| Move homelab rules to monitoring ownership | S | `infrastructure/home-lab-alerts.yaml` depends on monitoring CRDs but is owned by the mixed infrastructure Application. Create a later-wave monitoring-rules Application or local monitoring wrapper. |
| Add application metrics discovery contracts | M | NetworkPolicy ingress from `monitoring` does not create scrape targets. Define ServiceMonitor/PodMonitor conventions and expose metrics only for apps that implement them. |
| Tune Grafana startup/readiness from evidence | S | Recent readiness and liveness failures occurred during startup. Keep the extended liveness allowance, inspect readiness semantics, and tune based on measured startup behavior. |

## Theme B - App-of-apps lifecycle and ordering

| Item | Effort | Why |
|---|---:|---|
| Split the mixed infrastructure Application | M | MetalLB resources, storage, Argo configuration, ingress, PVCs, and PrometheusRule objects have different providers and lifecycles. Smaller Applications would clarify ownership and waves. |
| Remove the global Kustomize load-restriction exception | M | Normal `kubectl kustomize clusters/prd` fails because it references files above the cluster directory. Reorganize environment overlays so standard local rendering works without controller-wide `LoadRestrictionsNone`. |
| Separate platform and workload AppProjects | M | `base-app` permits every configured repository, every namespace, and every cluster-scoped kind. Give platform Applications privileged scope and limit workload Applications to their sources and destinations. |

## Theme C - Releases, environments, and onboarding

| Item | Effort | Why |
|---|---:|---|
| Reconcile shared PostgreSQL documentation and files | S | `applications/postgres/app-dev.yaml` exists even though the architecture states that development shares the production PostgreSQL instance. Remove it or document a deliberate alternative. |
| Automate application promotion | M | Add a controlled CI or dependency-update workflow that publishes an immutable image reference and changes the GitOps repository through review. |

## Theme D - Workload reliability and security

| Item | Effort | Why |
|---|---:|---|
| Add pod and container security contexts | M | Define non-root execution where supported, dropped capabilities, no privilege escalation, seccomp, and read-only root filesystems where compatible. |
| Add automated PostgreSQL backup and restore verification | L | Schedule backups to independent storage, define retention, and periodically prove restoration into a disposable instance. |

## Theme E - Secrets and operational safety

| Item | Effort | Why |
|---|---:|---|
| Adopt encrypted declarative secrets | M | Empty Secret scaffolds plus ignored `/data` fields create first-sync races and manual state outside Git. Select and document the decryption/key-recovery boundary. |
| Remove Secret scaffolds after migration | S | Prevent Argo from creating invalid empty credentials before the operator or secret controller supplies data. |
| Add secret scanning | S | Block committed environment files, Secret payloads, private keys, tokens, and high-confidence credentials. |
| Document credential rotation and recovery | M | Cover Ceph, PostgreSQL, applications, Grafana, notification receivers, and GitOps decryption keys without recording their values. |

## Theme F - Platform simplification

| Item | Effort | Why |
|---|---:|---|
| Resolve metrics-server ownership | S | `clusters/prd/metrics-server.yaml` is not registered, while the live Deployment is owned by the k3s packaged-addon controller. Choose k3s ownership or Argo ownership and remove the other path. |
| Reassess cert-manager | S | No Issuer, Certificate, or in-cluster TLS consumer was found because Traefik terminates TLS externally. Remove it unless a planned consumer exists. |
| Reassess CephFS | S | The driver is installed, but no CephFS StorageClass or workload consumer is defined. Remove it or document and validate its use case. |
| Remove or assign `platform-storage` | S | The PVC is bound but no repository workload consumes it. |
| Tune Ceph CSI provisioner replicas | M | Both CSI charts currently run three multi-container provisioner Pods. Measure failure tolerance and resource cost before selecting a lower homelab replica count. |
| Reassess SmartApp redundancy | S | Two nginx replicas, a PDB, and topology spreading may be appropriate, but should reflect an actual availability requirement rather than template inheritance. |

## Theme G - Validation and documentation

| Item | Effort | Why |
|---|---:|---|
| Add Kubernetes schema validation | M | Run kubeconform or an equivalent validator with the Argo CD and monitoring CRD schemas needed by this repository. |
| Render pinned upstream charts in CI | M | Local workload lint does not prove that values still match the pinned upstream chart schemas. |
| Add policy checks | M | Validate immutable production images, resources, probes, namespace destinations, branch conventions, and absence of dangerous sync options. |
| Keep README and manifests consistent | S | The previous README claimed metrics-server registration, pinned production images, two production replicas, and automatic removal behavior that did not match the implementation. Treat docs drift as a validation failure. |

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
