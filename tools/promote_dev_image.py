#!/usr/bin/env python3
"""Update the orchestrator dev chart to one published commit-tagged image."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"sha-[0-9a-f]{40}", args.tag):
        raise SystemExit("tag must match sha-<40 lowercase hexadecimal characters>")

    path = Path("applications/investory-orchestrator/values-dev.yaml")
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"(?m)^(\s+tag:\s*)\S+\s*$",
        rf"\g<1>{args.tag}",
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"expected exactly one image tag in {path}")
    path.write_text(updated, encoding="utf-8")
    print(f"Promoted development orchestrator image to {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
