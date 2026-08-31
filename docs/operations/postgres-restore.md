# PostgreSQL backup restore verification

The production backup is a monthly custom-format dump on the `postgres-backups` Ceph RBD claim.
The CronJob keeps only the newest dump.

The CronJob and backup Pod use stable `app: postgres` identity labels for discovery and operations.
Kubernetes labels are mutable metadata; preventing an operator or another controller from changing them
requires a separate admission policy and is not provided by the CronJob manifest itself.

## Create a backup for a test

Trigger the CronJob template manually and wait for completion:

```powershell
kubectl -n postgres create job postgres-backup-restore-test --from=cronjob/postgres-backup
kubectl -n postgres wait --for=condition=complete job/postgres-backup-restore-test --timeout=10m
kubectl -n postgres logs job/postgres-backup-restore-test
```

## Restore procedure

Create a disposable PostgreSQL Pod in the `postgres` namespace with:

- a new Ceph RBD PVC mounted as `PGDATA`;
- the `postgres-backups` PVC mounted read-only at `/backups`;
- the existing `postgres-credentials` Secret supplied through `envFrom`.

PVCs are namespace-scoped, so the disposable Pod must be in `postgres` to mount the retained backup
claim. After the Pod is ready, restore the dump without placing credentials in the command line:

```bash
kubectl -n postgres exec postgres-restore-test -- sh -c \
  'pg_restore --exit-on-error --clean --if-exists --no-owner \
  --dbname="$POSTGRES_DB" -h 127.0.0.1 -U "$POSTGRES_USER" \
  /backups/postgres-YYYY-MM-DD.dump'
```

If the target is an empty database, create schemas listed by the archive before restoring objects that
reference them. Verify the expected application schema and relation counts, then delete the disposable
Pod and PVC. Never delete `data-postgres-0` or `postgres-backups` as part of this test.

## Verification evidence

On 2026-08-31, the generated 6.4 MiB dump restored into a disposable Ceph-backed PostgreSQL Pod.
The `investory` schema was present with 49 table/materialized-relation objects, including 34 ordinary
tables. The disposable Pod and PVC were deleted afterward; the production data and backup claims
remained Bound.
