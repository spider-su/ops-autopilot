#!/usr/bin/env python3
"""Render every pinned Helm chart referenced by production Argo Applications."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    applications = []
    for path in sorted((args.root / "clusters" / "prd").glob("*.yaml")):
        for document in yaml.safe_load_all(path.read_text(encoding="utf-8")):
            if document and document.get("kind") == "Application":
                source = document.get("spec", {}).get("source", {})
                if source.get("chart"):
                    applications.append((document["metadata"]["name"], source, document.get("spec", {}).get("destination", {}).get("namespace", "default")))

    repositories: dict[str, str] = {}
    added_repositories: set[str] = set()
    for name, source, namespace in applications:
        chart = source["chart"]
        revision = source.get("targetRevision")
        repo = source.get("repoURL")
        if not repo or not revision:
            raise SystemExit(f"{name}: upstream chart must have repoURL and targetRevision")
        alias = repositories.setdefault(repo, f"ops-validation-{len(repositories) + 1}")
        if alias not in added_repositories:
            add = subprocess.run(["helm", "repo", "add", alias, repo, "--force-update"], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if add.returncode:
                raise SystemExit(f"{name}: helm repo add failed\n{add.stderr}")
            added_repositories.add(alias)
        command = [
            "helm", "template", name, f"{alias}/{chart}",
            "--version", str(revision), "--namespace", namespace,
            "--include-crds",
        ]
        values = source.get("helm", {}).get("values")
        values_file = output_dir / f".{name}-values.yaml"
        if values:
            values_file.write_text(values, encoding="utf-8")
            command.extend(["--values", str(values_file)])
        result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise SystemExit(f"{name}: helm template failed\n{result.stderr}")
        (output_dir / f"{name}.yaml").write_text(result.stdout, encoding="utf-8")
        if values_file.exists():
            values_file.unlink()
        print(f"Rendered {name} ({chart} {revision})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
