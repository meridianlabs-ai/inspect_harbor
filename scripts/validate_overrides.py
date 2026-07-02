#!/usr/bin/env python3
"""Validate docs/overrides.yml against the Harbor registry.

Runs as a CI check on every PR (see .github/workflows/build.yaml). The goal
is to catch an overrides file that is valid YAML but semantically broken.

Hard failures (exit non-zero) all validate the *committed* overrides.yml and
need no network:

    1. An entry has empty/missing/invalid `categories`. Usually the nightly
       cron auto-stubbed a new dataset with `categories: []` and it wasn't
       filled in — this is what gates the nightly triage PR.

    2. An entry uses a category not in the fixed vocabulary. Usually a typo
       or a new category that inspect_ai hasn't added to its CATEGORY_VOCAB.

    3. An entry sets `function_name` to a value that isn't a valid Python
       identifier — would crash the generator at decorate time.

Non-fatal warnings (surfaced, but exit zero) reflect *upstream* drift rather
than a problem with this PR, so they must not block unrelated PRs:

    - A registered hub slug has no entry in overrides.yml yet. The nightly
      cron's generate_tasks.py run auto-stubs new datasets into overrides.yml
      (which then trips failure 1 until triaged), so hard-failing here too
      would only block unrelated PRs whenever a dataset lands upstream.

    - An override entry has no matching registered slug (renamed upstream, or
      regen not yet run).

When a hard failure fires the script exits non-zero with a bulleted summary;
otherwise it prints any warnings and a one-line OK summary.
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

    if missing_overrides:
        print(
            f"\nwarning: {len(missing_overrides)} registered hub slug(s) have "
            f"no entry in docs/overrides.yml yet (new upstream dataset(s) — the "
            f"nightly cron will auto-stub them; not a failure for this PR):",
            file=sys.stderr,
        )
        for n in missing_overrides:
            print(f"  - {n}", file=sys.stderr)
        print(
            "  To stub now: run `uv run python scripts/generate_tasks.py`, "
            "then fill in the `categories:` field.",
            file=sys.stderr,
        )

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
