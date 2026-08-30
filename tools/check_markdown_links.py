#!/usr/bin/env python3
"""Check that repository-local Markdown links resolve to existing files."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
SKIPPED_PREFIXES = ("http://", "https://", "mailto:", "#", "app://")


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts and ".idea" not in path.parts
    )


def link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if " " in target and not target.startswith(SKIPPED_PREFIXES):
        target = target.split(" ", 1)[0]
    return unquote(target.split("#", 1)[0])


def main() -> int:
    failures: list[str] = []
    documents = markdown_files()
    for document in documents:
        text = document.read_text(encoding="utf-8-sig")
        for match in LINK_PATTERN.finditer(text):
            raw_target = match.group(1)
            if raw_target.startswith(SKIPPED_PREFIXES):
                continue
            target = link_target(raw_target)
            if not target:
                continue
            resolved = (document.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                failures.append(
                    f"{document.relative_to(ROOT)}: link escapes repository: {raw_target}"
                )
                continue
            if not resolved.exists():
                failures.append(
                    f"{document.relative_to(ROOT)}: missing target: {raw_target}"
                )

    if failures:
        print("Markdown link validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Markdown links passed ({len(documents)} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
