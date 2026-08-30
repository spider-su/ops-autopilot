# Encrypted secrets

Secrets use [SOPS](https://github.com/getsops/sops) with age encryption. Secret manifests belong in
this directory as `*.sops.yaml`; only their `data` or `stringData` fields are encrypted.

The repository intentionally does not contain an age recipient or encrypted payload yet. Configure
the operator's public recipient outside Git, then create or edit a secret with:

```powershell
$env:SOPS_AGE_RECIPIENT = 'age1...'
sops --age $env:SOPS_AGE_RECIPIENT secrets/postgres-credentials.sops.yaml
```

The corresponding private age key must remain in the Argo CD decryption boundary, not in this
repository. Until the Argo CD SOPS integration is installed and the encrypted workload secrets are
committed, the existing operator-managed Secret bootstrap remains required.

Never commit plaintext `data`, `stringData`, private keys, `.env` files, or age identity files.
