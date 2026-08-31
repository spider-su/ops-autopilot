# Validation

## Standard command

From the repository root on Windows:

```powershell
& .\scripts\validate.ps1
```

The same command runs in GitHub Actions for pushes to `main`/`dev` and for pull requests.

The helper is read-only and performs:

1. local Markdown-link validation;
2. Helm lint for each local chart and registered environment values, including each chart's
   `values.schema.json`;
3. Helm rendering for all local workload environments;
4. rendering of every pinned upstream chart referenced by production Argo Applications;
5. policy checks for destinations, namespaces, resources, probes, dangerous sync options, immutable
   production images, and secret payloads;
6. Kubernetes schema validation with `kubeconform`, including Argo CD and monitoring CRD schemas;
7. production, development, and infrastructure Kustomize rendering;
8. documentation and manifest consistency checks.

`Replace=true` is rejected by policy for normal Applications. The sole exception is the pinned
`argocd-infrastructure` Application, where it is required to manage Argo's oversized upstream CRDs
without exceeding Kubernetes' annotation limit.

## Individual checks

Documentation:

```powershell
python .\tools\check_markdown_links.py
```

Example chart check:

```powershell
helm lint applications/investory `
  -f applications/investory/values.yaml `
  -f applications/investory/values-prd.yaml
```

Cluster composition:

```powershell
kubectl kustomize clusters/prd | Out-Null
kubectl kustomize clusters/dev | Out-Null
```

Cluster kustomizations contain the environment-specific Argo Application wiring under `clusters/` and
refer only to files within their own overlay, so standard restricted rendering is sufficient.

## What these checks prove

- Markdown links resolve to repository files or valid document anchors are ignored as appropriate.
- Local Helm templates accept their configured values.
- Kustomize can compose all registered Application resources.

The validator also renders pinned upstream charts and calls `kubeconform` with the Kubernetes schema
catalog plus the Argo CD and Prometheus Operator CRD catalog. The CRD catalog is fetched at validation
time; network access is therefore required for a complete run.

They do not prove:

- Argo CD reconciliation;
- Pod health, target health, data durability, or user-visible behavior.

Use live verification only when cluster access is in scope and report it separately from local
validation.
