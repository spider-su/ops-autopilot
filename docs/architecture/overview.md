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

Each workload directory contains one Helm chart plus its Argo CD Application resources and environment
value files. A chart owns namespaced workload resources such as Deployments, Services, Ingresses,
PVCs, NetworkPolicies, and ResourceQuotas.

### `infrastructure/`

This Kustomize target owns cluster-wide and cross-cutting resources that are not naturally part of a
single workload chart, including storage, MetalLB configuration, Argo CD configuration and ingress,
and home-lab alert rules.

## Environment model

| Environment | Git revision | Workload namespace |
|---|---|---|
| Production | `main` | `<app>-prod` |
| Development | `dev` | `<app>-dev` |
| Shared services | normally `main` | service name, for example `postgres` |

Development is optional and contains only actively developed applications. Production owns shared
platform infrastructure. Branch consolidation is a planned improvement, not current behavior.

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

- Ceph CSI supplies RBD and CephFS drivers.
- `proxmox-ceph-rbd` is the workload StorageClass managed by this repository.
- PostgreSQL is a single shared StatefulSet with an RBD-backed PVC.
- PostgreSQL ingress is restricted by an explicit namespace allowlist in its chart values; external TCP
  exposure through ingress-nginx remains a separate operational security decision.
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
