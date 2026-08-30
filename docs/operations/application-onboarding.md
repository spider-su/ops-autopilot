# Application onboarding

## Supported shape

A normal workload has:

```text
applications/<app>/
  Chart.yaml
  values.yaml
  values-prd.yaml
  values-dev.yaml
  values.schema.json
  app-prd.yaml
  app-dev.yaml                 # optional until development deployment is needed
  templates/
```

Use the closest existing workload as a starting point. `investory` demonstrates configuration and
secret injection; `smartapp` demonstrates a simpler stateless web workload; `postgres` is stateful and
must not be used as the default application template.

## Create the chart

1. Copy the closest chart to `applications/<app>/`.
2. Replace the chart name, description, image, ports, resources, and ingress host.
   Keep the chart's `kubeVersion` constraint aligned with the cluster API versions it uses.
3. Delete capabilities the workload does not need.
4. Add workload-specific readiness, startup, and liveness probes when the application exposes suitable
   endpoints or commands.
5. Keep sensitive values out of all values files.

Base values describe reusable defaults. Environment files contain only intentional overrides. The chart
schema is evaluated against the merged values during `helm lint`; update it when adding a new supported
value or template capability.

## Create the Application resources

Production convention:

```yaml
metadata:
  name: <app>-prod
spec:
  project: base-app
  source:
    repoURL: https://github.com/spider-su/ops-autopilot.git
    targetRevision: main
    path: applications/<app>
    helm:
      releaseName: <app>
      valueFiles:
        - values.yaml
        - values-prd.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: <app>-prod
```

Development uses `targetRevision: dev`, `values-dev.yaml`, and namespace `<app>-dev` under the current
environment model.

## Register the workload

Add the production Application path to `clusters/prd/kustomization.yaml`. Add development to
`clusters/dev/kustomization.yaml` only while it is actively needed.

Registration is the deployment trigger after commit and push. Merely creating an Application file
does not make the parent discover it.

## External access

When ingress is enabled:

- choose a unique `*.home.k3s.com` hostname;
- add the matching Pi-hole DNS entry;
- confirm the external Traefik wildcard route preserves the Host header;
- avoid Kubernetes TLS configuration when TLS remains terminated by external Traefik.

TCP exposure is exceptional. Add it to ingress-nginx only after reviewing authentication, encryption,
and network reachability.

## Acceptance checklist

- [ ] Production uses a pinned image tag or digest and an intentional pull policy.
- [ ] Requests, limits, and namespace quotas are mutually compatible.
- [ ] Service selectors match Pod labels and Service ports match container ports.
- [ ] Health probes represent application readiness rather than only process existence (the workload
      chart defaults are configurable).
- [ ] Secret names and required keys are documented without secret values.
- [ ] NetworkPolicy allows only required ingress and egress.
- [ ] `networkPolicy.externalEgressCidrs` is narrowed from the compatibility default when external APIs
      are known.
- [ ] Stateful data has a storage, backup, and restore decision.
- [ ] Stateless/platform Application resources use the cascade finalizer; stateful Applications have an
      explicit deletion-protection decision.
- [ ] Helm lint and template rendering pass for each registered environment.
- [ ] Cluster Kustomize rendering passes.
- [ ] Markdown links pass.
- [ ] After push, Argo sync, workload health, endpoints, and the user-facing route are verified.

Run the standard validation described in [`../development/validation.md`](../development/validation.md).
