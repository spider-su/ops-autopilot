# Home Infra Agent deployment

This chart runs the `aserobaba/home-infra-agent` image as one replica in the development cluster. The dev Application is registered at `clusters/dev/workloads/home-infra-agent.yaml`; it reads this chart from `main` and uses mutable `latest` while iterating. Production is intentionally not registered: production workloads require a registry-resolved SHA-256 digest and reviewed promotion.

The chart mounts its configuration from a ConfigMap at `/etc/home-infra-agent`. It includes the Proxmox ping job for `192.168.1.51` through `.53`. NetworkPolicy permits DNS and egress to `192.168.1.0/24`, so the cluster must have a route to that subnet. Add any MQTT broker CIDR to `networkPolicy.externalEgressCidrs` if it is outside that subnet.

In development, the K3s job uses the projected token for the `home-infra-agent` ServiceAccount. Its ClusterRole can only `list` nodes, pods, deployments, StatefulSets, and DaemonSets across namespaces. It cannot read Secrets, ConfigMaps, logs, or Events. Egress to the Kubernetes API is limited to `networkPolicy.kubernetesApiCidr` on TCP 443. Disable `jobs.k3s.enabled` to remove the ClusterRole and ClusterRoleBinding and keep service-account token mounting off.

MQTT starts disabled until the broker is configured. Set `mqtt.enabled` and `mqtt.host` in values, and set `mqtt.passwordSecretName` to a namespaced Kubernetes Secret containing the `password` key when authentication is required. Secret creation remains outside Helm values and must follow the repository's SOPS/age process. Ingress is disabled by default; access the ClusterIP service through a trusted in-cluster path or `kubectl port-forward` until a private hostname and ingress policy are chosen.

The dev values expose the read-only UI at `https://ha-infra.home.k3s.com/dashboard`. The `/dashboard` path is rewritten to the app root; `/api` and `/health` are routed separately because the page calls those absolute paths. Pi-hole resolves the hostname to the Traefik host, which forwards HTTP to ingress-nginx at `192.168.1.221`. The external Traefik dynamic config is managed on `home-lab-pihole`, outside this GitOps repository.

The chart uses low resource requests/limits, a read-only root filesystem, non-root UID 10001, HTTP health probes, and a namespace ResourceQuota. Validate changes with `helm lint applications/home-infra-agent -f applications/home-infra-agent/values.yaml -f applications/home-infra-agent/values-dev.yaml`, then run the full repository validator.
