#!/usr/bin/env python3
"""Generate static task functions from the Harbor registry.

We discover every dataset by scraping ``hub.harborframework.com/datasets``
for ``(org, name)`` slugs, then fetch metadata for each via
``PackageDatasetClient.get_dataset_metadata``. The website is the only
public enumeration source until Harbor exposes a listing API
(see https://github.com/harbor-framework/harbor/issues/1580).

Per-dataset overrides (categories, hand-mapped function names, paper /
repo links) live in ``docs/overrides.yml``.
"""

import argparse
import asyncio
import fnmatch
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, TypedDict

import yaml
from _http import curl_get
from _templates import (
    PACKAGE_TASK_TEMPLATE,
    PAGE_TEMPLATE,
    REGISTRY_YML_HEADER,
    TASKS_TEMPLATE,
)
from harbor.registry.client.package import PackageDatasetClient

REGISTRY_SITE_BASE = "https://hub.harborframework.com"
REGISTRY_SITE_MAX_PAGES = 20
# Concurrency cap on Supabase metadata fetches. ~190 packages × 600ms each
# is ~2min sequential; with 10 in flight it's ~12s.
PACKAGE_FETCH_CONCURRENCY = 10
# Minimum slug count we expect from the scrape (pre-exclude). Below this we
# refuse to proceed: the website likely changed its HTML, our regex stopped
# matching, or the site is partially down. Without this guard a broken scrape
# would silently orphan-drop every entry in overrides.yml.
MIN_EXPECTED_SLUGS = 50
# Hard cap on description length in the registry listing table; longer descs
# are truncated with an ellipsis. Per-dataset .qmd pages keep the full text.
LISTING_DESC_MAX = 100

TASKS_FILE = Path(__file__).parent.parent / "src" / "inspect_harbor" / "_tasks.py"
REGISTRY_YML_FILE = Path(__file__).parent.parent / "docs" / "registry-listing.yml"
OVERRIDES_FILE = Path(__file__).parent.parent / "docs" / "overrides.yml"
EXCLUDE_FILE = Path(__file__).parent.parent / "docs" / "exclude.yml"
# Per-dataset landing pages, one ``.qmd`` per dataset, linked from the
# registry listing. Wiped and regenerated on every run; don't hand-edit.
REGISTRY_PAGES_DIR = Path(__file__).parent.parent / "docs" / "registry"
# Local-dev cache: speeds up Quarto preview reloads (otherwise every
# reload would re-scrape + re-fetch metadata). Cleared by deleting the dir.
CACHE_DIR = Path(__file__).parent.parent / ".cache" / "harbor-registry"
CACHE_TTL_SECONDS = 10 * 60  # 10 minutes


class FetchedDataset(TypedDict):
    """Raw shape produced by ``fetch_package_datasets``."""

    name: str  # ``org/name`` slug
    description: str
    samples: int
    version: str  # resolved sha for the ``latest`` ref


class Dataset(FetchedDataset):
    """A ``FetchedDataset`` decorated by ``decorate_datasets``.

    Adds the bits consumers (templates, listing emitter) need.
    """

    func_name: str
    harbor_url: str
    clean_description: str


