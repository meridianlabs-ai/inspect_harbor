#!/usr/bin/env python3
"""Load one task from every hub dataset so the parity test has something to compare.

Used by the ``harbor-parity`` workflow before ``tests/manual/test_harbor_parity.py``.
Loading exercises the hub queries, the task-version RPC and the archive
download for every dataset in ``docs/registry-listing.yml``, and collects the
warnings the adapter logs (unknown task.toml keys, degraded fidelity). The
summary goes to stdout and, in GitHub Actions, to the step summary.

Exit status is non-zero when no dataset loaded, or when any dataset fails to
load for a reason other than inspect_harbor refusing it by design (multi-step,
Windows and prior-context tasks raise ``NotImplementedError``).
"""

import logging
import os
import sys
import time
from collections import Counter
from pathlib import Path

import yaml
from inspect_harbor._harbor.cache import cache_root
from inspect_harbor._harbor.task import load_harbor_tasks

LISTING = Path(__file__).parent.parent / "docs" / "registry-listing.yml"
ADAPTER_LOGGER = "inspect_harbor._harbor"


def registry_slugs(listing: Path = LISTING) -> list[str]:
    """``org/name`` slugs from the generated registry listing."""
    return [entry["title"] for entry in yaml.safe_load(listing.read_text()) or []]


class _Collector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: Counter[str] = Counter()

    def emit(self, record: logging.LogRecord) -> None:
        self.messages[record.getMessage()] += 1


def main(listing: Path = LISTING) -> int:
    """Warm the cache and report; return the process exit status."""
    collector = _Collector()
    logging.getLogger(ADAPTER_LOGGER).addHandler(collector)
    slugs = registry_slugs(listing)
    loaded, unsupported, failed = 0, [], []
    t0 = time.monotonic()
    for slug in slugs:
        try:
            load_harbor_tasks(package_name=slug, n_tasks=1)
            loaded += 1
        except NotImplementedError as exc:
            unsupported.append(f"{slug}: {str(exc).splitlines()[0]}")
        except Exception as exc:  # noqa: BLE001 - reported below, then fail
            failed.append(f"{slug}: {type(exc).__name__}: {str(exc)[:500]}")

    # Task dirs are content-addressed, so datasets sharing a first task share
    # a dir; this is the number of comparisons the parity test will make.
    task_dirs = sum(1 for p in (cache_root() / "hub").glob("*/*/*/task.toml"))
    lines = [
        f"## Harbor parity cache warm-up ({time.monotonic() - t0:.0f}s)",
        "",
        f"- datasets: {len(slugs)}, loaded: {loaded}, unsupported by design: "
        f"{len(unsupported)}, failed: {len(failed)}",
        f"- distinct task dirs in cache: {task_dirs}",
    ]
    if failed:
        lines += ["", "### Failed to load", ""] + [f"- {f}" for f in failed]
    if unsupported:
        lines += ["", "### Unsupported by design", ""] + [f"- {u}" for u in unsupported]
    if collector.messages:
        lines += ["", "### Adapter warnings", ""]
        lines += [f"- {n}x {m}" for m, n in collector.messages.most_common()]
    report = "\n".join(lines)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a") as fh:
            fh.write(report + "\n")
    return 1 if failed or not loaded else 0


if __name__ == "__main__":
    sys.exit(main())
