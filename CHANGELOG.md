# Changelog

Completed repository-level documentation and platform changes are recorded here. Future work remains in
[`ROADMAP.md`](ROADMAP.md).

## 2026-08-30

- Reorganized documentation around a canonical index with architecture, operations, onboarding,
  monitoring, validation, and agent-workflow documents.
- Added project-local Codex actions and repository helper files for repeatable documentation, Helm, and
  Kustomize checks.
- Consolidated the architecture review findings into the roadmap without changing runtime manifests.
- Added explicit Argo sync waves for platform, infrastructure, database, and workload Applications.
- Added cascading deletion finalizers for platform/stateless Applications while preserving PostgreSQL
  from accidental cascade deletion.
- Added configurable startup, readiness, and liveness probes to Investory and SmartApp, and disabled
  unused service-account token mounts for application and PostgreSQL Pods.
- Aligned Investory development resources with its namespace quota and corrected the production quota
  comment.
- Added digest-aware image helpers and pinned all production workload images to registry-resolved
  immutable digests; development remains mutable by design.
- Added `values.schema.json` to all workload charts so Helm lint rejects unknown keys and invalid image,
  port, probe, resource, storage, quota, and policy values before deployment.
- Added a GitHub Actions validation workflow that runs the repository validator on `main`, `dev`, and
  pull requests.
- Extended repository validation with chart policy checks for required schemas and immutable production
  image digests with `IfNotPresent` pull policy.
- Restricted PostgreSQL NetworkPolicy ingress to the explicitly documented application, ingress, and
  monitoring namespaces instead of allowing every namespace.
- Made application external egress destinations explicit and configurable via
  `networkPolicy.externalEgressCidrs`; SmartApp defaults to no external egress.
- Declared Kubernetes 1.25+ compatibility in every application chart to make API-version assumptions
  visible during Helm lint and install.
- Disabled the unconfigured Alertmanager component so monitoring does not imply notifications that are
  silently discarded; re-enable it when a real receiver is selected.
- Disabled kube-prometheus default rule groups for controller-manager, scheduler, and kube-proxy, which
  are not exposed by this k3s control plane and otherwise generate persistent false positives.
- Aligned kubelet, cAdvisor, and probe scraping with the intentional 60-second bounded-resource
  monitoring profile instead of retaining the chart's separate 10-second cAdvisor interval.
- Set Prometheus collection and rule evaluation to 60 seconds so enabled upstream 2-minute and
  5-minute queries have multiple usable samples.
- Moved homelab Prometheus rules into a dedicated monitoring-rules Application ordered after the
  monitoring CRDs, removing them from the mixed infrastructure Application.
- Removed the unused metrics-server Argo Application manifest and repository allowlist entry so
  ownership remains with the k3s packaged add-on.
- Removed cert-manager because no in-cluster certificate consumer exists; TLS remains terminated by
  the external Traefik boundary.
- Removed the unused CephFS CSI Application because no CephFS StorageClass or workload consumer exists;
  the RBD driver remains the managed storage path.
- Retained and documented the unused `infrastructure/platform-storage` PVC as reserved Ceph RBD storage
  rather than pruning its bound volume.
- Disabled kube-prometheus scraping for controller-manager, scheduler, and kube-proxy because those
  component endpoints are not exposed by this k3s control plane.
- Split platform storage/MetalLB and Argo CD configuration into separate infrastructure Applications;
  monitoring rules were already isolated into their own Application.
- Added separate AppProject boundaries: `platform-app` is restricted to platform sources and
  destinations, while `base-app` is limited to workload namespaces and namespaced resource kinds.
- Consolidated environment sources on `main`; production and development retain separate values and
  namespaces without relying on a drifting `dev` branch.
- Removed the unused `common-utils` Helm library; workload charts now own their independently rendered
  helper templates without a misleading unsynchronized dependency.
- Added a compatible application security baseline: RuntimeDefault seccomp, disabled privilege
  escalation, and dropped Linux capabilities for SmartApp, Investory, and PostgreSQL containers.
- Scoped application DNS egress to kube-dns Pods in `kube-system`; public Investory egress remains an
  explicitly documented compatibility exception pending an endpoint allowlist decision.
- Documented PostgreSQL TCP exposure through the private-LAN ingress-nginx LoadBalancer as intentional
  operator-PC testing access, not an Internet-facing or TLS boundary.
