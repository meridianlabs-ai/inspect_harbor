#!/usr/bin/env python3
"""Validate docs/overrides.yml against the Harbor registry.

Runs as a required CI check on every PR (see .github/workflows/build.yaml).
The goal is to prevent an overrides file that is syntactically valid YAML
but semantically broken, with four failure modes we care about:

    1. A registry dataset has no entry in overrides.yml. Usually the
       nightly cron auto-stubbed it with `categories: []` and a reviewer
       forgot to fill it in.

    2. An entry has empty/missing/invalid `categories`. Same cause.

    3. An entry uses a category not in the fixed vocabulary. Usually a
       typo or a new category that inspect_ai hasn't added to its
       CATEGORY_VOCAB.

    4. An entry sets `function_name` to a value that isn't a valid
       Python identifier — would crash the generator at decorate time.

When any of these fire the script exits non-zero with a bulleted summary
the reviewer can act on. When all pass, prints a one-line OK summary.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml
from generate_tasks import (
    filter_excluded,
    load_exclude_patterns,
    scrape_hub_slugs,
)

OVERRIDES_FILE = Path(__file__).parent.parent / "docs" / "overrides.yml"

# Mirror of inspect_ai's docs/evals/sync.py:CATEGORY_VOCAB. Must be kept in
# sync if inspect_ai extends the taxonomy; their sync_harbor.py will reject
# categories outside its own vocabulary regardless of what we accept here.
CATEGORY_VOCAB: set[str] = {
    "Coding",
    "Assistants",
    "Cybersecurity",
    "Safeguards",
    "Mathematics",
    "Reasoning",
    "Knowledge",
    "Science",
    "Biology",
    "Chemistry",
    "Physics",
    "Professional",
    "Finance",
    "Medicine",
    "Law",
    "Multimodal",
    "Scheming",
    "Behavior",
}


def fetch_registered_slugs() -> set[str]:
    """Return the canonical ``{org/name}`` slug set the registry would emit.

    Uses the same scrape + exclude pipeline as ``generate_tasks.py`` — what
    you get back is exactly the dataset set that ends up in
    ``src/inspect_harbor/_tasks.py``. Skips the per-package metadata fetch
    (we only need slug identity, not version/samples), so it's quick.
    """
    slugs = scrape_hub_slugs()
    slugs = filter_excluded(slugs, load_exclude_patterns())
    return {f"{org}/{name}" for org, name in slugs}


def load_overrides() -> dict[str, dict[str, Any]]:
    """Load docs/overrides.yml and return ``{slug: fields}``."""
    if not OVERRIDES_FILE.exists():
        sys.exit(f"error: {OVERRIDES_FILE} does not exist")
    data = yaml.safe_load(OVERRIDES_FILE.read_text()) or {}
    if not isinstance(data, dict):
        sys.exit(f"error: {OVERRIDES_FILE} must be a mapping at top level")
    return {name: fields for name, fields in data.items() if isinstance(fields, dict)}


def main() -> None:
    """Validate docs/overrides.yml against the registry; exit non-zero on failure."""
    print(f"Validating {OVERRIDES_FILE}...")
    overrides = load_overrides()
    print(f"  Parsed {len(overrides)} override entries")

    print("Resolving registered slugs (scrape + exclude)...")
    registered = fetch_registered_slugs()
    print(f"  Found {len(registered)} registered slug(s)")

    missing_overrides = sorted(registered - overrides.keys())
    orphan_overrides = sorted(overrides.keys() - registered)

    empty_categories: list[str] = []
    invalid_categories: list[tuple[str, list[str]]] = []
    invalid_func_names: list[tuple[str, str]] = []

    for name, fields in overrides.items():
        cats = fields.get("categories")
        if not isinstance(cats, list) or len(cats) == 0:
            empty_categories.append(name)
        else:
            bad = [c for c in cats if not isinstance(c, str) or c not in CATEGORY_VOCAB]
            if bad:
                invalid_categories.append((name, bad))

        fn = fields.get("function_name")
        if fn is not None and (not isinstance(fn, str) or not fn.isidentifier()):
            invalid_func_names.append((name, str(fn)))

    errors: list[str] = []

    if missing_overrides:
        lines = [
            f"{len(missing_overrides)} registered slug(s) have no entry in "
            f"docs/overrides.yml:",
            *(f"  - {n}" for n in missing_overrides),
            "  Fix: run `uv run python scripts/generate_tasks.py` to auto-stub, "
            "then fill in the `categories:` field.",
        ]
        errors.append("\n".join(lines))

    if empty_categories:
        lines = [
            f"{len(empty_categories)} override entr(ies) have empty or missing "
            f"`categories`:",
            *(f"  - {n}" for n in empty_categories),
            "  Fix: add one or more categories from the vocabulary in "
            "docs/overrides.yml's header.",
        ]
        errors.append("\n".join(lines))

    if invalid_categories:
        lines = [
            f"{len(invalid_categories)} override entr(ies) use categories "
            f"outside the vocabulary:",
            *(f"  - {name}: {bad}" for name, bad in invalid_categories),
            f"  Valid categories: {sorted(CATEGORY_VOCAB)}",
        ]
        errors.append("\n".join(lines))

    if invalid_func_names:
        lines = [
            f"{len(invalid_func_names)} override entr(ies) have invalid "
            f"`function_name`:",
            *(
                f"  - {name}: {fn!r} is not a valid Python identifier"
                for name, fn in invalid_func_names
            ),
        ]
        errors.append("\n".join(lines))

    if orphan_overrides:
        print(
            f"\nwarning: {len(orphan_overrides)} override entr(ies) have no "
            f"matching registered slug (possibly renamed upstream or "
            f"regen not run):",
            file=sys.stderr,
        )
        for n in orphan_overrides:
            print(f"  - {n}", file=sys.stderr)

    if errors:
        print("\n" + ("=" * 60), file=sys.stderr)
        print("VALIDATION FAILED", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for err in errors:
            print("\n" + err, file=sys.stderr)
        sys.exit(1)

    print(f"\n✓ All {len(overrides)} override entries valid")


if __name__ == "__main__":
    main()
