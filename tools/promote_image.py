#!/usr/bin/env python3
"""Update one production chart to a validated immutable image digest."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", choices=("investory", "smartapp", "postgres"), required=True)
    parser.add_argument("--digest", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", args.digest):
        raise SystemExit("digest must match sha256:<64 lowercase hexadecimal characters>")

    path = Path("applications") / args.app / "values-prd.yaml"
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(r"(?m)^(\s+)digest:\s*sha256:[0-9a-f]{64}\s*$", rf"\1digest: {args.digest}", text)
    if count != 1:
        raise SystemExit(f"expected exactly one production digest in {path}, found {count}")
    path.write_text(updated, encoding="utf-8")
    print(f"Promoted {args.app} to {args.digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
