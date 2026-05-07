"""End-to-end smoke tests against the live Harbor registry.

Excluded by default via ``--ignore=tests/manual`` in ``pyproject.toml``.
Opt in by naming the directory explicitly::

    uv run pytest tests/manual                  # everything
    uv run pytest tests/manual -k url           # URL checks only
    uv run pytest tests/manual -k task          # task instantiation only

Two test groups:

* ``test_task_runs_with_one_sample`` — for every ``@task`` in
  ``inspect_harbor._tasks``, build a 1-sample Task against live Harbor.

* ``test_harbor_url_resolves`` — re-runs the scrape + decoration
  pipeline against live Harbor and HEAD-checks each ``harbor_url``.
"""

import http.client
import inspect
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import pytest

# Make scripts/ importable so we can reuse the URL pipeline.
_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from generate_tasks import (  # noqa: E402
    decorate_datasets,
    fetch_package_datasets,
    scrape_hub_slugs,
)
from inspect_harbor import _tasks  # noqa: E402

pytestmark = pytest.mark.slow


def _all_generated_tasks() -> list[tuple[str, Callable[..., Any]]]:
    """Return ``[(name, fn), …]`` for every @task defined in ``_tasks``.

    Filters by ``__module__`` so we don't pick up ``task`` /
    ``Task`` re-exported from ``inspect_ai`` at the top of the file.
    """
    return sorted(
        (name, fn)
        for name, fn in inspect.getmembers(_tasks, inspect.isfunction)
        if not name.startswith("_")
        and getattr(fn, "__module__", "") == "inspect_harbor._tasks"
    )


def _all_canonical_urls() -> list[tuple[str, str]]:
    """Re-run the URL pipeline against live Harbor; return ``[(name, url), …]``.

    URLs are deterministic from scraped ``(org, name)`` slugs, so every
    one is canonical by construction.
    """
    slugs = scrape_hub_slugs()
    fetched = fetch_package_datasets(slugs)
    decorated = decorate_datasets(fetched, {})
    return [(d["name"], d["harbor_url"]) for d in decorated]


_TASK_FUNCS = _all_generated_tasks()
_CANONICAL_URLS = _all_canonical_urls()


@pytest.mark.parametrize("name,task_fn", _TASK_FUNCS, ids=[n for n, _ in _TASK_FUNCS])
def test_task_runs_with_one_sample(name: str, task_fn: Callable[..., Any]) -> None:
    """Build a 1-sample Task against the live registry."""
    try:
        task = task_fn(n_tasks=1)
    except NotImplementedError as e:
        # Multi-step tasks intentionally raise — out of scope for this PR.
        pytest.skip(f"multi-step task: {e}")
    assert task.dataset is not None, f"{name}: task returned no dataset"
    assert len(task.dataset) >= 1, f"{name}: dataset is empty"


@pytest.mark.parametrize(
    "name,url", _CANONICAL_URLS, ids=[n for n, _ in _CANONICAL_URLS]
)
def test_harbor_url_resolves(name: str, url: str) -> None:
    """The Harbor URL linked from the dataset's per-benchmark page resolves (HTTP < 400)."""
    parsed = urlparse(url)
    conn = http.client.HTTPSConnection(parsed.netloc, timeout=10)
    try:
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"
        conn.request("HEAD", path, headers={"User-Agent": "inspect-harbor-tests/1.0"})
        resp = conn.getresponse()
    finally:
        conn.close()
    assert resp.status < 400, f"{name}: {url} returned HTTP {resp.status}"
