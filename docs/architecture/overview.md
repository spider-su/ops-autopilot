# Architecture overview

## Purpose

The repository provides a deliberately small GitOps control plane for one k3s homelab. Its primary
design goal is easy, repeatable onboarding of applications without turning the repository into a
general-purpose platform framework.

## Control flow

```text
operator applies one parent Application
  -> parent reads an environment kustomization from Git
     -> kustomization creates child Argo CD Applications
        -> each child reconciles an upstream chart, a local chart, or Kustomize resources
           -> Kubernetes controllers converge workloads and platform services
```

The parent Application manages child `Application` resources, not application Pods directly. Each
child independently reports sync and health state.

## Repository boundaries

### `clusters/`

Environment composition belongs here:

- Git revision and namespace selection.
- Registration of platform and workload Applications.
- Upstream platform chart configuration.
- The parent Application used for bootstrap.

### `applications/`

Each workload directory contains one reusable Helm chart and environment value files. Environment
directories under `clusters/` own Argo CD Application wiring. A chart owns namespaced workload
resources such as Deployments, Services, Ingresses, PVCs, NetworkPolicies, and ResourceQuotas.

### `infrastructure/`

The `infrastructure/platform` Kustomize target owns storage and MetalLB resources. The
`infrastructure/argocd` target owns Argo CD configuration and ingress. The separate
`infrastructure/monitoring` target owns homelab alert rules. Each target is reconciled by its own Argo
Application so resources with different lifecycles have explicit ownership.

## Environment model

| Environment | Git revision | Workload namespace |
|---|---|---|
| Production | `main` | `<app>-prod` |
| Development | `main` | `<app>-dev` |
| Shared services | normally `main` | service name, for example `postgres` |

Development is optional and contains the active SmartApp workload. Investory remains registered in dev
with zero replicas for environment parity, while production is its active environment. Production keeps
the SmartApp counterpart registered with zero replicas. Both environments use one branch; values files
and cluster wiring carry the environment differences.

## Naming and service discovery

Application resources use `helm.releaseName: <app>`, without the environment suffix. The namespace
provides isolation, so stable in-cluster DNS remains concise, for example:

```text
investory.investory-prod.svc.cluster.local
postgres.postgres.svc.cluster.local
```

## Traffic path

```text
browser
  -> Traefik on the Pi-hole host (TLS termination)
     -> ingress-nginx LoadBalancer over HTTP
        -> application Ingress
           -> Service
              -> Pod
```

Pi-hole DNS and the Traefik dynamic configuration are external dependencies and are not reconciled by
this repository.

## Storage and database

- Ceph CSI RBD supplies the workload storage driver; no CephFS StorageClass or workload consumer is
  managed by this repository.
- `proxmox-ceph-rbd` is the workload StorageClass managed by this repository.
- PostgreSQL is a single shared StatefulSet with an RBD-backed PVC.
- `infrastructure/platform-storage` is a deliberately reserved 5 GiB RBD-backed PVC with no current
  workload consumer; retain it until an explicit storage cleanup decision is made.
- Prometheus and Alertmanager use separate RBD-backed claims for short-term operational state. PostgreSQL
  writes one monthly custom-format dump to a separate 10 GiB RBD claim and retains only the newest dump.
- SmartApp runs one development replica for active testing; its production counterpart is registered but
  scaled to zero. This is an environment-placement choice, not a high-availability guarantee.
- Investory runs one production replica; its production namespace quota allows a temporary second pod
  during rolling replacement. Its inactive development counterpart remains at zero replicas.
- PostgreSQL is a single StatefulSet replica on shared Ceph RBD. It deliberately has no PDB: a
  `minAvailable: 1` budget would not add redundancy and would prevent voluntary node maintenance.
- Ingress-NGINX remains two replicas with `minAvailable: 1`, which is meaningful because one replica can
  continue serving while the other is disrupted.
- Ceph CSI RBD uses two provisioner replicas after measuring three live Pods at approximately 9–22m CPU
  and 104–147Mi memory each; nodeplugin remains one DaemonSet Pod per node.
- PostgreSQL retains the restricted capability exception required by the official image entrypoint to
  initialize ownership on the Ceph-mounted data directory; the application containers retain the
  drop-all-capabilities baseline. The exception also includes `SETUID` and `SETGID` so the entrypoint
  can drop from root to the PostgreSQL user.
- PostgreSQL ingress is restricted by an explicit namespace allowlist in its chart values. TCP port 5432
  is intentionally exposed through the private-LAN ingress-nginx LoadBalancer for operator-PC testing;
  this is not an Internet exposure or TLS boundary.
- Environment separation inside PostgreSQL is an application/schema concern; this repository does not
  currently provision one database server per environment.

## Reconciliation and ownership boundary

Argo CD reconciles the remote repository, not a developer's working tree. Rendering proves that YAML
can be generated; an Argo `Synced` state proves desired objects match Git; workload `Healthy` state and
application behavior require additional evidence. Platform and stateless child Applications carry Argo's
resources finalizer so an intentional manifest removal cascades their resources. The PostgreSQL child is
deliberately excluded from that finalizer to protect stateful data; removing it requires an explicit
operator cleanup and backup decision.

Child Application dependency order is explicit through sync-wave annotations. Remaining security,
environment-model, monitoring, and storage improvements are tracked in
[`../../ROADMAP.md`](../../ROADMAP.md).

Platform Applications use the privileged `platform-app` AppProject with explicit platform destinations
and cluster-resource allowlists. Workload Applications use the constrained `base-app` AppProject, which
allows only the application namespaces and namespaced workload resource kinds.

Application Pods use the compatible security baseline of `RuntimeDefault` seccomp, no privilege
escalation, and all Linux capabilities dropped. Non-root execution and read-only root filesystems remain
compatibility follow-ups for images whose entrypoints and writable paths have been verified.

Application egress permits DNS only to `kube-system`, PostgreSQL only through its namespace and port,
and same-namespace traffic where required. Investory intentionally retains broad public egress because
the application owner controls the service and its external integrations; this is an accepted private
homelab tradeoff rather than an accidental allowlist omission. Revisit it if the trust boundary or
deployment model changes.
