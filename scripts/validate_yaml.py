#!/usr/bin/env python3
"""Validate the repository's YAML files and internal asset references.

Two checks, both aimed at the mistakes that actually break users' setups:

1. Every ``.yaml``/``.yml`` file parses as valid YAML.
2. Every ``raw.githubusercontent.com/s0len/meta-manager-config/main/...``
   URL found in YAML files, the README and docs points at a file that
   exists in the repo (asset filename mismatches are the most common PR
   error). Kometa template placeholders (``<<key>>`` etc.) are skipped.

Usage:

    python3 scripts/validate_yaml.py            # validate everything
    python3 scripts/validate_yaml.py <paths...> # validate specific files

Exits non-zero when something is broken. Requires pyyaml.
"""

from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
# URLs may contain literal spaces (Kometa accepts them), so capture to
# end-of-line/quote and trim trailing punctuation afterwards.
RAW_URL = re.compile(
    r"raw\.githubusercontent\.com/s0len/meta-manager-config/"
    r"(?:main|refs/heads/main)/([^\"'\n)\]>|]+)"
)
SKIP_DIRS = {".git", "tmp", ".cursor"}


def yaml_files(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p) for p in paths if p.endswith((".yaml", ".yml"))]
    found = []
    for path in REPO_ROOT.rglob("*"):
        if path.suffix not in (".yaml", ".yml"):
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        found.append(path)
    return sorted(found)


def check_syntax(files: list[Path]) -> list[str]:
    errors = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as handle:
                yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            errors.append(f"{path.relative_to(REPO_ROOT)}: {exc}")
    return errors


def check_references(files: list[Path]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings).

    Broken references in the onboarding/config surface (README, docs,
    example config, overlays) are errors — copying those must never 404.
    Missing image assets referenced from metadata/ and collection_files/
    are warnings: the generators intentionally emit ``url_poster`` even
    when no artwork exists yet, and Kometa falls back gracefully.
    """
    errors, warnings = [], []
    doc_files = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "CONTRIBUTING.md",
        *sorted(REPO_ROOT.glob("exampleConfig.y*ml")),
        *sorted((REPO_ROOT / "docs").glob("*.md")),
    ]
    for path in [*files, *doc_files]:
        if not path.exists():
            continue
        rel = path.relative_to(REPO_ROOT)
        soft = rel.parts[0] in ("metadata", "collection_files")
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in RAW_URL.finditer(text):
            ref = urllib.parse.unquote(match.group(1)).rstrip(" .,")
            if "<<" in ref:  # Kometa template placeholder
                continue
            if not (REPO_ROOT / ref).exists():
                target = warnings if soft else errors
                target.append(f"{rel}: references missing file {ref}")
    return sorted(set(errors)), sorted(set(warnings))


def main() -> int:
    files = yaml_files(sys.argv[1:])
    syntax_errors = check_syntax(files)
    ref_errors, ref_warnings = (
        check_references(files) if not sys.argv[1:] else ([], [])
    )

    for err in syntax_errors:
        print(f"SYNTAX  {err}")
    for err in ref_errors:
        print(f"BROKEN  {err}")
    for warn in ref_warnings:
        print(f"warn    {warn}")

    print(f"\n{len(syntax_errors)} syntax error(s), {len(ref_errors)} broken "
          f"reference(s), {len(ref_warnings)} missing-asset warning(s)")
    return 1 if (syntax_errors or ref_errors) else 0


if __name__ == "__main__":
    sys.exit(main())
