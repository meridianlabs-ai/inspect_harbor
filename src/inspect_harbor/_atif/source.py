"""ATIF source: async generator yielding Scout `Transcript`s."""

from datetime import datetime
from logging import getLogger
from os import PathLike
from typing import AsyncIterator

from harbor.models.trajectories import Trajectory
from inspect_scout import Transcript
from pydantic import ValidationError

from inspect_harbor._atif.convert import trajectory_to_transcript
from inspect_harbor._atif.discovery import discover_trajectory_files

logger = getLogger(__name__)


async def atif(
    path: str | PathLike[str] | None = None,
    session_id: str | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    limit: int | None = None,
) -> AsyncIterator[Transcript]:
    """Read transcripts from ATIF JSON files.

    ATIF (Agent Trajectory Interchange Format, defined in Harbor RFC 0001)
    is a JSON-based format for the complete interaction history of an
    autonomous LLM agent. Harbor's installed agents (claude_code, codex,
    goose, opencode, openhands, gemini_cli, mini_swe_agent, swe_agent,
    terminus_2) emit one `trajectory.json` per run.

    Args:
        path: Directory containing trajectory.json files, or a path to a
            specific trajectory file.
        session_id: Filter to trajectories with this `session_id`.
        from_time: Only files modified on or after this time.
        to_time: Only files modified strictly before this time.
        limit: Max transcripts to yield.

    Yields:
        Scout Transcript objects ready for insertion into a transcript
        database.
    """
    count = 0

    for trajectory_path in discover_trajectory_files(
        path=path, from_time=from_time, to_time=to_time
    ):
        if limit is not None and count >= limit:
            return

        try:
            content = trajectory_path.read_text()
            trajectory = Trajectory.model_validate_json(content)
        except (OSError, ValidationError) as e:
            logger.warning(
                "Skipping non-ATIF or unreadable file %s: %s",
                trajectory_path,
                e,
            )
            continue

        if session_id is not None and trajectory.session_id != session_id:
            continue

        yield trajectory_to_transcript(
            trajectory,
            source_uri=str(trajectory_path),
        )
        count += 1
