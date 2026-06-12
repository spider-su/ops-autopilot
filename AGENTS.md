# AGENTS.md â€” AI Agent Guide for ops-autopilot

## Architecture Overview

Argo CD **GitOps repo** for Kubernetes. No build systems â€” all changes are declarative YAML committed to Git.

**Hierarchy:**
```
clusters/{env}/kustomization.yaml   # bootstrap (kubectl apply once)
  â”œâ”€â”€ infra.yaml                    # Argo CD Application â†’ infrastructure/  (prd only)
  â””â”€â”€ {app}.yaml                    # Argo CD Application â†’ applications/{app}/ (Helm chart)
```

`applications/` holds only **Helm charts** â€” no env subfolders.  
`clusters/` holds all env-specific wiring â€” branch, namespace, value overrides.  
`clusters/prd/base-app-project.yaml` is a **single shared AppProject** named `base-app` (`namespace: "*"`) for all apps, applied on prd bootstrap.

## Branch & Namespace Convention

| Cluster | Git Branch | App namespace |
|---------|-----------|---------------|
| `clusters/dev` | `dev` | `{app}-dev` |
| `clusters/prd` | `main` | `{app}-prod` |

Shared services (no env suffix): `postgres`, etc.

**Never deploy dev work on `main`.** Each Application CR in `clusters/dev/` uses `targetRevision: dev`.  
**`prd` must be bootstrapped before `dev`** â€” infra (namespaces, ceph-csi-secret) lives in prd.

## Key Structural Rules

- `clusters/dev/kustomization.yaml` â€” lists only `app-dev.yaml` refs for apps under active development. All others stay untouched in prd.
- `clusters/prd/kustomization.yaml` â€” lists `infrastructure.yaml` + `app-prd.yaml` refs for every app. Adding an entry here auto-deploys to prd.
- Each app's folder `applications/{appname}/` contains everything: Helm chart (`Chart.yaml`, `values*.yaml`, `templates/`) **and** the Application CRs (`app-dev.yaml`, `app-prd.yaml`).
- Application CRs explicitly select env values via `helm.valueFiles: [values.yaml, values-{env}.yaml]`.
- Application CRs set `helm.releaseName: {appname}` (without env suffix) so all Kubernetes resources are named `investory` / `smartapp` â€” the namespace (`investory-prd`, `investory-dev`) provides the env separation. This keeps service DNS clean: `investory.investory-prd.svc.cluster.local`.
- `applications/common-utils/` is a Helm **library** chart (type: library) with shared named templates. Each app copies the helpers into its own `templates/_helpers.tpl` â€” no Helm dependency wiring needed.
- Infra Application (`clusters/prd/infrastructure.yaml`) uses Kustomize to apply `infrastructure/` resources cluster-wide.

## Adding a New Application

1. **Create Helm chart**: `applications/{appname}/` â€” copy `applications/investory/` as template. Update `Chart.yaml` name, fill in `values.yaml`, `values-prd.yaml`, `values-dev.yaml`.
2. **Add Application CRs** in the same folder: `app-prd.yaml` (`targetRevision: main`, `helm.releaseName: {appname}`, `values-prd.yaml`, `namespace: {appname}-prd`) and optionally `app-dev.yaml` (`targetRevision: dev`, `helm.releaseName: {appname}`, `values-dev.yaml`, `namespace: {appname}-dev`).
3. **Register in prd**: add `- ../../applications/{appname}/app-prd.yaml` to `clusters/prd/kustomization.yaml`.
4. **Register in dev** (when needed): add `- ../../applications/{appname}/app-dev.yaml` to `clusters/dev/kustomization.yaml`.

Namespaces are created automatically via `syncOptions: [CreateNamespace=true]` on each Application CR — no separate namespace manifest needed.

## PostgreSQL — Shared Instance, Schema-per-Env

A single `postgres-prd` instance serves all environments. **Do not create a `postgres-dev` deployment.**  
Dev and prd apps are separated by **PostgreSQL schemas**, not by separate instances.

- **Internal DNS:** `postgres.postgres.svc.cluster.local:5432`
- **External access:** `192.168.1.221:5432` (TCP via ingress-nginx)
- **Credentials:** stored in `postgres-credentials` secret in `postgres` namespace — never in git. Apply once:
  ```bash
  kubectl create secret generic postgres-credentials \
    --from-literal=POSTGRES_USER=postgres \
    --from-literal=POSTGRES_PASSWORD=<password> \
    --from-literal=POSTGRES_DB=postgres \
    --namespace=postgres --dry-run=client -o yaml | kubectl apply -f -
  ```
