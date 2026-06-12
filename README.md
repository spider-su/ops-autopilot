# GitOps Argo CD Platform

Argo CD GitOps repo for a homelab Kubernetes cluster (k3s, 3 nodes, Proxmox/Ceph). All changes are declarative YAML committed to Git — no manual `kubectl` deployments after bootstrap.

---

## Architecture

```
clusters/prd/parent-app.yaml      ← bootstrap (kubectl apply once)
  └── clusters-prd Application    ← watches clusters/prd/kustomization.yaml
        ├── Platform Applications  ← metallb, ingress-nginx, cert-manager, ...
        └── App Applications       ← investory-prod, smartapp-prod, postgres, ...
```

- `clusters/` — env-specific wiring (branch, namespace, value files, parent apps)
- `applications/` — Helm charts + Application CRs, one folder per app
- `infrastructure/` — cluster-wide Kustomize resources (StorageClass, secret scaffold, ArgoCD ingress)

---

## Repository Structure

```
.
├── applications/
│   ├── common-utils/              # Helm library — shared _helpers.tpl
│   ├── investory/
│   │   ├── Chart.yaml
│   │   ├── app-dev.yaml           # Argo CD Application CR — dev
│   │   ├── app-prd.yaml           # Argo CD Application CR — prod
│   │   ├── values.yaml            # base defaults
│   │   ├── values-dev.yaml        # dev overrides
│   │   ├── values-prd.yaml        # prod overrides (replicas, ingress host)
│   │   └── templates/
│   │       ├── _helpers.tpl
│   │       ├── deployment.yaml
│   │       ├── service.yaml
│   │       ├── ingress.yaml       # optional — enabled via values
│   │       ├── pvc.yaml           # optional — enabled via values
│   │       ├── networkpolicy.yaml # default-deny with allow rules
│   │       └── resourcequota.yaml # namespace CPU/memory/pod limits
│   ├── smartapp/                  # identical structure to investory
│   └── postgres/                  # shared DB — no env suffix, schema-per-env
│
├── clusters/
│   ├── dev/
│   │   ├── parent-app.yaml        # bootstrap entry point for dev
│   │   └── kustomization.yaml     # lists app-dev.yaml for active dev apps only
│   └── prd/
│       ├── parent-app.yaml        # bootstrap entry point for prd
│       ├── kustomization.yaml     # lists all platform + app Application CRs
│       ├── base-app-project.yaml  # shared AppProject for all apps
│       ├── infrastructure.yaml    # Application → infrastructure/ (Kustomize)
│       ├── ingress-nginx.yaml     # Application → upstream Helm chart
│       ├── cert-manager.yaml
│       ├── metallb.yaml
│       ├── metrics-server.yaml
│       ├── monitoring.yaml        # kube-prometheus-stack
│       ├── ceph-csi-rbd.yaml
│       └── ceph-csi-cephfs.yaml
│
└── infrastructure/                # Kustomize — cluster-wide resources
    ├── kustomization.yaml
    ├── storageclass.yaml          # proxmox-ceph-rbd (default StorageClass)
    ├── secret.yaml                # ceph-csi-secret scaffold (credentials applied manually)
    ├── pvc.yaml                   # platform-storage PVC
    ├── argocd-config.yaml         # argocd-server insecure mode
    └── argocd-ingress.yaml        # Ingress for argocd.home.k3s.com
```

---

## Namespace Convention

| Type | Pattern | Example |
|------|---------|---------|
| Production apps | `{app}-prod` | `investory-prod` |
| Dev apps | `{app}-dev` | `investory-dev` |
| Shared services | `{app}` | `postgres` |
| Platform tools | own namespace | `monitoring`, `ingress-nginx`, ... |

---

## Bootstrap (one-time per cluster)

**prd must be bootstrapped first** — it owns infrastructure that dev depends on.

