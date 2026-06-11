# ðŸ“˜ GitOps Argo CD Platform

Argo CD GitOps repo for Kubernetes. All changes are declarative YAML committed to Git â€” no manual `kubectl` deployments.

---

# ðŸ§  Architecture Overview

```
clusters/{env}/kustomization.yaml        â† bootstrap (kubectl apply once)
  â”œâ”€â”€ clusters/prd/base-app-project.yaml             â† AppProject (prd only)
  â”œâ”€â”€ clusters/prd/infrastructure.yaml            â† Application â†’ infrastructure/ (prd only)
  â””â”€â”€ applications/{app}/app-{env}.yaml  â† Application â†’ applications/{app}/ (Helm)
```

- `clusters/` â€” all env-specific wiring (branch, namespace, value files)
- `applications/` â€” Helm charts + Application CRs, one folder per app
- `infrastructure/` â€” cluster-wide platform resources (Ceph secret, shared PVC)

---

# ðŸ§± Repository Structure

```
.
â”œâ”€â”€ applications/
â”‚   â”œâ”€â”€ common-utils/              # Helm library chart â€” shared helpers (_helpers.tpl)
â”‚   â”œâ”€â”€ investory/
â”‚   â”‚   â”œâ”€â”€ Chart.yaml
â”‚   â”‚   â”œâ”€â”€ app-dev.yaml           # Argo CD Application CR â€” dev env
â”‚   â”‚   â”œâ”€â”€ app-prd.yaml           # Argo CD Application CR â€” prd env
â”‚   â”‚   â”œâ”€â”€ values.yaml            # base defaults
â”‚   â”‚   â”œâ”€â”€ values-dev.yaml        # dev overrides
â”‚   â”‚   â”œâ”€â”€ values-prd.yaml        # prd overrides (replicas, ingress host)
â”‚   â”‚   â””â”€â”€ templates/
â”‚   â”‚       â”œâ”€â”€ _helpers.tpl
â”‚   â”‚       â”œâ”€â”€ deployment.yaml
â”‚   â”‚       â”œâ”€â”€ service.yaml
â”‚   â”‚       â”œâ”€â”€ pvc.yaml           # optional â€” enabled via values
â”‚   â”‚       â””â”€â”€ ingress.yaml       # optional â€” enabled via values
â”‚   â””â”€â”€ smartapp/                  # identical structure to investory
â”‚
â”œâ”€â”€ clusters/
â”‚   â”œâ”€â”€ dev/
â”‚   â”‚   â””â”€â”€ kustomization.yaml     # references app-dev.yaml from active dev apps
â”‚   â””â”€â”€ prd/
â”‚       â”œâ”€â”€ kustomization.yaml     # references apps.yaml + infra.yaml + app-prd.yaml from all apps
â”‚       â”œâ”€â”€ apps.yaml              # shared Argo CD AppProject for all apps
â”‚       â””â”€â”€ infra.yaml             # Application CR â†’ infrastructure/
â”‚
â””â”€â”€ infrastructure/
â”‚   â”œâ”€â”€ kustomization.yaml
â”‚   â”œâ”€â”€ secret.yaml                # ceph-csi-secret in default ns (Ceph RBD provisioner)
â”‚   â””â”€â”€ pvc.yaml                   # platform-storage PVC in infrastructure ns
```

---

# ðŸš€ How It Works

## 1. Bootstrap (one-time only)

```bash
kubectl apply -f clusters/prd/kustomization.yaml   # deploys infra + all apps
kubectl apply -f clusters/dev/kustomization.yaml   # deploys active dev app only
```

`prd` must be bootstrapped first â€” it owns the infrastructure (Ceph secret, PVC) that `dev` depends on.

**After bootstrapping prd**, set the Ceph credentials (not stored in git):
```bash
kubectl create secret generic ceph-csi-secret \
  --from-literal=userID=admin \
  --from-literal=userKey=$(ceph auth get-key client.admin) \
  --namespace=default --dry-run=client -o yaml | kubectl apply -f -
```

## 2. Cluster layer

The cluster kustomization files are thin â€” they just reference Application CRs that live inside each app's own folder:

- `clusters/prd/kustomization.yaml` references `infrastructure.yaml` + each app's `app-prd.yaml`
- `clusters/dev/kustomization.yaml` references only the active dev app's `app-dev.yaml`

All app-specific config (Helm chart, values, Application CRs) lives together in `applications/{app}/`.

