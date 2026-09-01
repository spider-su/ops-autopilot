# Design Decisions: Intentional Constraints

**Date:** September 1, 2026  
**Purpose:** Document why certain enterprise-grade features are deliberately excluded from ops-autopilot.

---

## Overview

ops-autopilot is designed for a **single-operator homelab**, not a general-purpose multi-tenant platform.
This document explains why enterprise-grade capabilities are intentionally deferred and when they should be
reconsidered.

---

## 1. No Kyverno Policy Layer

### What Kyverno Does
Kyverno is a Kubernetes-native policy engine that enforces rules at cluster runtime. Examples:
- "All Pods must have resource requests"
- "Container images must come from approved registries"
- "Pods must run with read-only root filesystems"

### Why ops-autopilot Excludes It

**Current approach:** Validation happens in CI via `scripts/validate.ps1`:
```
Local development
  → Commit to Git
    → GitHub Actions: scripts/validate.ps1 runs
      → Catches schema errors, image pinning, AppProject routing, etc.
        → ✅ Approved or ❌ Rejected before merge
          → Only clean manifests reach `main`
            → Argo CD deploys validated manifests
```

**Why this is sufficient:**
1. Single operator writes all manifests (no accidental violations)
2. Policy violations caught **before they reach Git** (cheaper to fix)
3. No runtime overhead (Kyverno would run on every reconciliation)
4. Simpler debugging (fail fast at CI time, not during Argo sync)

**Example cost comparison:**
- **With Kyverno:** Every Argo sync checks policy (CPU cost) → may reject and mark Application unhealthy
- **With CI validation:** One check per commit (zero runtime cost) → manifests guaranteed compliant

### When to Reconsider

✅ **Add Kyverno if:**
- Multiple operators push to the repository
- Untrusted or auto-generated manifests are deployed
- You need to enforce policies that change at runtime (e.g., image registry whitelist)
- Cluster operators outnumber application developers

❌ **Don't add if:**
- Single operator, implicit trust (current state)
- CI validation catches all your policies
- Runtime overhead is undesirable

---

## 2. No Ceph RBD Snapshots

### What RBD Snapshots Do
Ceph RBD snapshots create point-in-time copies of block storage volumes:
- Instant snapshot of 100 GB volume (metadata only, not full copy)
- Automatic snapshot policies (hourly, daily, weekly)
- Rollback to any snapshot

### Why ops-autopilot Excludes It

**Current approach:** PostgreSQL uses monthly custom-format dumps:
```
PostgreSQL → cron job → pg_dump → Ceph RBD claim (10 GB)
              (runs monthly)           (retains newest only)
```

**Why this is sufficient:**
1. **Only PostgreSQL is stateful** (Investory, SmartApp are stateless)
2. **Monthly is adequate** for homelab (not a production trading system)
3. **Dump-based restore is cleaner:**
   - Can inspect dump before restoring
   - Can verify data integrity (Flyway migrations run on restore)
   - Snapshot rollback is risky (loses all intermediate writes)
4. **No snapshot management complexity:**
   - Ceph snapshots need retention policies (daily? weekly?)
   - Snapshot chains can become orphaned
   - Require manual cleanup if policy changes

**Example scenario:**
```
Production:
  ├─ Prometheus RBD claim (10 GB, ephemeral time-series, no backup needed)
  ├─ Alertmanager RBD claim (2 GB, ephemeral state, no backup needed)
  └─ PostgreSQL RBD claim (5 GB, monthly dump to separate 10 GB claim)

Total backup requirement: One custom dump per month, not continuous snapshots
```

### When to Reconsider

✅ **Add RBD snapshots if:**
- Multiple stateful workloads deployed (not just PostgreSQL)
- Hour-level RPO requirement (current: ~30 days)
- Durable multi-tenant data storage required
- Automated rollback without human verification needed

❌ **Don't add if:**
- PostgreSQL is the only stateful component (current state)
- Monthly dump-based backups meet RPO/RTO
- Snapshot retention policies are too complex to manage

---

## 3. Limited Argo CD Observability

### What "Full" Observability Means
Enterprise Argo setups include:
- Prometheus metrics exported from Argo CD (sync duration, error counts, etc.)
- AlertManager rules for Application sync failures
- ArgoCD Notifications (Slack, email, PagerDuty)
- ArgoCD Server metrics dashboard in Grafana
- Audit logs for every sync decision

### Why ops-autopilot Excludes It

**Current approach:** Manual UI inspection:
```
$ kubectl get applications -n argocd
NAME                  SYNC STATUS  HEALTH STATUS
investory-prod        Synced       Healthy
postgres-prod         Synced       Healthy
smartapp-prod         Synced       Healthy
```

**Why this is sufficient:**
1. **Scale:** 2-5 applications can be visually inspected in 30 seconds
2. **Ownership:** Single operator knows which app they just changed
3. **Simplicity:** No extra Prometheus scrape jobs, no AlertManager config
4. **Observability exists:** Each Application independently reports status
   - Pod health is visible via `kubectl get pods`
   - Sync status is visible via Argo UI
   - Application events are available via `kubectl describe application`

