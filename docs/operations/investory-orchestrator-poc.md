# Investory Orchestrator POC

The `clusters/dev` Argo CD Application deploys the scheduler and dashboard from
`applications/investory-orchestrator` into the `investory-orchestrator`
namespace. Its development values follow the mutable `latest` image published
by Docker Hub as `aserobaba/orchestrator` after the orchestrator repository's validation
workflow succeeds. Publishing an image does not update the Argo CD application
by itself. After each build, copy its `sha-<40-character commit>` tag into the
**Promote orchestrator development image** workflow in this repository. That
workflow opens a GitOps pull request; review and merge it to roll out the image.
Production deployment is intentionally not registered until a production image
digest and its promotion wiring are available.

## Runtime secrets

Before the Deployment can start, provide these Kubernetes Secrets in the
`investory-orchestrator` namespace. Keep all values outside this repository.

`orchestrator-runtime`:

- `database-url`: DSN to the existing PostgreSQL service and the role allowed
  to create/use the `investory_orchestrator` schema;
- `github-installation-id`;
- `github-app-private-key` (PEM contents);
- `dashboard-api-token`.

`mac-runner-ssh`:

- `id_ed25519`: private key authorized for the forced runner command on devMac;
- `known_hosts`: verified SSH host key for devMac.

The repository's preferred durable secret path is a SOPS-encrypted Secret
manifest under `secrets/workloads/`, rendered by a KSOPS Application targeting
this namespace. Do not add that manifest until the operator has the real secret
values and can encrypt them with the repository's age recipient. For a
short-lived supervised POC, the operator may provision the two Secrets directly
with `kubectl`; keep the commands and values out of shell history and do not
commit generated Secret YAML.

The database NetworkPolicy permits this namespace to reach PostgreSQL on TCP
5432. The workload NetworkPolicy allows DNS, PostgreSQL, and external egress
needed for GitHub API and SSH access to the configured Mac runner. The dashboard
is a ClusterIP service; use `kubectl port-forward` for local access.

## First deployment checks

1. Publish the image to Docker Hub. Keep it public for unauthenticated k3s
   pulls, or configure a pull secret using `image.pullSecrets` if it is private.
2. Provision both runtime Secrets and verify the Mac forced-command SSH login.
3. Merge the GitOps Application registration and wait for Argo sync and both
   Deployment rollouts.
4. Run the development image promotion workflow with the published SHA tag and
   merge the generated pull request; verify the scheduler and dashboard rollouts.
5. Port-forward the dashboard, configure the repository, then queue a test
   issue and verify the task reaches READY or BLOCKED with its GitHub mention.

See the application repository's
[`docs/k3s-poc.md`](https://github.com/spider-su/investory-orchestrator/blob/main/docs/k3s-poc.md)
for the end-to-end Mac runner setup and issue workflow.
