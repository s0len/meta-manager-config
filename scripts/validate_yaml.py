#!/usr/bin/env python3
"""Validate the repository's YAML files and internal asset references.

Three checks, all aimed at the mistakes that actually break users'
setups:

1. Every ``.yaml``/``.yml`` file parses as valid YAML.
2. No mapping contains a duplicate key. Kometa loads YAML through
   ruamel, which *rejects* duplicates, while pyyaml's ``safe_load``
   silently keeps the last one -- so a show missing a season key (its
   ``episodes:`` blocks collapsing into one mapping) parses fine here
   but aborts every user's run.
3. Every ``raw.githubusercontent.com/s0len/meta-manager-config/main/...``
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


def _rel(path: Path) -> Path:
    """Repo-relative display path; explicit CLI args may be relative."""
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return path


def check_syntax(files: list[Path]) -> list[str]:
    errors = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as handle:
                yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            errors.append(f"{_rel(path)}: {exc}")
    return errors


def check_duplicate_keys(files: list[Path]) -> list[str]:
    """Report every mapping key that appears twice in the same mapping.

    ``yaml.safe_load`` accepts duplicates and keeps the last value, so
    this needs the node tree rather than the loaded document. Walking it
    (instead of raising from a custom constructor) reports every
    duplicate in one pass instead of only the first.
    """
    errors = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as handle:
                root = yaml.compose(handle)
        except yaml.YAMLError:
            continue  # already reported by check_syntax
        if root is None:
            continue
        rel = _rel(path)
        stack = [root]
        while stack:
            node = stack.pop()
            if isinstance(node, yaml.MappingNode):
                seen: dict[str, int] = {}
                for key_node, value_node in node.value:
                    stack.append(value_node)
                    key = getattr(key_node, "value", None)
                    if not isinstance(key, str):
                        continue
                    line = key_node.start_mark.line + 1
                    if key in seen:
                        errors.append(
                            f"{rel}:{line}: duplicate key '{key}' "
                            f"(first seen on line {seen[key]})"
                        )
                    else:
                        seen[key] = line
            elif isinstance(node, yaml.SequenceNode):
                stack.extend(node.value)
    return sorted(set(errors))


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
        rel = _rel(path)
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
    dupe_errors = check_duplicate_keys(files)
    ref_errors, ref_warnings = (
        check_references(files) if not sys.argv[1:] else ([], [])
    )

    for err in syntax_errors:
        print(f"SYNTAX  {err}")
    for err in dupe_errors:
        print(f"DUPKEY  {err}")
    for err in ref_errors:
        print(f"BROKEN  {err}")
    for warn in ref_warnings:
        print(f"warn    {warn}")

    print(f"\n{len(syntax_errors)} syntax error(s), {len(dupe_errors)} "
          f"duplicate key(s), {len(ref_errors)} broken reference(s), "
          f"{len(ref_warnings)} missing-asset warning(s)")
    return 1 if (syntax_errors or dupe_errors or ref_errors) else 0


if __name__ == "__main__":
    sys.exit(main())