def _cached(
    cache_name: str, fetch: Callable[[], bytes], ttl: int = CACHE_TTL_SECONDS
) -> bytes:
    """Read ``cache_name`` from CACHE_DIR if fresh, else call ``fetch`` and write."""
    path = CACHE_DIR / cache_name
    if path.exists():
        age = time.time() - path.stat().st_mtime
        if age < ttl:
            return path.read_bytes()
    data = fetch()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def _write_if_changed(path: Path, content: str) -> bool:
    """Write ``content`` to ``path`` only if it differs from what's there."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return False
    path.write_text(content)
    return True


def _default_description(dataset_name: str) -> str:
    """Fallback used when a Harbor metadata entry has no ``description``."""
    return f"{dataset_name} dataset from Harbor registry"


def scrape_hub_slugs() -> set[tuple[str, str]]:
    """Paginate ``hub.harborframework.com/datasets`` and return all (org, name) pairs."""
    print(f"Scraping {REGISTRY_SITE_BASE}/datasets...")
    pairs: set[tuple[str, str]] = set()
    pages_scraped = 0
    href_pattern = re.compile(r"/datasets/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")

    for page in range(1, REGISTRY_SITE_MAX_PAGES + 1):
        url = f"{REGISTRY_SITE_BASE}/datasets?page={page}"
        body = _cached(
            f"hub-page-{page}.html",
            lambda url=url: curl_get(url, max_time=60),
        ).decode()
        pages_scraped = page
        new_pairs = set(href_pattern.findall(body))
        if not new_pairs - pairs:
            break
        pairs |= new_pairs

    print(f"  {len(pairs)} unique slugs across {pages_scraped} page(s)")
    if len(pairs) < MIN_EXPECTED_SLUGS:
        raise RuntimeError(
            f"Scrape returned only {len(pairs)} slug(s) (expected ≥ "
            f"{MIN_EXPECTED_SLUGS}). The website likely changed shape or is "
            "down; refusing to proceed (would orphan-drop every override)."
        )
    return pairs


def load_exclude_patterns() -> list[str]:
    """Load slug-exclusion globs from ``docs/exclude.yml``.

    Each entry is a fnmatch pattern matched against the full ``org/name``
    slug (e.g. ``openthoughts/*``, ``harbor/hello-world``). Empty list if
    the file is absent or malformed.
    """
    if not EXCLUDE_FILE.exists():
        return []
    try:
        data = yaml.safe_load(EXCLUDE_FILE.read_text()) or []
    except yaml.YAMLError as exc:
        print(f"  ⚠ {EXCLUDE_FILE} failed to parse ({exc})", file=sys.stderr)
        return []
    if not isinstance(data, list):
        print(
            f"  ⚠ {EXCLUDE_FILE} top-level must be a list; got {type(data).__name__}",
            file=sys.stderr,
        )
        return []
    return [p for p in data if isinstance(p, str)]


def filter_excluded(
    slugs: set[tuple[str, str]], patterns: list[str]
) -> set[tuple[str, str]]:
    """Drop any ``(org, name)`` whose ``org/name`` slug matches a pattern."""
    if not patterns:
        return slugs
    kept: set[tuple[str, str]] = set()
    excluded = 0
    for org, name in slugs:
        slug = f"{org}/{name}"
        if any(fnmatch.fnmatch(slug, p) for p in patterns):
            excluded += 1
            continue
        kept.add((org, name))
    if excluded:
        print(f"  Excluded {excluded} slug(s) via {len(patterns)} exclude pattern(s)")
    return kept


def fetch_package_datasets(slugs: set[tuple[str, str]]) -> list[FetchedDataset]:
    """Fetch metadata for every scraped slug via ``PackageDatasetClient``.

    Per-slug responses are cached under
    ``.cache/harbor-registry/pkg-<org>__<name>.json`` to keep Quarto
    preview reloads cheap. Aborts if more than half of the fetches fail.
    """
    candidates = sorted(slugs)
    print(f"Fetching metadata for {len(candidates)} package candidate(s)...")

    sem = asyncio.Semaphore(PACKAGE_FETCH_CONCURRENCY)
    pkg_client = PackageDatasetClient()

    async def _fetch_one(org: str, name: str) -> FetchedDataset | None:
        slug = f"{org}/{name}"
        cache_path = CACHE_DIR / f"pkg-{org}__{name}.json"
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < CACHE_TTL_SECONDS:
                return json.loads(cache_path.read_text())
        async with sem:
            try:
                meta = await pkg_client.get_dataset_metadata(slug)
            except Exception as e:
                print(
                    f"  ⚠ {slug}: {type(e).__name__}: {str(e)[:120]}",
                    file=sys.stderr,
                )
                return None
        entry: FetchedDataset = FetchedDataset(
            name=slug,
            description=(meta.description or "").strip(),
            samples=len(meta.task_ids),
            version=meta.version or "",
        )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(entry))
        return entry

    async def _fetch_all() -> list[FetchedDataset | None]:
        return list(await asyncio.gather(*[_fetch_one(o, n) for o, n in candidates]))

    raw = asyncio.run(_fetch_all())
    packages = [r for r in raw if r is not None]
    failed = len(raw) - len(packages)
    if raw and failed / len(raw) > 0.5:
        raise RuntimeError(
            f"More than half of package metadata fetches failed "
            f"({failed}/{len(raw)}); aborting (likely Supabase or network "
            "issue). See per-slug warnings above."
        )
    print(f"  Fetched {len(packages)} package metadata entries")
    return packages


def dataset_name_to_function_name(dataset_name: str) -> str:
    """Convert a slug to a valid Python function name (auto-derived default).

    Callers can override per-dataset via ``function_name:`` in
    ``docs/overrides.yml`` — see ``decorate_datasets``.

    Examples:
        terminal-bench/terminal-bench   -> terminal_bench_terminal_bench
        scale-ai/swe-atlas-qna          -> scale_ai_swe_atlas_qna
        harbor/hello-world              -> harbor_hello_world
        LiteCoder/LiteCoder-rl          -> litecoder_litecoder_rl
    """
    return dataset_name.lower().replace("-", "_").replace(".", "_").replace("/", "_")


def decorate_datasets(
    fetched: list[FetchedDataset], overrides: dict[str, dict[str, Any]]
) -> list[Dataset]:
    """Attach the derived fields every consumer needs.

    Honors two per-dataset overrides from ``docs/overrides.yml``:

    * ``function_name`` — replace the auto-derived Python identifier
      (e.g. ``swe_bench_swe_bench_verified`` → ``swe_bench_verified``).
      Must be a valid identifier.
    * ``desc`` — replace Harbor's metadata description. Flows through to
      the @task docstring, the listing entry, and the per-dataset .qmd.
      Same field that ``inspect_ai/docs/evals/sync_harbor.py`` reads, so
      one override drives every consumer.
    """
    out: list[Dataset] = []
    for d in fetched:
        org, short = d["name"].split("/", 1)
        url = f"{REGISTRY_SITE_BASE}/datasets/{org}/{short}/latest"

        override = overrides.get(d["name"], {})

        custom = override.get("function_name")
        if custom is not None:
            if not isinstance(custom, str) or not custom.isidentifier():
                raise RuntimeError(
                    f"Invalid function_name override for {d['name']!r}: "
                    f"{custom!r} is not a valid Python identifier."
                )
            func_name = custom
        else:
            func_name = dataset_name_to_function_name(d["name"])

        description = d["description"]
        custom_desc = override.get("desc")
        if custom_desc is not None:
            if not isinstance(custom_desc, str):
                raise RuntimeError(
                    f"Invalid desc override for {d['name']!r}: must be a string."
                )
            if custom_desc.strip():
                description = custom_desc

        out.append(
            Dataset(
                name=d["name"],
                description=description,
                samples=d["samples"],
                version=d["version"],
                func_name=func_name,
                harbor_url=url,
                clean_description=_clean_registry_description(description),
            )
        )
    return out


def generate_tasks_content(registry: list[Dataset]) -> str:
    """Generate the content of ``_tasks.py`` — one ``@task`` per dataset.

    Each function takes ``ref: str = "latest"`` and forwards
    ``package_name``/``package_ref`` to ``_harbor_base``. The resolved sha
    for ``latest`` is surfaced in the docstring.
    """
    functions: list[str] = []
    func_name_to_source: dict[str, str] = {}

    for d in registry:
        name = d["name"]
        func_name = d["func_name"]

        prior = func_name_to_source.get(func_name)
        if prior is not None and prior != name:
            raise RuntimeError(
                f"Function-name collision: both {prior!r} and {name!r} map "
                f"to {func_name!r}. Add a ``function_name:`` override in "
                f"docs/overrides.yml to disambiguate."
            )
        func_name_to_source[func_name] = name

        functions.append(
            PACKAGE_TASK_TEMPLATE.format(
                func_name=func_name,
                description=d["description"] or _default_description(name),
                package_name=name,
                resolved_version=d["version"],
            )
        )

    return TASKS_TEMPLATE.format(functions="\n".join(functions))


def _clean_registry_description(description: str) -> str:
    """Flatten whitespace and strip inline URLs from a registry description."""
    description = description.replace("\n", " ").strip()
    # Strip "Original benchmark:", "Adapter:", "Source:", "Website:" footers.
    description = re.sub(
        r"\s*(Original benchmark|Adapter details|Adapter|Source|Website)"
        r":\s*https?://\S+\.?\s*",
        " ",
        description,
    )
    # Eat any leading whitespace alongside the parens so "X (URL)." → "X."
    # rather than "X ."
    description = re.sub(r"\s*\(https?://\S+\)", "", description)
    description = re.sub(r"\s*https?://\S+", "", description)
    description = re.sub(r"\s{2,}", " ", description)
    result = description.strip().rstrip(" .")
    return (result + ".") if result else ""


def load_overrides() -> dict[str, dict[str, Any]]:
    """Load the hand-maintained per-dataset overrides from docs/overrides.yml.

    Returns a mapping of ``{dataset_name: {field: value, ...}}``.
    """
    if not OVERRIDES_FILE.exists():
        print(
            f"  ⚠ {OVERRIDES_FILE} not found. Listing will render "
            f"without category filters.",
            file=sys.stderr,
        )
        return {}
    try:
        data = yaml.safe_load(OVERRIDES_FILE.read_text()) or {}
    except yaml.YAMLError as exc:
        print(
            f"  ⚠ {OVERRIDES_FILE} failed to parse ({exc}). "
            f"Listing will render without category filters.",
            file=sys.stderr,
        )
        return {}
    if not isinstance(data, dict):
        print(
            f"  ⚠ {OVERRIDES_FILE} has unexpected shape (not a mapping). "
            f"Listing will render without category filters.",
            file=sys.stderr,
        )
        return {}
    return {name: fields for name, fields in data.items() if isinstance(fields, dict)}


def write_overrides_file(data: dict[str, dict[str, Any]]) -> None:
    """Rewrite docs/overrides.yml: preserve the header comment block, sort body.

    Every field on every entry is written back verbatim — ``categories``,
    ``function_name``, ``arxiv``, ``repo``, etc. The header (everything
    before the first non-comment line) is preserved; inline comments inside
    the body are not (the body is purely machine-managed key/value content).
    """
    if not OVERRIDES_FILE.exists():
        print(
            f"  ⚠ Cannot write overrides: {OVERRIDES_FILE} does not exist.",
            file=sys.stderr,
        )
        return
    lines = OVERRIDES_FILE.read_text().splitlines(keepends=True)
    body_start = next(
        (
            i
            for i, line in enumerate(lines)
            if line and not line.startswith("#") and not line.isspace()
        ),
        len(lines),
    )
    header = "".join(lines[:body_start])

    chunks: list[str] = []
    for key, value in sorted(data.items()):
        chunk = yaml.safe_dump(
            {key: value},
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=10000,
        )
        chunks.append(chunk)
    OVERRIDES_FILE.write_text(header + "\n".join(chunks))


def resolve_categories(
    registry: list[Dataset], overrides: dict[str, dict[str, Any]]
) -> tuple[dict[str, list[str]], list[str]]:
    """Build the dataset→categories map; reconcile overrides.yml with the registry.

    Symmetric reconciliation on every run:

    * **Missing** entries (registered slug, no override) get an empty
      ``categories: []`` stub. ``validate_overrides.py`` blocks merging
      until a human fills it in.
    * **Orphan** entries (override key, no longer-registered slug) are
      dropped (e.g. dataset removed from the website, or newly added to
      ``docs/exclude.yml``).

    The file is rewritten only if anything changed.
    """
    categories_map: dict[str, list[str]] = {}
    registry_names: set[str] = set()

    for entry in registry:
        name = entry.get("name")
        if not name or name in registry_names:
            continue
        registry_names.add(name)
        cats = (overrides.get(name) or {}).get("categories")
        if isinstance(cats, list) and all(isinstance(c, str) for c in cats):
            categories_map[name] = list(cats)

    missing = sorted(registry_names - set(overrides))
    orphans = sorted(set(overrides) - registry_names)

    if missing:
        print(
            f"\n⚠ {len(missing)} registry dataset(s) have no override entry "
            "in docs/overrides.yml and were auto-stubbed:",
            file=sys.stderr,
        )
        for n in missing:
            print(f"  - {n}", file=sys.stderr)
        print(
            "\n  Fill in `categories:` for each before merging. "
            "scripts/validate_overrides.py will block merges on empty stubs.",
            file=sys.stderr,
        )

    if orphans:
        print(
            f"\n⚠ {len(orphans)} override entry/entries no longer match a "
            "registered dataset and were dropped:",
            file=sys.stderr,
        )
        for n in orphans:
            print(f"  - {n}", file=sys.stderr)

    if missing or orphans:
        orphan_set = set(orphans)
        new_data = {k: v for k, v in overrides.items() if k not in orphan_set}
        for n in missing:
            new_data[n] = {"categories": []}
        write_overrides_file(new_data)

    return categories_map, missing


def generate_registry_yml_content(
    registry: list[Dataset],
    categories_map: dict[str, list[str]],
) -> str:
    """Build docs/registry-listing.yml — the data source for the Quarto listing.

    One entry per dataset. Title is the ``org/name`` slug; ``version`` is
    the live ``latest`` tag (Harbor packages are content-addressed under it).
    """
    entries: list[dict[str, Any]] = []

    for d in registry:
        desc = d["clean_description"]
        if len(desc) > LISTING_DESC_MAX:
            desc_trunc = desc[: LISTING_DESC_MAX - 1].rstrip(" .") + "…"
        else:
            desc_trunc = desc
        entry: dict[str, Any] = {
            "title": d["name"],
            "path": f"registry/{d['func_name']}.html",
            "desc": desc,
            "desc_trunc": desc_trunc,
            "task_function": d["func_name"],
            "samples": d["samples"],
            "version": "latest",
        }
        cats = categories_map.get(d["name"])
        if cats:
            entry["categories"] = cats
        entries.append(entry)

    body = yaml.safe_dump(
        entries,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=10000,
    )
    return REGISTRY_YML_HEADER + "\n" + body


def _build_table_rows(dataset: Dataset, override: dict[str, Any]) -> str:
    """Render the Markdown rows for a per-dataset details table."""
    rows: list[str] = [
        f"| Harbor registry | [{dataset['name']}]({dataset['harbor_url']}) |",
        f"| Inspect task    | `{dataset['func_name']}` |",
        f"| Latest digest   | {dataset['version']} |",
        f"| Samples         | {dataset['samples']} |",
    ]

    arxiv = override.get("arxiv")
    repo = override.get("repo")
    if isinstance(arxiv, str) and arxiv:
        rows.append(f"| Paper           | [arxiv]({arxiv}) |")
    if isinstance(repo, str) and repo:
        rows.append(f"| Source          | [{repo}]({repo}) |")
    return "\n".join(rows)


def _render_page(
    dataset: Dataset,
    categories: list[str],
    override: dict[str, Any],
) -> str:
    """Render the .qmd body for a single per-dataset landing page."""
    # Render frontmatter categories as a YAML block list. Empty string
    # (not ``categories: []``) when no categories, so the frontmatter
    # doesn't carry an empty key.
    categories_block = (
        "categories:\n" + "\n".join(f"  - {c}" for c in categories) + "\n"
        if categories
        else ""
    )
    return PAGE_TEMPLATE.format(
        title=dataset["name"],
        description=dataset["clean_description"],
        categories_block=categories_block,
        func_name=dataset["func_name"],
        table_rows=_build_table_rows(dataset, override),
    )


def generate_registry_pages(
    registry: list[Dataset],
    overrides: dict[str, dict[str, Any]],
    categories_map: dict[str, list[str]],
) -> int:
    """Write per-dataset landing pages under docs/registry/.

    One ``.qmd`` per dataset. Orphan pages (for datasets no
    longer present in the registry) are deleted.
    """
    REGISTRY_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    expected_files: set[Path] = set()
    written = 0

    for d in registry:
        content = _render_page(
            dataset=d,
            categories=categories_map.get(d["name"], []),
            override=overrides.get(d["name"], {}),
        )

        page_path = REGISTRY_PAGES_DIR / f"{d['func_name']}.qmd"
        expected_files.add(page_path)
        if _write_if_changed(page_path, content):
            written += 1

    # Delete any .qmd that shouldn't be there (dataset removed or renamed).
    for stale in REGISTRY_PAGES_DIR.glob("*.qmd"):
        if stale not in expected_files:
            stale.unlink()

    return written


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate inspect_harbor task bindings and docs artifacts "
        "from the Harbor registry.",
    )
    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Skip regenerating src/inspect_harbor/_tasks.py and only emit "
        "the docs artifacts (registry-listing.yml + registry/*.qmd, plus "
        "auto-stubs into overrides.yml). Used by Quarto's pre-render so "
        "local docs builds don't churn _tasks.py.",
    )
    args = parser.parse_args()

    print("Harbor Registry Task Generator")
    print("=" * 50)

    # Discover datasets via website scrape, then fetch metadata for each.
    slugs = scrape_hub_slugs()
    slugs = filter_excluded(slugs, load_exclude_patterns())
    fetched = fetch_package_datasets(slugs)

    # Load overrides — decoration honors ``function_name`` overrides.
    print(f"\nLoading overrides from {OVERRIDES_FILE}...")
    overrides = load_overrides()

    registry = decorate_datasets(fetched, overrides)

    if not args.docs_only:
        print("\nGenerating _tasks.py...")
        tasks_content = generate_tasks_content(registry)
        changed = _write_if_changed(TASKS_FILE, tasks_content)
        print(f"{'✓ Wrote' if changed else '= Unchanged'}: {TASKS_FILE}")
        print(f"  Size: {len(tasks_content)} bytes")
        print(f"  Functions: {tasks_content.count('@task\n')}")
    else:
        print("\nSkipping _tasks.py regeneration (--docs-only).")

    # Auto-stub any new dataset names. The nightly PR carries the stubs and
    # CI (scripts/validate_overrides.py) blocks merging until a human fills
    # ``categories:`` in.
    categories_map, newly_stubbed = resolve_categories(registry, overrides)
    print(f"  Loaded categories for {len(categories_map)} dataset(s)")
    if newly_stubbed:
        print(f"  Auto-stubbed {len(newly_stubbed)} new dataset(s) in {OVERRIDES_FILE}")

    print("\nGenerating docs/registry-listing.yml...")
    registry_yml_content = generate_registry_yml_content(registry, categories_map)
    changed = _write_if_changed(REGISTRY_YML_FILE, registry_yml_content)
    print(f"{'✓ Wrote' if changed else '= Unchanged'}: {REGISTRY_YML_FILE}")
    print(f"  Size: {len(registry_yml_content)} bytes")

    print(f"\nGenerating per-benchmark pages in {REGISTRY_PAGES_DIR}...")
    pages_written = generate_registry_pages(registry, overrides, categories_map)
    if pages_written:
        print(f"✓ Wrote {pages_written} page(s) (others unchanged)")
    else:
        print("= All pages unchanged")


if __name__ == "__main__":
    main()
