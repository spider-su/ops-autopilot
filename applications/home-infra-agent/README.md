# Home Infra Agent deployment

This chart runs the `aserobaba/home-infra-agent` image as one replica in the development cluster. The dev Application is registered at `clusters/dev/workloads/home-infra-agent.yaml` and reads this chart from `main`. The base chart defaults to `latest`; the dev overlay pins an immutable `sha-<commit>` tag with `imagePullPolicy: Always`. Promote a release by updating the dev pin in `values-dev.yaml`. Production is intentionally not registered: production workloads require a registry-resolved SHA-256 digest and reviewed promotion.

The chart mounts its configuration from a ConfigMap at `/etc/home-infra-agent`. It includes the Proxmox ping job for `192.168.1.51` through `.53`. NetworkPolicy permits DNS and egress to `192.168.1.0/24`, so the cluster must have a route to that subnet. Add any MQTT broker CIDR to `networkPolicy.externalEgressCidrs` if it is outside that subnet.

The Proxmox and K3s jobs run every 60 seconds and become stale after 180 seconds (three missed intervals). Solarman runs every 3,600 seconds and becomes stale after 7,200 seconds (two intervals). Solarman's source-data age limit is configured separately in its source settings.

The dev overlay also enables the Investory portfolio snapshot job. It reads the encrypted
`home-infra-agent-investory-db` Secret (`url` key) through a fixed, read-only database function and
publishes the latest portfolio 1 equity/profit snapshot hourly on weekdays from 09:00 through 22:00
Warsaw time. `networkPolicy.investoryEgressCidrs` contains the current resolved Neon endpoint IPs and
permits TCP 5432 only; update those `/32` entries if the Neon DNS answers change. The SOPS secret is
deployed by `secrets-home-infra-agent-dev` before the workload Application.

The dev overlay enables the hourly Solarman current-data job and permits HTTPS egress to the
currently resolved `globalapi.solarmanpv.com` addresses. Update `networkPolicy.solarmanEgressCidrs`
if DNS changes those addresses. The chart expects an externally managed Secret named
`home-infra-agent-solarman` with `app-id`, `app-secret`, `email`, and `password` keys; the optional
`device-serial` key selects the intended inverter when discovery is ambiguous. No Solarman
credentials are stored in Helm values or this repository. Until the Secret is provisioned, the pod
starts normally, makes no Solarman API requests, and the job reports an error status.

In development, the K3s job uses the projected token for the `home-infra-agent` ServiceAccount. Its ClusterRole can only `list` nodes, pods, deployments, StatefulSets, and DaemonSets across namespaces. It cannot read Secrets, ConfigMaps, logs, or Events. The ClusterRole and binding are owned by a separate `platform-app` Argo Application so the workload's `base-app` project does not gain cluster-scoped RBAC permissions. Egress to the Kubernetes API is limited to `networkPolicy.kubernetesApiCidr` on TCP 443. Disable `jobs.k3s.enabled` to keep service-account token mounting off; remove the separate RBAC Application if cluster access is no longer required.

MQTT starts disabled until the broker is configured. Set `mqtt.enabled` and `mqtt.host` in values, and set `mqtt.passwordSecretName` to a namespaced Kubernetes Secret containing the `password` key when authentication is required. Secret creation remains outside Helm values and must follow the repository's SOPS/age process. Ingress is disabled by default; access the ClusterIP service through a trusted in-cluster path or `kubectl port-forward` until a private hostname and ingress policy are chosen.

The dev values expose the read-only UI at `https://ha-infra.home.k3s.com/dashboard`. The `/dashboard` path is rewritten to the app root; `/api` and `/health` are routed separately because the page calls those absolute paths. Pi-hole resolves the hostname to the Traefik host, which forwards HTTP to ingress-nginx at `192.168.1.221`. The external Traefik dynamic config is managed on `home-lab-pihole`, outside this GitOps repository.

The chart uses low resource requests/limits, a read-only root filesystem, non-root UID 10001, HTTP health probes, and a namespace ResourceQuota. Validate changes with `helm lint applications/home-infra-agent -f applications/home-infra-agent/values.yaml -f applications/home-infra-agent/values-dev.yaml`, then run the full repository validator.
