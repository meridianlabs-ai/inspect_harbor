"""ATIF file discovery and reading utilities.

ATIF (Agent Trajectory Interchange Format, defined in Harbor RFC 0001)
is a JSON-based format for the complete interaction history of an
autonomous LLM agent. Harbor's installed agents (claude_code, codex,
goose, opencode, openhands, gemini_cli, mini_swe_agent, swe_agent,
terminus_2) emit one `trajectory.json` per run.
"""

from datetime import datetime
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import Iterator

logger = getLogger(__name__)

# ATIF source type constant
ATIF_SOURCE_TYPE = "atif"


def discover_trajectory_files(
    path: str | PathLike[str] | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
) -> Iterator[Path]:
    """Discover ATIF trajectory files.

    Args:
        path: Path to search. Can be:
            - None: no files are discovered (no default location)
            - A directory (searched recursively)
            - A specific trajectory.json file
        from_time: Only yield files modified on or after this time
        to_time: Only yield files modified before this time

    Yields:
        Trajectory file paths, sorted by modification time (newest first)
    """
    if path is None:
        return

    search_path = Path(path).expanduser()

    if not search_path.exists():
        logger.warning("Path does not exist: %s", search_path)
        return

    if search_path.is_file():
        trajectory_files = [search_path]
    else:
        trajectory_files = list(search_path.rglob("*.json"))

    filtered: list[tuple[Path, float]] = []
    for f in trajectory_files:
        try:
            mtime = f.stat().st_mtime
        except OSError as e:
            logger.warning("stat failed for %s: %s", f, e)
            continue

        if from_time is not None and mtime < from_time.timestamp():
            continue
        if to_time is not None and mtime >= to_time.timestamp():
            continue

        filtered.append((f, mtime))

    filtered.sort(key=lambda x: x[1], reverse=True)

    for f, _ in filtered:
        yield f
