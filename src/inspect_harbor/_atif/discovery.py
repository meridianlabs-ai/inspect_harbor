"""File discovery for ATIF trajectory.json files."""

from datetime import datetime
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import Iterator

logger = getLogger(__name__)


def discover_trajectory_files(
    path: str | PathLike[str] | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
) -> Iterator[Path]:
    """Yield candidate ATIF trajectory.json files under `path`.

    Filters by file modification time (mtime) when from_time / to_time are
    given; the cheaper pre-filter avoids parsing files we'll discard. The
    caller is expected to validate via Pydantic and reject files whose
    contents are not valid ATIF.

    Args:
        path: Directory to search recursively, or a single file path.
            If None, no files are discovered.
        from_time: Only files modified on or after this time.
        to_time: Only files modified strictly before this time.

    Yields:
        Path objects for candidate trajectory files, sorted by mtime
        (newest first) so callers can stop early via `limit`.
    """
    if path is None:
        return

    p = Path(path).expanduser()

    if not p.exists():
        logger.warning("ATIF discovery: path does not exist: %s", p)
        return

    if p.is_file():
        candidates = [p]
    else:
        candidates = list(p.rglob("*.json"))

    filtered: list[tuple[Path, float]] = []
    for f in candidates:
        try:
            mtime = f.stat().st_mtime
        except OSError as e:
            logger.warning("ATIF discovery: stat failed for %s: %s", f, e)
            continue

        if from_time is not None and mtime < from_time.timestamp():
            continue
        if to_time is not None and mtime >= to_time.timestamp():
            continue

        filtered.append((f, mtime))

    filtered.sort(key=lambda x: x[1], reverse=True)

    for f, _ in filtered:
        yield f
