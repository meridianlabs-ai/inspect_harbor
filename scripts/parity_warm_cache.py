#!/usr/bin/env python3
"""Load one task from every hub dataset so the parity test has something to compare.

Used by the ``harbor-parity`` workflow before ``tests/manual/test_harbor_parity.py``.
Loading exercises the hub queries, the task-version RPC and the archive
download for every dataset in ``docs/registry-listing.yml``, and collects the
task.toml drift notices the models log. The summary goes to stdout and, in
GitHub Actions, to the step summary.

Exit status is non-zero when any dataset fails to load for a reason other than
being multi-step (which inspect_harbor refuses by design).
"""

import logging
import os
import sys
import time
from collections import Counter
from pathlib import Path

import yaml
from inspect_harbor._harbor.task import load_harbor_tasks

LISTING = Path(__file__).parent.parent / "docs" / "registry-listing.yml"
DRIFT_LOGGER = "inspect_harbor._harbor.models"


def registry_slugs(listing: Path = LISTING) -> list[str]:
    """``org/name`` slugs from the generated registry listing."""
    return [entry["title"] for entry in yaml.safe_load(listing.read_text())]


class _Collector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: Counter[str] = Counter()

    def emit(self, record: logging.LogRecord) -> None:
        self.messages[record.getMessage()] += 1


def main() -> int:
    """Warm the cache and report; return the process exit status."""
    collector = _Collector()
    logging.getLogger(DRIFT_LOGGER).addHandler(collector)
    slugs = registry_slugs()
    loaded, unsupported, failed = 0, [], []
    t0 = time.monotonic()
    for slug in slugs:
        try:
            load_harbor_tasks(package_name=slug, n_tasks=1)
            loaded += 1
        except NotImplementedError:
            unsupported.append(slug)
        except Exception as exc:  # noqa: BLE001 - reported below, then fail
            failed.append(f"{slug}: {type(exc).__name__}: {str(exc)[:200]}")

    lines = [
        f"## Harbor parity cache warm-up ({time.monotonic() - t0:.0f}s)",
        "",
        f"- datasets: {len(slugs)}, loaded: {loaded}, unsupported (multi-step): "
        f"{len(unsupported)}, failed: {len(failed)}",
    ]
    if failed:
        lines += ["", "### Failed to load", ""] + [f"- {f}" for f in failed]
    if collector.messages:
        lines += ["", "### task.toml drift notices", ""]
        lines += [f"- {n}x {m}" for m, n in collector.messages.most_common()]
    report = "\n".join(lines)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).open("a").write(report + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
