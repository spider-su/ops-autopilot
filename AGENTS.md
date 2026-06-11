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
| `clusters/prd` | `main` | `{app}-prd` |

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

Namespaces are created automatically via `syncOptions: [CreateNamespace=true]` on each Application CR â€” no separate namespace manifest needed.

## Infra Layer â€” Connecting Apps to Storage, Ingress, Secrets

Platform Applications in `clusters/prd/` (each is a separate Argo CD Application):
- `infrastructure.yaml` â†’ `infrastructure/` (Kustomize) â€” `ceph-csi-secret` scaffold + `platform-storage` PVC
- `ingress-nginx.yaml` â†’ upstream Helm chart â€” routes external traffic to app Ingress resources
- `cert-manager.yaml` â†’ upstream Helm chart â€” TLS certificate management
- `metrics-server.yaml` â†’ upstream Helm chart â€” enables `kubectl top` and HPA

Namespaces are **not** managed here â€” each Application CR uses `syncOptions: [CreateNamespace=true]` to create its own namespace on first deploy.

**To enable per-app storage** â€” set in `values-prd.yaml` or `values-dev.yaml`:
```yaml
pvc:
  enabled: true
  size: 5Gi          # uses proxmox-ceph-rbd StorageClass automatically
  mountPath: /data
```

**To enable ingress** â€” set in `values-prd.yaml`:
```yaml
ingress:
  enabled: true
  host: myapp.example.com   # requires ingress-nginx in infra layer
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
# Bootstrap (prd first, then dev)
kubectl apply -f clusters/prd/kustomization.yaml
kubectl apply -f clusters/dev/kustomization.yaml

# Set Ceph credentials after prd bootstrap (not stored in git â€” run once)
kubectl create secret generic ceph-csi-secret \
  --from-literal=userID=admin \
  --from-literal=userKey=$(ceph auth get-key client.admin) \
  --namespace=default --dry-run=client -o yaml | kubectl apply -f -

# Check all Argo CD Applications
kubectl get applications -n argocd

# Debug a sync failure
kubectl describe application <name> -n argocd
kubectl logs -n argocd deploy/argocd-repo-server
```

## Repo: `https://github.com/spider-su/ops-autopilot.git`
