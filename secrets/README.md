# Encrypted secrets

Secrets use [SOPS](https://github.com/getsops/sops) with age encryption. Secret manifests belong in
this directory as `*.sops.yaml`; only their `data` or `stringData` fields are encrypted. Argo CD
renders the `platform` and `workloads` bundles through KSOPS.

The repository contains only encrypted payloads and the public age recipient is recorded in the
repository's `.sops.yaml`. Create or edit a secret with:

```powershell
$env:SOPS_AGE_RECIPIENT = 'age1...'
sops --age $env:SOPS_AGE_RECIPIENT secrets/postgres-credentials.sops.yaml
```

The corresponding private age key is stored in the `argocd/sops-age` Secret and mounted only into
the Argo CD repo-server decryption tooling. The repo-server deployment is patched with
[`infrastructure/argocd/argocd-repo-server-ksops-patch.yaml`](../infrastructure/argocd/argocd-repo-server-ksops-patch.yaml)
because the current Argo CD installation is external to this repository; apply that patch during
Argo bootstrap or after an Argo CD upgrade. Back the key up in an offline/password-manager
location; the cluster copy alone is not sufficient after cluster loss.

Never commit plaintext `data`, `stringData`, private keys, `.env` files, or age identity files.