- **Storage:** 10Gi Ceph RBD via `proxmox-ceph-rbd` StorageClass
- **TCP port** 5432 is mapped in `clusters/prd/ingress-nginx.yaml` under `tcp:` — update there if postgres namespace/port ever changes.

## Infra Layer — Connecting Apps to Storage, Ingress, Secrets

Platform Applications in `clusters/prd/` (each is a separate Argo CD Application):
- `infrastructure.yaml` → `infrastructure/` (Kustomize) — `ceph-csi-secret` scaffold, `platform-storage` PVC, `proxmox-ceph-rbd` StorageClass
- `ingress-nginx.yaml` → upstream Helm chart — routes external traffic to app Ingress resources
- `cert-manager.yaml` → upstream Helm chart — TLS certificate management
- `metrics-server.yaml` → upstream Helm chart — enables `kubectl top` and HPA
- `metallb.yaml` → upstream Helm chart — L2 LoadBalancer, IP pool `192.168.1.220-240`, ingress-nginx gets `192.168.1.221`
- `monitoring.yaml` → `prometheus-community/kube-prometheus-stack` — Prometheus + Grafana + Alertmanager
- `ceph-csi-rbd.yaml` → `ceph.github.io/csi-charts/ceph-csi-rbd` — RBD block storage CSI driver (k3s kubelet path configured)
- `ceph-csi-cephfs.yaml` → `ceph.github.io/csi-charts/ceph-csi-cephfs` — CephFS shared storage CSI driver (k3s kubelet path configured)

Namespaces are **not** managed here â€” each Application CR uses `syncOptions: [CreateNamespace=true]` to create its own namespace on first deploy.

**To enable per-app storage** â€” set in `values-prd.yaml` or `values-dev.yaml`:
```yaml
pvc:
  enabled: true
  size: 5Gi          # uses proxmox-ceph-rbd StorageClass automatically
  mountPath: /data
```

**To enable ingress** — set in `values-prd.yaml`:
```yaml
ingress:
  enabled: true
  host: myapp.example.com   # requires ingress-nginx in infra layer
```

**To expose a TCP service** (e.g. a database) — add to `clusters/prd/ingress-nginx.yaml` under `tcp:`:
```yaml
tcp:
  5432: "postgres-prd/postgres:5432"   # port: "namespace/service:port"
```

## Helm Template Helpers (`_helpers.tpl`)

All apps use four named templates defined in `templates/_helpers.tpl` (canonical source: `applications/common-utils/templates/_helpers.tpl`):

| Helper | Output |
|--------|--------|
| `app.name` | `.Release.Name` |
| `app.image` | `repository:tag` |
| `app.labels` | Full K8s label set (`app`, `app.kubernetes.io/*`, `helm.sh/chart`) including `version` from `Chart.AppVersion` |
| `app.selectorLabels` | `app: {name}` only â€” stable, never changes after first deploy |

## Operational Commands

```bash
# Bootstrap (prd first, then dev) — one-time only per cluster
kubectl apply -f clusters/prd/parent-app.yaml
kubectl apply -f clusters/dev/parent-app.yaml

# After bootstrap, adding/removing apps is automatic:
# - Add: commit new app-prd.yaml ref to clusters/prd/kustomization.yaml → Argo CD creates it
# - Remove: remove ref from kustomization.yaml → Argo CD prunes the Application + its resources

# Set Ceph credentials after prd bootstrap (not stored in git — run once)
kubectl create secret generic ceph-csi-secret \
  --from-literal=userID=admin \
  --from-literal=userKey=$(ceph auth get-key client.admin) \
  --namespace=default --dry-run=client -o yaml | kubectl apply -f -

# Set postgres credentials (not stored in git — run once)
kubectl create secret generic postgres-credentials \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=<password> \
  --from-literal=POSTGRES_DB=postgres \
  --namespace=postgres-prd --dry-run=client -o yaml | kubectl apply -f -

# Check all Argo CD Applications
kubectl get applications -n argocd

# Debug a sync failure
kubectl describe application <name> -n argocd
kubectl logs -n argocd deploy/argocd-repo-server
```

## Repo: `https://github.com/spider-su/ops-autopilot.git`
