"""Tests for the `atif()` async-generator source function.

Exercises file walking, format detection (Pydantic validation), and the
filter parameters (`session_id`, `from_time`, `to_time`, `limit`).
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterator

import pytest
from inspect_harbor import atif
from inspect_scout import Transcript

FIXTURES = Path(__file__).parent / "fixtures"


async def _collect(gen: AsyncIterator[Transcript]) -> list[Transcript]:
    return [t async for t in gen]


@pytest.mark.asyncio
async def test_yields_transcripts_from_fixtures_dir() -> None:
    """The two valid v1.5/v1.6 fixtures yield; v1.7 fixtures are skipped."""
    transcripts = await _collect(atif(path=str(FIXTURES)))
    # Two valid v1.5/v1.6 fixtures yield; the two v1.7 fixtures are skipped.
    assert len(transcripts) == 2
    assert all(t.source_type == "atif" for t in transcripts)


@pytest.mark.asyncio
async def test_yields_from_single_file_path() -> None:
    """`path` accepts a path to a single trajectory file, not just a directory."""
    fixture = FIXTURES / "openhands_hello-world.trajectory.json"
    transcripts = await _collect(atif(path=str(fixture)))
    assert len(transcripts) == 1


@pytest.mark.asyncio
async def test_skips_non_atif_json(tmp_path: Path) -> None:
    """Random *.json files in the search path are skipped, not crashed."""
    (tmp_path / "not_atif.json").write_text(json.dumps({"foo": "bar"}))
    transcripts = await _collect(atif(path=str(tmp_path)))
    assert transcripts == []


@pytest.mark.asyncio
async def test_session_id_filter(tmp_path: Path) -> None:
    """`session_id` filters by the trajectory's session_id field."""
    src = (FIXTURES / "openhands_hello-world.trajectory.json").read_text()
    target = json.loads(src)
    target["session_id"] = "wanted"
    other = json.loads(src)
    other["session_id"] = "skipped"
    (tmp_path / "a.json").write_text(json.dumps(target))
    (tmp_path / "b.json").write_text(json.dumps(other))

    transcripts = await _collect(atif(path=str(tmp_path), session_id="wanted"))
    assert len(transcripts) == 1
    assert transcripts[0].transcript_id == "wanted"


@pytest.mark.asyncio
async def test_limit_truncates_yield(tmp_path: Path) -> None:
    """`limit` stops yielding after N transcripts."""
    src = (FIXTURES / "openhands_hello-world.trajectory.json").read_text()
    for i in range(3):
        d = json.loads(src)
        d["session_id"] = f"s{i}"
        (tmp_path / f"t{i}.json").write_text(json.dumps(d))

    transcripts = await _collect(atif(path=str(tmp_path), limit=2))
    assert len(transcripts) == 2


@pytest.mark.asyncio
async def test_from_time_filters_by_mtime(tmp_path: Path) -> None:
    """`from_time` skips files whose mtime is older."""
    src = (FIXTURES / "openhands_hello-world.trajectory.json").read_text()
    new_file = tmp_path / "new.json"
    old_file = tmp_path / "old.json"

    d_new = json.loads(src)
    d_new["session_id"] = "new"
    new_file.write_text(json.dumps(d_new))

    d_old = json.loads(src)
    d_old["session_id"] = "old"
    old_file.write_text(json.dumps(d_old))

    # Backdate the "old" file's mtime by an hour.
    old_ts = (datetime.now() - timedelta(hours=1)).timestamp()
    os.utime(old_file, (old_ts, old_ts))

    cutoff = datetime.now() - timedelta(minutes=30)
    transcripts = await _collect(atif(path=str(tmp_path), from_time=cutoff))

    assert len(transcripts) == 1
    assert transcripts[0].transcript_id == "new"


@pytest.mark.asyncio
async def test_no_path_yields_nothing() -> None:
    """`atif()` with no path yields zero transcripts (no implicit default)."""
    transcripts = await _collect(atif())
    assert transcripts == []


@pytest.mark.asyncio
async def test_nonexistent_path_yields_nothing() -> None:
    """A path that doesn't exist yields zero transcripts (logged, not raised)."""
    transcripts = await _collect(atif(path="/nonexistent/path/to/nowhere"))
    assert transcripts == []
