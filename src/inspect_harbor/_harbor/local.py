"""Local dataset directories and task filtering."""

import logging
from collections.abc import Callable
from fnmatch import fnmatch
from pathlib import Path
from typing import TypeVar

from inspect_harbor._harbor.task_dir import HarborTask

logger = logging.getLogger(__name__)

T = TypeVar("T")


def filter_entries(
    entries: list[T],
    name: Callable[[T], str],
    include: list[str] | None,
    exclude: list[str] | None,
    n_tasks: int | None,
) -> list[T]:
    """Apply Harbor's dataset filters to task entries, preserving order.

    ``include`` and ``exclude`` are glob patterns matched with ``fnmatch``
    against ``name(entry)``; ``n_tasks`` truncates the result after
    filtering. Entries are filtered individually, so duplicate names are
    kept or dropped one by one exactly as Harbor does.

    Raises:
        ValueError: When ``include`` is given and matches no task.
    """
    filtered = entries
    if include:
        filtered = [e for e in filtered if any(fnmatch(name(e), p) for p in include)]
        if not filtered:
            available = sorted(name(e) for e in entries)
            raise ValueError(
                f"No tasks matched the filter(s) {include}. There are "
                f"{len(available)} tasks available in this dataset. "
                f"Example task names: {available[:5]}"
            )
    if exclude:
        filtered = [
            e for e in filtered if not any(fnmatch(name(e), p) for p in exclude)
        ]
    if n_tasks is not None:
        filtered = filtered[:n_tasks]
    return filtered


def filter_task_names(
    names: list[str],
    include: list[str] | None,
    exclude: list[str] | None,
    n_tasks: int | None,
) -> list[str]:
    """``filter_entries`` over plain names."""
    return filter_entries(names, lambda n: n, include, exclude, n_tasks)


def list_local_dataset_tasks(
    dataset_dir: Path,
    include: list[str] | None,
    exclude: list[str] | None,
    n_tasks: int | None,
    disable_verification: bool,
) -> list[Path]:
    """Return the task directories inside a local dataset directory.

    Children that are not valid task directories are skipped, as Harbor
    does; a child that has a ``task.toml`` but fails to load is reported so
    a typo does not silently shrink the dataset.
    """
    candidates: list[Path] = []
    for child in sorted(dataset_dir.iterdir()):
        if not child.is_dir():
            continue
        if HarborTask.is_valid_dir(child, disable_verification=disable_verification):
            candidates.append(child)
        elif (child / "task.toml").exists():
            logger.warning("Skipping %s: not a valid Harbor task directory", child)
    return filter_entries(candidates, lambda p: p.name, include, exclude, n_tasks)
