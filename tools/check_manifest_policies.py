#!/usr/bin/env python3
"""Repository policy and documentation checks for rendered GitOps manifests."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import yaml

WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}
WORKLOAD_FILES = {"investory-prd.yaml", "smartapp-prd.yaml", "postgres-prd.yaml"}
ALLOWED_DESTINATIONS = {
    "base-app": {"investory-prod", "investory-dev", "smartapp-prod", "smartapp-dev", "postgres", "postgres-dev"},
    "platform-app": {"argocd", "infrastructure", "metallb-system", "ingress-nginx", "monitoring", "ceph-csi-rbd"},
}
REQUIRED_DOC_TEXT = {
    "README.md": ("clusters/", "applications/", "main"),
    "docs/architecture/overview.md": ("RBD", "CephFS", "platform-app", "base-app"),
    "docs/development/validation.md": ("kubeconform", "upstream", "policy"),
}


def documents(path: Path):
    if path.is_file() and path.suffix in {".yaml", ".yml"}:
        paths = [path]
    else:
        paths = sorted(path.rglob("*.yaml")) + sorted(path.rglob("*.yml"))
    for file in paths:
        if "templates" in file.parts:
            continue
        try:
            for document in yaml.safe_load_all(file.read_text(encoding="utf-8")):
                if document:
                    yield file, document
        except yaml.YAMLError as error:
            raise SystemExit(f"Invalid YAML in {file}: {error}")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def check_source_manifests(root: Path, errors: list[str]) -> None:
    for file, document in documents(root / "clusters"):
        kind = document.get("kind")
        spec = document.get("spec", {})
        if kind == "Application":
            source = spec.get("source", {})
            if source.get("targetRevision") == "dev":
                fail(errors, f"{file}: targetRevision dev is not allowed")
            destination = spec.get("destination", {})
            if destination.get("server") != "https://kubernetes.default.svc":
                fail(errors, f"{file}: destination server must be the in-cluster API")
            project = spec.get("project")
            namespace = destination.get("namespace")
            if project in ALLOWED_DESTINATIONS and namespace not in ALLOWED_DESTINATIONS[project]:
                fail(errors, f"{file}: {project} cannot deploy to {namespace}")
            options = spec.get("syncPolicy", {}).get("syncOptions", [])
            if any(re.match(r"(?i)^(replace|force)=true$", option) for option in options):
                fail(errors, f"{file}: dangerous sync option present")
        elif kind == "AppProject":
            destinations = {entry.get("namespace") for entry in spec.get("destinations", [])}
            if document.get("metadata", {}).get("name") in ALLOWED_DESTINATIONS:
                expected = ALLOWED_DESTINATIONS[document["metadata"]["name"]]
                if destinations != expected:
                    fail(errors, f"{file}: AppProject destinations do not match the declared ownership boundary")
        elif kind == "Secret":
            if document.get("data") or document.get("stringData"):
                fail(errors, f"{file}: Secret payloads must not be committed")

    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True).stdout.decode()
    for relative in tracked.split("\0"):
        if not relative:
            continue
        candidate = root / relative
        if candidate.name.startswith(".env") or candidate.suffix == ".env":
            fail(errors, f"{candidate}: environment file must not be committed")
            continue
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text):
            fail(errors, f"{candidate}: private key payload detected")
        if re.search(r"\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})\b", text):
            fail(errors, f"{candidate}: high-confidence token detected")


def check_workloads(workload_dir: Path, errors: list[str]) -> None:
    for file, document in documents(workload_dir):
        if file.name not in WORKLOAD_FILES or document.get("kind") not in WORKLOAD_KINDS:
            continue
        pod_spec = document.get("spec", {}).get("template", {}).get("spec", {})
        if document.get("kind") in {"Job", "CronJob"}:
            pod_spec = document.get("spec", {}).get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", pod_spec)
        for container in pod_spec.get("containers", []) + pod_spec.get("initContainers", []):
            name = container.get("name", "unnamed")
            resources = container.get("resources", {})
            if not resources.get("requests") or not resources.get("limits"):
                fail(errors, f"{file}/{name}: requests and limits are required")
            if document.get("kind") in {"Deployment", "StatefulSet", "DaemonSet"}:
                for probe in ("startupProbe", "readinessProbe", "livenessProbe"):
                    if not container.get(probe):
                        fail(errors, f"{file}/{name}: {probe} is required")
            image = container.get("image", "")
            if file.name.endswith("-prd.yaml") and "@sha256:" not in image:
                fail(errors, f"{file}/{name}: production image must use a digest")
            if file.name.endswith("-prd.yaml") and container.get("imagePullPolicy") != "IfNotPresent":
                fail(errors, f"{file}/{name}: production pull policy must be IfNotPresent")


def check_docs(root: Path, errors: list[str]) -> None:
    for relative, required in REQUIRED_DOC_TEXT.items():
        text = (root / relative).read_text(encoding="utf-8")
        for value in required:
            if value.lower() not in text.lower():
                fail(errors, f"{relative}: missing documented term {value}")
    forbidden = ["LoadRestrictionsNone", "applications/postgres/app-dev.yaml", "applications/smartapp/app-dev.yaml"]
    for relative in ["README.md", "ROADMAP.md", "CHANGELOG.md", "docs"]:
        path = root / relative
        candidates = [path] if path.is_file() else path.rglob("*.md")
        for candidate in candidates:
            text = candidate.read_text(encoding="utf-8")
            for value in forbidden:
                if value in text:
                    fail(errors, f"{candidate}: stale reference {value}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--workload-dir", type=Path, required=True)
    args = parser.parse_args()
    errors: list[str] = []
    check_source_manifests(args.root, errors)
    check_workloads(args.workload_dir, errors)
    check_docs(args.root, errors)
    if errors:
        print("Manifest policy failures:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Manifest policy and documentation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
