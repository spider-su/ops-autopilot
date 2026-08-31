# Bootstrap and recovery

## Prerequisites

- A working k3s cluster with Argo CD installed in `argocd`.
- `kubectl` access to the target cluster.
- Reachability from cluster nodes to the configured Ceph monitors.
- Operator access to the external Pi-hole and Traefik configuration.
- Ceph and PostgreSQL credentials available through the SOPS/age decryption boundary.

Confirm the active context before every bootstrap or recovery command:

```bash
kubectl config current-context
kubectl get nodes
```

## Bootstrap production

Apply the production parent once:

```bash
kubectl apply -f clusters/prd/parent-app.yaml
```

The parent reads remote `main`, creates the registered child Applications, and enables automated prune
and self-heal. Wait for the platform Applications before expecting dependent workloads to become
healthy.

## Required credentials

Secret values are managed with SOPS/age. Never paste real values into shell history, issue comments, or
documentation. See [`secrets/README.md`](../../secrets/README.md) for the encryption boundary.

Required Secret objects currently include:

- `default/ceph-csi-secret`
- `postgres/postgres-credentials`
- `investory-prod/investory-secrets`
- `monitoring/alertmanager-smtp` (`smtp-password`)

The existing chart Secret scaffolds remain as compatibility artifacts until encrypted replacements are
connected to the Argo CD decryption boundary. Do not put their payloads in Git.

## Credential rotation and recovery

Rotate each external credential at its provider first, then update the corresponding encrypted SOPS
manifest and reconcile the owning Application. Rotate Ceph credentials before revoking the old key so
existing PVC mounts remain recoverable; rotate PostgreSQL credentials by updating the database and its
Secret in a coordinated maintenance window; rotate application API keys and the Alertmanager SMTP app
password independently. Keep the age private key and recovery instructions in the operator's secured
key store. A lost age private key cannot be recovered from this repository.

## Bootstrap development

Production must be bootstrapped first because development consumes shared platform and database
services:

```bash
kubectl apply -f clusters/dev/parent-app.yaml
```

## External network prerequisites

For each public homelab hostname:

1. Pi-hole must resolve the hostname to the Traefik host.
2. Traefik must match `*.home.k3s.com` and forward HTTP to the ingress-nginx LoadBalancer address.
3. The workload must enable an Ingress with the same hostname.

These first two steps are outside GitOps scope and must be verified separately.

For private-LAN PostgreSQL testing, use the ingress-nginx LoadBalancer LAN address on TCP port `5432`.
This path is intentionally available to operator PCs for testing and must not be published beyond the
homelab LAN; production credentials and untrusted networks require a separate secure-access design.

## Verify convergence

```bash
kubectl get applications -n argocd
kubectl get pods -A
kubectl get pvc -A
kubectl get ingress -A
```

For a failing child Application:

```bash
kubectl describe application <name> -n argocd
kubectl logs -n argocd deploy/argocd-repo-server
```

Do not treat `Synced` alone as proof of a functioning workload. Check Pods, endpoints, events, and the
actual user-facing route as appropriate.

## Recovery boundary

- Reapply a parent only when the parent Application is absent or its declarative spec must be restored.
- Do not routinely use destructive replace operations to clear sync errors.
- Do not delete an Application until its resource-deletion behavior and stateful data impact are
  understood.
- Restore PostgreSQL from a tested backup procedure, not from assumptions about PVC durability.
- PostgreSQL production creates one monthly custom-format dump on a separate Ceph RBD claim. The backup
  job retains only the newest dump; verify restoration manually before relying on it.
- The PostgreSQL image requires `CHOWN`, `DAC_OVERRIDE`, and `FOWNER` during entrypoint initialization
  of its mounted data directory. This is an intentional, narrowly scoped exception to the workload
  capability baseline.
