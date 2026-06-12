# AGENTS.md — AI Agent Guide for ops-autopilot

## Architecture Overview

Argo CD **GitOps repo** for Kubernetes. No build systems — all changes are declarative YAML committed to Git.

**Hierarchy:**
```
clusters/prd/parent-app.yaml        # bootstrap (kubectl apply once)
  └── clusters-prd Application      # watches clusters/prd/kustomization.yaml
        ├── platform Application CRs # metallb, ingress-nginx, cert-manager, ...
        └── app Application CRs      # investory-prod, smartapp-prod, postgres, ...
```

`applications/` holds only **Helm charts** — no env subfolders.  
`clusters/` holds all env-specific wiring — branch, namespace, value overrides.  
`clusters/prd/base-app-project.yaml` is a **single shared AppProject** named `base-app` (`namespace: "*"`) for all apps, applied on prd bootstrap.

## Branch & Namespace Convention

| Cluster | Git Branch | App namespace |
|---------|-----------|---------------|
| `clusters/dev` | `dev` | `{app}-dev` |
| `clusters/prd` | `main` | `{app}-prod` |

Shared services (no env suffix): `postgres`, etc.

**Never deploy dev work on `main`.** Each Application CR in `clusters/dev/` uses `targetRevision: dev`.  
**`prd` must be bootstrapped before `dev`** — infra (namespaces, ceph-csi-secret) lives in prd.

## Key Structural Rules

- `clusters/dev/kustomization.yaml` — lists only `app-dev.yaml` refs for apps under active development. All others stay untouched in prd.
- `clusters/prd/kustomization.yaml` — lists all platform Application CRs + `app-prd.yaml` refs for every app. Adding an entry here auto-deploys to prd.
- Each app's folder `applications/{appname}/` contains everything: Helm chart (`Chart.yaml`, `values*.yaml`, `templates/`) **and** the Application CRs (`app-dev.yaml`, `app-prd.yaml`).
- Application CRs explicitly select env values via `helm.valueFiles: [values.yaml, values-{env}.yaml]`.
- Application CRs set `helm.releaseName: {appname}` (without env suffix) so all Kubernetes resources are named `investory` / `smartapp` — the namespace (`investory-prod`, `investory-dev`) provides the env separation. This keeps service DNS clean: `investory.investory-prod.svc.cluster.local`.
- `applications/common-utils/` is a Helm **library** chart (type: library) with shared named templates. Each app copies the helpers into its own `templates/_helpers.tpl` — no Helm dependency wiring needed.
- Infra Application (`clusters/prd/infrastructure.yaml`) uses Kustomize to apply `infrastructure/` resources cluster-wide.
- **app-of-apps**: `clusters/prd/parent-app.yaml` is applied once manually. After that, Argo CD auto-manages all child Applications — adding/removing refs from `kustomization.yaml` is all that's needed.

## Adding a New Application

1. **Create Helm chart**: `applications/{appname}/` — copy `applications/investory/` as template. Update `Chart.yaml` name, fill in `values.yaml`, `values-prd.yaml`, `values-dev.yaml`.
2. **Add Application CRs** in the same folder: `app-prd.yaml` (`targetRevision: main`, `helm.releaseName: {appname}`, `values-prd.yaml`, `namespace: {appname}-prod`) and optionally `app-dev.yaml` (`targetRevision: dev`, `helm.releaseName: {appname}`, `values-dev.yaml`, `namespace: {appname}-dev`).
3. **Register in prd**: add `- ../../applications/{appname}/app-prd.yaml` to `clusters/prd/kustomization.yaml` and commit — Argo CD auto-deploys.
4. **Register in dev** (when needed): add `- ../../applications/{appname}/app-dev.yaml` to `clusters/dev/kustomization.yaml` and commit to `dev` branch.

Namespaces are created automatically via `syncOptions: [CreateNamespace=true]` on each Application CR — no separate namespace manifest needed.

## PostgreSQL — Shared Instance, Schema-per-Env

A single `postgres` instance serves all environments. **Do not create a `postgres-dev` deployment.**  
Dev and prod apps are separated by **PostgreSQL schemas**, not by separate instances.

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
- `infrastructure.yaml` → `infrastructure/` (Kustomize) — `ceph-csi-secret` scaffold, `platform-storage` PVC, `proxmox-ceph-rbd` StorageClass, ArgoCD ingress + insecure config
- `ingress-nginx.yaml` → upstream Helm chart — routes external traffic to app Ingress resources
- `cert-manager.yaml` → upstream Helm chart — TLS certificate management
- `metrics-server.yaml` → upstream Helm chart — enables `kubectl top` and HPA
- `metallb.yaml` → upstream Helm chart — L2 LoadBalancer, IP pool `192.168.1.220-240`, ingress-nginx gets `192.168.1.221`
- `monitoring.yaml` → `prometheus-community/kube-prometheus-stack` — Prometheus + Grafana + Alertmanager
- `ceph-csi-rbd.yaml` → `ceph.github.io/csi-charts/ceph-csi-rbd` — RBD block storage CSI driver (k3s kubelet path configured)
- `ceph-csi-cephfs.yaml` → `ceph.github.io/csi-charts/ceph-csi-cephfs` — CephFS shared storage CSI driver (k3s kubelet path configured)