## 3. Helm chart layer

Argo CD auto-detects Helm when `Chart.yaml` is present. Each app chart selects env-specific values:

```yaml
source:
  path: applications/investory
  helm:
    releaseName: investory
    valueFiles:
      - values.yaml
      - values-prd.yaml     # or values-dev.yaml
```

`values.yaml` holds safe defaults. `values-prd.yaml` overrides replicas and enables ingress. `values-dev.yaml` overrides the image tag to `latest`.

## 4. Infrastructure layer

Managed by `clusters/prd/` â€” each component is a separate Argo CD Application:

| Application | Source | Namespace |
|-------------|--------|-----------|
| `infra` | `infrastructure/` (this repo, Kustomize) | `infrastructure` |
| `metallb` | `metallb.github.io/metallb` chart | `metallb-system` |
| `ingress-nginx` | `kubernetes.github.io/ingress-nginx` chart | `ingress-nginx` |
| `cert-manager` | `charts.jetstack.io` chart | `cert-manager` |
| `metrics-server` | `kubernetes-sigs.github.io/metrics-server` chart | `kube-system` |

Namespaces are created automatically via `CreateNamespace=true`. The `ceph-csi-secret` is scaffolded by `infra` but credentials must be applied manually (see Bootstrap section).

---

# ðŸ“¦ Application Flow

```
git push
   â†“
Argo CD detects change
   â†“
{app} Application syncs
   â†“
Helm renders templates with env values
   â†“
Deployment + Service (+ PVC / Ingress if enabled) applied to {app}-{env} namespace
```

---

# ðŸ§ª How to Use

## ðŸ”¹ Add a new application

**1.** Copy an existing chart as a starting point:
```bash
cp -r applications/investory applications/myapp
```

**2.** Update `applications/myapp/Chart.yaml` â€” set `name: myapp`.

**3.** Edit `values.yaml`, `values-prd.yaml`, `values-dev.yaml` for the new app.

**4.** Create `applications/myapp/app-prd.yaml`:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prd
  namespace: argocd
spec:
  project: apps
  source:
    repoURL: https://github.com/spider-su/ops-autopilot.git
    targetRevision: main
    path: applications/myapp
    helm:
      releaseName: myapp
      valueFiles:
        - values.yaml
        - values-prd.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp-prd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

**5.** Add `- ../../applications/myapp/app-prd.yaml` to `clusters/prd/kustomization.yaml`.

**6.** Commit and push to `main` â€” Argo CD deploys automatically and creates the `myapp-prd` namespace on its own.

For dev work: create `applications/myapp/app-dev.yaml` (same pattern, `targetRevision: dev`, `values-dev.yaml`, `namespace: myapp-dev`) and add `- ../../applications/myapp/app-dev.yaml` to `clusters/dev/kustomization.yaml`.

---

## ðŸ”¹ Enable storage for an app

In `values-prd.yaml` or `values-dev.yaml`:
```yaml
pvc:
  enabled: true
  size: 5Gi
  mountPath: /data
```

Uses `proxmox-ceph-rbd` StorageClass automatically. The PVC and volume mount are added by the Helm templates.

## ðŸ”¹ Enable ingress for an app

```yaml
ingress:
  enabled: true
  host: myapp.example.com
```

Requires `ingress-nginx` to be present in the cluster.

## ðŸ”¹ Switch which app dev is working on

Edit `clusters/dev/kustomization.yaml` â€” swap the listed app file. All other apps remain untouched in prd.

## ðŸ”¹ Check system status

```bash
kubectl get applications -n argocd
kubectl get pods -A
kubectl get svc -A
```

## ðŸ”¹ Debug sync issues

```bash
kubectl describe application <name> -n argocd
kubectl logs -n argocd deploy/argocd-repo-server
```

---

# ðŸŒ Environments

| Cluster | Branch | Namespace pattern | Manages |
|---------|--------|-------------------|---------|
| `clusters/prd` | `main` | `{app}-prd` | Infrastructure + all apps |
| `clusters/dev` | `dev` | `{app}-dev` | Active dev app only |

---

# ðŸ§© Design Principles

- Git is the single source of truth
- No manual `kubectl` deployments after bootstrap
- Env separation lives entirely in `clusters/` â€” `applications/` has no env awareness
- One shared AppProject `base-app` (`clusters/prd/base-app-project.yaml`) â€” no per-app RBAC overhead
- Infrastructure owned by prd, consumed by dev