**Time comparison:**
- **With metrics:** 5 min to configure ArgoCD Prometheus exporter + Grafana dashboard
- **Without:** `kubectl get applications` = 5 seconds (better for homelab)

### When to Reconsider

✅ **Add Argo observability if:**
- 10+ applications (visual inspection becomes tedious)
- Multiple operators (need to know who changed what)
- Multi-cluster federation (need central dashboard)
- SLA requirements (need quantified metrics)

❌ **Don't add if:**
- 2-5 applications and single operator (current state)
- Manual inspection provides adequate visibility
- Runtime overhead is undesirable

**Note:** Prometheus/Alertmanager/Grafana are deployed for **application monitoring**, not cluster
observability. You can add Argo CD metrics to the existing Prometheus if needed without additional tools.

---

## 4. No Application-Specific Test Suite

### What This Means
Some cluster repositories include:
- Helm chart unit tests (validating template rendering)
- Policy tests (validating that policies work)
- Integration tests (testing Application sync behavior)

### Why ops-autopilot Excludes It

**Scope boundary:**
```
This repository (ops-autopilot) validates:
  ✅ Helm templates render without errors
  ✅ Kubernetes schema compliance
  ✅ AppProject destinations match resource kinds
  ✅ Image digests are pinned in production
  ❌ NOT: Whether Investory business logic is correct
  ❌ NOT: Whether SmartApp displays the homepage correctly
```

**Why this boundary is correct:**
1. **Application tests belong in app repos** (e.g., spider-su/investory)
   - Investory developers test Investory behavior
   - SmartApp developers test SmartApp behavior
   - Cluster operators test cluster configuration
2. **Cluster repo tests cluster composition**, not app behavior:
   - Does this Application manifest render correctly? (Yes, via Helm lint)
   - Are Dependencies ordered correctly? (Yes, via sync waves)
   - Are Network Policies too restrictive? (Yes, via manual testing)
3. **Testing application behavior requires:**
   - Running the application
   - Calling its endpoints
   - Verifying business logic
   - This is out of scope for cluster ops

**What gets tested:**
```
scripts/validate.ps1:
  ├─ Markdown links (docs are accurate)
  ├─ Helm lint (templates are valid YAML)
  ├─ Helm rendering (templates render without error)
  ├─ Kubernetes schema (output is valid Kubernetes)
  ├─ Policy checks (production has pinned images, no secrets in git)
  ├─ Kustomize rendering (cluster composition is valid)
  └─ CI passes before merge
  
Per-application tests (in app repos):
  ├─ Application unit tests
  ├─ Application integration tests
  ├─ Application smoke tests
  └─ Deployed and verified
```

### When to Reconsider

✅ **Add cluster-level tests if:**
- Complex Network Policies that need automated verification
- Custom chart validation beyond `helm lint`
- Application dependency ordering that needs testing
- Multi-cluster federation with complex routing

❌ **Don't add if:**
- Simple workloads (Investory, SmartApp are straightforward)
- Manual testing is sufficient
- App repos already have adequate tests

---

## 5. No Cost Tracking or Resource Attribution

### What Cost Tracking Means
Enterprise setups track:
- CPU/memory cost per application
- Storage cost per workload
- Network egress charges
- Licensing per container

### Why ops-autopilot Excludes It

**Your infrastructure model:**
```
Proxmox license: $XXX/year (fixed, regardless of workloads)
Mac Mini hardware: $XXX × 3 (capital cost, amortized over 5 years)
Gigabit switch: $XXX (fixed, regardless of workloads)
Ceph storage: Included in Mac Mini (no per-GB charge)
```

**Why cost attribution is irrelevant:**
1. **No chargeback model:** Single person owns and pays for everything
2. **No capacity planning:** You're not selling capacity to tenants
3. **No multi-cost-center billing:** It's a hobby, not a business
4. **Fixed costs dominate:** Hardware cost >> operational cost
5. **Scaling is organic:** You'll add workloads because you need them, not because of utilization

**What tracking would cost:**
- Setup: 2-4 hours to configure Prometheus rules, labels, dashboards
- Monthly: 1 hour to review cost breakdowns
- Result: Pretty dashboards showing "Investory costs $0.04/month in power"

### When to Reconsider

✅ **Add cost tracking if:**
- Selling cluster capacity (chargeback to departments)
- Cloud infrastructure with per-resource charges (AWS, GCP, Azure)
- Multiple cost centers funding different workloads
- Capacity planning for growth

❌ **Don't add if:**
- Hobby project with fixed hardware (current state)
- Single person owns the cluster
- No chargeback or billing model

---

## Design Philosophy

### The Core Principle

**Move complexity as far left as possible.**

