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
- Disabled kube-prometheus scraping for controller-manager, scheduler, and kube-proxy because those
  component endpoints are not exposed by this k3s control plane.
