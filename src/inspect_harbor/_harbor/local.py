"""Local dataset directories and task-name filtering."""

from fnmatch import fnmatch
from pathlib import Path

from inspect_harbor._harbor.task_dir import HarborTask


def filter_task_names(
    names: list[str],
    include: list[str] | None,
    exclude: list[str] | None,
    n_tasks: int | None,
) -> list[str]:
    """Apply Harbor's dataset filters to a list of task names, preserving order.

    ``include`` and ``exclude`` are glob patterns matched with ``fnmatch``;
    ``n_tasks`` truncates the result after filtering.

    Raises:
        ValueError: When ``include`` is given and matches no task.
    """
    filtered = names
    if include:
        filtered = [n for n in filtered if any(fnmatch(n, p) for p in include)]
        if not filtered:
            available = sorted(names)
            raise ValueError(
                f"No tasks matched the filter(s) {include}. There are "
                f"{len(available)} tasks available in this dataset. "
                f"Example task names: {available[:5]}"
            )
    if exclude:
        filtered = [n for n in filtered if not any(fnmatch(n, p) for p in exclude)]
    if n_tasks is not None:
        filtered = filtered[:n_tasks]
    return filtered


def list_local_dataset_tasks(
    dataset_dir: Path,
    include: list[str] | None,
    exclude: list[str] | None,
    n_tasks: int | None,
    disable_verification: bool,
) -> list[Path]:
    """Return the task directories inside a local dataset directory.

    Children that are not valid task directories are skipped; the rest are
    filtered by directory name with ``filter_task_names``.
    """
    candidates = {
        child.name: child
        for child in sorted(dataset_dir.iterdir())
        if child.is_dir()
        and HarborTask.is_valid_dir(child, disable_verification=disable_verification)
    }
    keep = filter_task_names(list(candidates), include, exclude, n_tasks)
    return [candidates[name] for name in keep]