Namespaces are **not** managed here — each Application CR uses `syncOptions: [CreateNamespace=true]` to create its own namespace on first deploy.

**To enable per-app storage** — set in `values-prd.yaml` or `values-dev.yaml`:
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
  host: myapp.home.k3s.com   # Traefik on pihole handles TLS → forwards HTTP to ingress-nginx
```

**To expose a TCP service** (e.g. a database) — add to `clusters/prd/ingress-nginx.yaml` under `tcp:`:
```yaml
tcp:
  5432: "postgres/postgres:5432"   # port: "namespace/service:port"
```

## Network Policies & Resource Quotas

All app charts include these templates (enabled by default via `values.yaml`):

- **`NetworkPolicy`** — default-deny with explicit allow rules:
  - Apps: ingress from `ingress-nginx` + `monitoring`, egress to `postgres` + DNS
  - Postgres: ingress from any namespace on port 5432
  - Extra namespaces: `networkPolicy.extraIngressNamespaces: [myns]`
- **`ResourceQuota`** — limits per namespace, configurable via `resourceQuota.hard` in values

To disable for an app: `networkPolicy.enabled: false` or `resourceQuota.enabled: false` in `values-prd.yaml`.

## Helm Template Helpers (`_helpers.tpl`)

All apps use four named templates defined in `templates/_helpers.tpl` (canonical source: `applications/common-utils/templates/_helpers.tpl`):

| Helper | Output |
|--------|--------|
| `app.name` | `.Release.Name` |
| `app.image` | `repository:tag` |
| `app.labels` | Full K8s label set (`app`, `app.kubernetes.io/*`, `helm.sh/chart`) including `version` from `Chart.AppVersion` |
| `app.selectorLabels` | `app: {name}` only — stable, never changes after first deploy |

## Operational Commands

```bash
# Bootstrap (prd first, then dev) — one-time only per cluster
kubectl apply -f clusters/prd/parent-app.yaml
kubectl apply -f clusters/dev/parent-app.yaml

# After bootstrap, adding/removing apps is automatic:
# - Add: commit new app-prd.yaml ref to clusters/prd/kustomization.yaml → Argo CD creates it
# - Remove: remove ref from kustomization.yaml → Argo CD prunes the Application + its resources

# Set Ceph credentials after prd bootstrap (not stored in git — run once)
kubectl delete secret ceph-csi-secret -n default
kubectl create secret generic ceph-csi-secret \
  --from-literal=userID=admin \
  --from-literal=userKey=$(ceph auth get-key client.admin) \
  --type=kubernetes.io/rbd \
  --namespace=default

# Set postgres credentials (not stored in git — run once)
kubectl create secret generic postgres-credentials \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=<password> \
  --from-literal=POSTGRES_DB=postgres \
  --namespace=postgres --dry-run=client -o yaml | kubectl apply -f -

# Check all Argo CD Applications
kubectl get applications -n argocd

# Debug a sync failure
kubectl describe application <name> -n argocd
kubectl logs -n argocd deploy/argocd-repo-server
```

## External Network Layer (outside k3s)

Traffic flow for `*.home.k3s.com`:

```
Browser
  → Traefik (on pihole, :443 HTTPS)
    → ingress-nginx (192.168.1.221:80, plain HTTP)
      → app Service → Pod
```

**PiHole** (`home-lab-pihole`, internal DNS server):
- DNS entries for all `*.home.k3s.com` subdomains point to Traefik's IP
- To add a new app: add a DNS record in PiHole pointing to Traefik

**Traefik** (`/etc/traefik/dynamic/k3s.yml` on pihole):
- Handles TLS termination for all `*.home.k3s.com` traffic
- Forwards plain HTTP to `http://192.168.1.221` (MetalLB ingress-nginx IP)
- `passHostHeader: true` — preserves the original Host header so ingress-nginx can route by hostname
- Config uses `HostRegexp` to match all subdomains:
  ```yaml
  rule: "HostRegexp(`^.+\\.home\\.k3s\\.com$`) || Host(`home.k3s.com`)"
  ```

**ingress-nginx** is configured with `ssl-redirect: false` and `use-forwarded-headers: true` since TLS is terminated upstream by Traefik.

**Adding a new subdomain:**
1. Add DNS entry in PiHole for `myapp.home.k3s.com` → Traefik IP
2. Set `ingress.host: myapp.home.k3s.com` in `values-prd.yaml`
3. Commit — Argo CD creates the Ingress, Traefik routes automatically (wildcard rule already covers it)

## Repo: `https://github.com/spider-su/ops-autopilot.git`