```
Complexity ladder (highest to lowest):
  ↑ Runtime (during Argo sync) ← Kyverno complexity
  │ Deployment (during roll-out) ← App tests complexity
  │ Pre-commit (during git push) ← CI validation ← Current ops-autopilot
  ↓ Development (before commit) ← Local validation
```

**ops-autopilot philosophy:**
1. Catch errors at **development time** (local `helm lint`)
2. Validate at **CI time** (pre-commit checks)
3. Only deploy **proven manifests** (Argo deploys validated YAML)
4. Minimize **runtime complexity** (no runtime policy engine)

### Size-Appropriate Tooling

|Scale|Operators|Apps|Tooling|
|---|---|---|---|
|Solo homelab|1|2-5|CI validation (current)|
|Small team|2-5|5-15|+ Kyverno + Argo metrics|
|Platform team|5+|15+|+ ArgoCD Notifications + multi-cluster|
|Enterprise|50+|100+|+ Cost tracking + compliance + audit|

**ops-autopilot is sized for: 1 operator, 2-5 applications.**

---

## Decision Matrix: When to Add Capabilities

Use this table to decide when to add enterprise features:

| Capability | Add When | Don't Add If |
|---|---|---|
| **Kyverno** | Multi-operator, untrusted deployments | Single operator, CI validation works |
| **RBD snapshots** | Multiple stateful workloads, hour-level RPO | PostgreSQL-only, monthly RPO acceptable |
| **Argo metrics** | 10+ applications, SLA requirements | 2-5 applications, manual inspection sufficient |
| **App tests** | Complex application logic, integration testing | Simple stateless apps, unit tests in app repos |
| **Cost tracking** | Multi-tenant, chargeback model | Hobby infrastructure, fixed costs |

---

## How These Decisions Appear in the Repository

### In ROADMAP.md
```markdown
## Intentional Non-Goals
[See ROADMAP.md for the list of deliberately excluded features]

## Explicitly deferred
[See ROADMAP.md for features that might be added later]
```

### In Architecture
```markdown
# docs/architecture/overview.md
Includes statements like:
- "Argo CD reconciles the remote repository, not a developer's working tree"
- "Platform and stateless child Applications carry Argo's resources finalizer"
- "Pod security baseline of RuntimeDefault seccomp, no privilege escalation"
```

### In Bootstrap
```markdown
# docs/operations/bootstrap.md
- Recovery boundary clearly defined
- PostgreSQL backup strategy explained
- Policy enforcement documented
```

### In Validation
```markdown
# docs/development/validation.md
- Lists what the validator checks (catches early)
- Lists what it doesn't check (application behavior)
```

---

## Adding Features: The Decision Process

When you want to add one of these capabilities:

1. **Identify the trigger:**
   ```
   Example: "I have 10 applications now, Argo UI is slow"
   ```

2. **Verify it's not a process problem:**
   ```
   Have I tried: kubectl get applications -n argocd?
   Am I filtering/searching correctly?
   Is the problem scale (10 apps) or my workflow?
   ```

3. **Check the decision matrix above.**
   ```
   10 applications + Argo observability = YES, reconsider
   ```

4. **Implement narrowly:**
   ```
   Don't add full Prometheus metrics; just add:
     - ArgoCD Prometheus exporter
     - One Grafana dashboard showing sync status
   ```

5. **Document the change:**
   ```
   Update ROADMAP.md to move from "Intentional Non-Goals"
   to the appropriate theme section, then implement
   ```

6. **Update this document:**
   ```
   Change the "When to Reconsider" section from "if"
   to "Now that we have", explaining what changed
   ```

---

## Future: If You Scale

### When Scaling to 5-10 Applications
Consider adding:
- ✅ ArgoCD Prometheus exporter (light weight)
- ✅ Grafana dashboard for Application status
- ❌ Full cost tracking (still not needed)

### When Scaling to 10-20 Applications
Consider:
- ✅ ApplicationSet (reduce duplication)
- ✅ Kyverno (multiple operators)
- ✅ Multi-cluster federation planning
- ❌ Sealed Secrets (SOPS/age still works)

### When Scaling Beyond 20 Applications
Reconsider:
- Architecture (single cluster vs. multi-cluster)
- Platform abstraction (Flux CD, Helm Umbrella, or Kyverno + templates)
- Multi-tenancy (AppProject per team)
- Observability (full Prometheus + logging + tracing)

---

## Summary

ops-autopilot demonstrates **pragmatic engineering**: each excluded feature has a clear answer to
"why not add this?" and a clear trigger for "when to reconsider."

**Current state is intentional, not incomplete.**

Keep this document as a reference when new features are proposed. Before adding anything, check:
1. Is it in "Intentional Non-Goals"? (If yes, understand why before changing)
2. What does scaling trigger? (Use the decision matrix)
3. What maintenance cost does it add? (Runtime, operational, documentation)
4. Is there a simpler alternative? (Usually yes for homelab)