```bash
# 1. Bootstrap prd
kubectl apply -f clusters/prd/parent-app.yaml

# 2. Set Ceph credentials (not in git — run once)
kubectl create secret generic ceph-csi-secret \
  --from-literal=userID=admin \
  --from-literal=userKey=$(ceph auth get-key client.admin) \
  --type=kubernetes.io/rbd \
  --namespace=default --dry-run=client -o yaml | kubectl apply -f -

# 3. Set postgres credentials (not in git — run once)
kubectl create secret generic postgres-credentials \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=<password> \
  --from-literal=POSTGRES_DB=postgres \
  --namespace=postgres --dry-run=client -o yaml | kubectl apply -f -

# 4. Bootstrap dev (optional)
kubectl apply -f clusters/dev/parent-app.yaml
```

After bootstrap, **everything is automatic** — commit to git, Argo CD deploys.

---

## Adding a New Application

**1.** Copy an existing chart:
```bash
cp -r applications/investory applications/myapp
```

**2.** Update `Chart.yaml` name, edit `values.yaml`, `values-prd.yaml`, `values-dev.yaml`.

**3.** Update `app-prd.yaml`:
```yaml
metadata:
  name: myapp-prod
spec:
  source:
    path: applications/myapp
    helm:
      releaseName: myapp
      valueFiles: [values.yaml, values-prd.yaml]
  destination:
    namespace: myapp-prod
```

**4.** Add to `clusters/prd/kustomization.yaml`:
```yaml
- ../../applications/myapp/app-prd.yaml
```

**5.** Commit and push to `main` — Argo CD deploys automatically. ✅

For dev: create `app-dev.yaml` (`targetRevision: dev`, `namespace: myapp-dev`) and add to `clusters/dev/kustomization.yaml`.

---

## Platform Services

| Application | Purpose | URL / Access |
|-------------|---------|--------------|
| `metallb` | L2 LoadBalancer (192.168.1.220-240) | — |
| `ingress-nginx` | HTTP/TCP ingress | `192.168.1.221` |
| `cert-manager` | TLS certificate management | — |
| `metrics-server` | `kubectl top` + HPA | — |
| `ceph-csi-rbd` | RBD block storage CSI | — |
| `ceph-csi-cephfs` | CephFS shared storage CSI | — |
| `monitoring` | Prometheus + Grafana + Alertmanager | `https://grafana.home.k3s.com` |
| `postgres` | Shared PostgreSQL (schema-per-env) | `192.168.1.221:5432` |
| `argocd` | GitOps controller | `https://argocd.home.k3s.com` |

---

## Storage

Enable per-app Ceph RBD storage in `values-prd.yaml`:
```yaml
pvc:
  enabled: true
  size: 5Gi
  mountPath: /data
```

---

## Ingress & External Access

**Traffic flow:**
```
Browser → Traefik (pihole, HTTPS) → ingress-nginx (192.168.1.221, HTTP) → app Pod
```

**PiHole** is the internal DNS server — all `*.home.k3s.com` entries point to Traefik's IP.

**Traefik** (running on the pihole server) handles TLS and forwards plain HTTP to ingress-nginx at `192.168.1.221`. Config lives in `/etc/traefik/dynamic/k3s.yml` on the pihole host — uses a wildcard `HostRegexp` rule so new subdomains work automatically without Traefik changes.

**To add a new app subdomain:**
1. Add DNS record in PiHole: `myapp.home.k3s.com` → Traefik IP
2. Set in `values-prd.yaml`: `ingress.host: myapp.home.k3s.com`
3. Commit to `main` — done ✅

Enable HTTP ingress in `values-prd.yaml`:
```yaml
ingress:
  enabled: true
  host: myapp.home.k3s.com
```


To expose a TCP service, add to `clusters/prd/ingress-nginx.yaml`:
```yaml
tcp:
  5432: "postgres/postgres:5432"
```

---

## Network Policies & Resource Quotas

All app charts include `NetworkPolicy` and `ResourceQuota` templates (enabled by default).

- **Apps** allow ingress from `ingress-nginx` and `monitoring` only
- **Postgres** allows ingress on port 5432 from any namespace
- Quotas are set in `values.yaml` and can be overridden per env

---

## Useful Commands

```bash
# Check all Applications
kubectl get applications -n argocd

# Debug sync failure
kubectl describe application <name> -n argocd
kubectl logs -n argocd deploy/argocd-repo-server

# Check resources per namespace
kubectl get pods,svc,ingress,pvc -n investory-prod
kubectl top nodes
```
