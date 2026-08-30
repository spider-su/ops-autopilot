# ops-autopilot

`ops-autopilot` is a small Argo CD GitOps repository for a three-node k3s homelab. A single parent
Application discovers platform and workload Applications, while Helm values keep environment-specific
configuration out of the reusable workload templates.

## What this repository manages

- Argo CD app-of-apps bootstrap for production and development.
- Homelab platform services: MetalLB, ingress-nginx, Ceph CSI, monitoring, and supporting infrastructure.
- Shared PostgreSQL and the Investory and SmartApp workloads.
- Namespace creation, resource quotas, network policies, ingress, storage, and pinned platform chart
  versions.

## Deployment model

```text
clusters/prd/parent-app.yaml
  -> clusters-prd Application
     -> clusters/prd/kustomization.yaml
        -> platform Applications
        -> shared-service Applications
        -> workload Applications
```

The production parent reads `main`; the development parent currently reads `dev`. Child Applications
reconcile either an upstream Helm chart or a chart under `applications/`. Argo CD reads the remote Git
repository, so local edits do not affect the cluster until they are committed, pushed, and reconciled.

The canonical architecture and dependency description is
[`docs/architecture/overview.md`](docs/architecture/overview.md).

## Repository layout

| Path | Responsibility |
|---|---|
| `clusters/` | Environment entry points and Argo CD Application wiring. |
| `applications/` | Reusable workload Helm charts and environment values. |
| `clusters/` | Environment-specific Argo Application wiring and bootstrap resources. |
| `infrastructure/` | Cluster-scoped and cross-cutting Kustomize resources. |
| `docs/` | Canonical architecture, operations, onboarding, monitoring, and validation documentation. |
| `.codex/` | Project-local Codex configuration and repeatable actions. |

## Bootstrap

Production infrastructure must exist before optional development workloads are bootstrapped:

```bash
kubectl apply -f clusters/prd/parent-app.yaml
kubectl apply -f clusters/dev/parent-app.yaml
```

Bootstrap also requires operator-managed Ceph and PostgreSQL credentials. Follow
[`docs/operations/bootstrap.md`](docs/operations/bootstrap.md); do not commit secrets or copy credentials
into documentation.

## Add an application

The supported onboarding flow is:

1. Create `applications/<app>/` from the closest existing chart.
2. Replace names, image configuration, ports, resources, and optional capabilities.
3. Add production and, when needed, development Application manifests under the appropriate
   `clusters/<env>/workloads/` directory.
4. Register the manifest in the appropriate cluster kustomization.
5. Render and lint locally before pushing.

The complete contract and checklist are in
[`docs/operations/application-onboarding.md`](docs/operations/application-onboarding.md).

## Validate changes

On Windows:

```powershell
& .\scripts\validate.ps1
```

The helper checks local Markdown links, lints every workload chart, and renders both cluster
kustomizations using the same unrestricted load behavior configured in Argo CD. See
[`docs/development/validation.md`](docs/development/validation.md) for individual commands and known
limitations.

## Current operational scope

- Traffic is terminated by Traefik outside k3s, forwarded over HTTP to ingress-nginx, and routed by
  hostname to Services.
- PostgreSQL is a shared stateful service in the `postgres` namespace.
- Prometheus, Grafana, and Alertmanager are deployed by `clusters/prd/monitoring.yaml`.
- Sensitive values are currently created manually and excluded from Argo CD data diffs.
- Application image promotion is currently manual.

These statements describe the current implementation, not the desired end state. Known design and
operational improvements are intentionally parked in [`ROADMAP.md`](ROADMAP.md).

## Documentation links

- [`AGENTS.md`](AGENTS.md): concise working rules and task-to-document router.
- [`docs/README.md`](docs/README.md): documentation index and source-of-truth map.
- [`docs/architecture/overview.md`](docs/architecture/overview.md): stable GitOps architecture.
- [`docs/operations/bootstrap.md`](docs/operations/bootstrap.md): bootstrap and secret prerequisites.
- [`docs/operations/application-onboarding.md`](docs/operations/application-onboarding.md): new-app
  workflow.
- [`docs/operations/monitoring.md`](docs/operations/monitoring.md): monitoring design and current
  constraints.
- [`ROADMAP.md`](ROADMAP.md): future work only.
- [`CHANGELOG.md`](CHANGELOG.md): completed documentation and platform changes.
