# 📘 GitOps Argo CD Platform

This repository implements a **clean Argo CD app-of-apps GitOps architecture** for Kubernetes.

It replaces manual deployments and tools like Autopilot with a fully declarative, Git-driven system.

---

# 🧠 Architecture Overview

This repo follows the **app-of-apps pattern**:


Git Repository
↓
Argo CD "root" Application
↓
apps Application layer
↓
individual Applications (e.g. investory)
↓
Kubernetes workloads (Deployments, Services, etc.)


---

# 🧱 Repository Structure


.
├── apps/
│ └── investory/
│ ├── application.yaml # Argo CD Application
│ ├── deployment.yaml # Kubernetes Deployment
│ ├── service.yaml # Kubernetes Service
│ └── kustomization.yaml
│
├── clusters/
│ ├── production/
│ │ ├── root.yaml # Bootstrap entry point
│ │ ├── apps.yaml # App-of-apps controller
│ │ ├── infra.yaml # Infrastructure apps
│ │ └── kustomization.yaml
│ │
│ ├── dev/
│ └── staging/
│
├── infrastructure/
│ └── kustomization.yaml # Platform components (future)
│
└── projects/
└── investory.yaml # Argo CD project RBAC rules


---

# 🚀 How It Works

## 1. Bootstrap (one-time only)

Apply the root application:

```bash
kubectl apply -f clusters/production/root.yaml

This installs the entry point for GitOps.

2. App-of-Apps layer

root.yaml points to:

clusters/production

Inside it:

apps.yaml → manages all applications
infra.yaml → manages platform components
3. Application layer

Inside apps/:

Each service is defined as an Argo CD Application
Example: investory/application.yaml

Each Application points to a workload folder:

apps/investory/
4. Workload layer

Standard Kubernetes manifests:

Deployment
Service
ConfigMaps (optional)

Example:

investory → nginx deployment (2 replicas)
📦 Example Application Flow
Git commit
   ↓
Argo CD detects change
   ↓
root Application syncs
   ↓
apps Application syncs
   ↓
investory Application created/updated
   ↓
Kubernetes Deployment applied
   ↓
Pods start running
🧪 How to Use
🔹 Add a new application
Create folder:
mkdir -p apps/myapp
Add Kubernetes manifests:
deployment.yaml
service.yaml
kustomization.yaml
Create Argo CD Application:
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<your-repo>.git
    targetRevision: main
    path: apps/myapp
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
Commit and push:
git add .
git commit -m "add myapp"
git push

Argo CD will deploy it automatically.

🔹 Check system status
kubectl get applications -n argocd
kubectl get pods -A
kubectl get svc -A
🔹 Debug sync issues
kubectl describe application <name> -n argocd
kubectl logs -n argocd deploy/argocd-repo-server
🧩 Design Principles
Git is the single source of truth
No manual kubectl deployments
Declarative infrastructure only
App-of-apps pattern for scalability
Environment separation via clusters/
🌍 Environments
clusters/dev → development
clusters/staging → pre-production
clusters/production → production

Each environment has its own root application.

🔐 Infrastructure Layer (future)

The infrastructure/ folder is reserved for:

ingress-nginx
cert-manager
monitoring stack
cluster addons
🧠 Key Benefit

Once deployed:

You only modify Git — the cluster continuously reconciles itself.

✅ Status
✔ Argo CD app-of-apps enabled
✔ GitOps workflow active
✔ Example service deployed (investory)
✔ Multi-environment ready
✔ Autopilot removed
