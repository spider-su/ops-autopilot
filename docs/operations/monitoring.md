# Monitoring

## Components and ownership

`clusters/prd/monitoring.yaml` deploys `kube-prometheus-stack` into `monitoring`, including:

- Prometheus Operator and Prometheus
- Grafana
- Alertmanager
- kube-state-metrics
- node-exporter
- chart-provided ServiceMonitors, dashboards, and rules

`infrastructure/home-lab-alerts.yaml` adds homelab-specific node and workload rules. Kubernetes
`metrics-server` is separate: the live k3s installation currently owns it as a packaged add-on, while
the repository also contains an unregistered Argo Application manifest.

## Current collection profile

The repository intentionally favors low resource use over rapid detection:

- short Prometheus retention;
- a low-frequency global scrape interval;
- a lower-frequency evaluation interval;
- explicit CPU and memory budgets;
- extended Grafana liveness startup allowance.

Some chart endpoints can define their own interval and override the Prometheus global default. Always
inspect effective ServiceMonitors and active Prometheus targets before describing the complete stack as
low frequency.

## Current limitations

- Prometheus and Alertmanager use ephemeral storage.
- Alertmanager currently has no external notification receiver.
- Several upstream rules assume components or scrape windows that do not match k3s and the configured
  collection interval.
- Monitoring an application requires both metric exposure and a matching ServiceMonitor or PodMonitor;
  allowing the `monitoring` namespace through a NetworkPolicy is not sufficient.
- Current production target health must be checked live; Argo `Healthy` does not mean every Prometheus
  target is up.

The remediation work is tracked in [`../../ROADMAP.md`](../../ROADMAP.md), not redefined here.

## Live verification

```bash
kubectl get application monitoring -n argocd
kubectl get pods -n monitoring
kubectl get prometheus,alertmanager -n monitoring
kubectl get servicemonitor,podmonitor,prometheusrule -A
```

Use the Prometheus targets and rules APIs or Grafana UI to verify:

- active targets and their effective scrape intervals;
- target errors and timeouts;
- rule evaluation health;
- firing and pending alerts;
- Alertmanager receiver routing.

Inspect node-exporter reachability from Prometheus when only some nodes are down; a Running DaemonSet
Pod does not prove that port `9100` is reachable across nodes.

## Change policy

- Keep the upstream chart version pinned.
- Render the exact chart version and values before changing field names.
- Reconcile scrape intervals with every rate/range window used by enabled rules.
- Decide persistence and notification semantics explicitly rather than relying on chart defaults.
- Validate resource tuning after startup and outside active Argo retry or sync storms.
