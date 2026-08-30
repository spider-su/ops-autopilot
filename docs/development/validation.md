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
3. production policy checks for schema presence and immutable image digests;
4. production and development Kustomize rendering.

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
kubectl kustomize clusters/prd --load-restrictor LoadRestrictionsNone | Out-Null
kubectl kustomize clusters/dev --load-restrictor LoadRestrictionsNone | Out-Null
```

The unrestricted load option remains temporarily required because cluster kustomizations still reference
Application resources under `applications/`. Argo CD is configured with the same temporary option;
reorganizing those environment overlays is tracked in the roadmap.

## What these checks prove

- Markdown links resolve to repository files or valid document anchors are ignored as appropriate.
- Local Helm templates accept their configured values.
- Kustomize can compose all registered Application resources.

They do not prove:

- upstream chart rendering unless the upstream chart is rendered separately;
- Kubernetes API schema compatibility;
- Argo CD reconciliation;
- Pod health, target health, data durability, or user-visible behavior.

Use live verification only when cluster access is in scope and report it separately from local
validation.
