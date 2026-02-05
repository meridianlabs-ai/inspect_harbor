"""Tests for Harbor solver."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from inspect_ai.model import ModelName
from inspect_ai.solver import TaskState
from inspect_harbor._sandbox_utils import cleanup_sandbox_directories, copy_directory_to_sandbox
from inspect_harbor._solver import oracle


@pytest.mark.asyncio
async def test_oracle_executes_solution_script():
    """Test that oracle solver executes the solve.sh script and cleans up."""
    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/fake/solution",
            "solve_path": "/fake/solution/solve.sh",
        },
    )

    mock_sandbox = Mock()
    exec_calls: list[list[str]] = []

    async def track_exec(cmd: list[str], **_kwargs: object) -> Mock:
        exec_calls.append(cmd)
        return Mock(returncode=0, stdout="", stderr="")

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)
    mock_sandbox.write_file = AsyncMock()

    with (
        patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.copy_directory_to_sandbox", new_callable=AsyncMock) as mock_copy,
    ):
        solver_fn = oracle()
        result_state = await solver_fn(state, Mock())

        mock_copy.assert_called_once_with("/fake/solution", "/solution")

        # Should have: [solution script execution, rm /solution]
        assert len(exec_calls) == 2
        assert exec_calls[0] == ["bash", "-l", "/solution/solve.sh"]
        assert exec_calls[1] == ["rm", "-rf", "/solution"]

        assert result_state == state


@pytest.mark.asyncio
async def test_oracle_with_environment_variables():
    """Test that oracle passes environment variables to the solution."""
    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/fake/solution",
            "solve_path": "/fake/solution/solve.sh",
            "harbor_config": {
                "agent": {"timeout_sec": 300},
                "solution": {"env": {"API_KEY": "test123", "DEBUG": "true"}},
            },
        },
    )

    mock_sandbox = Mock()
    mock_sandbox.exec = AsyncMock(return_value=Mock(returncode=0, stdout="", stderr=""))

    with (
        patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.copy_directory_to_sandbox", new_callable=AsyncMock),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())

        # Check the first call (solution script execution, not cleanup)
        calls = mock_sandbox.exec.call_args_list
        assert len(calls) == 2  # Solution execution + cleanup
        first_call_args = calls[0]
        assert first_call_args[1]["env"] == {"API_KEY": "test123", "DEBUG": "true"}


@pytest.mark.asyncio
async def test_oracle_with_nonzero_exit_code():
    """Test that oracle handles non-zero exit codes gracefully."""
    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/fake/solution",
            "solve_path": "/fake/solution/solve.sh",
        },
    )

    mock_sandbox = Mock()
    mock_sandbox.exec = AsyncMock(
        return_value=Mock(returncode=1, stdout="error output", stderr="error details")
    )

    with (
        patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.copy_directory_to_sandbox", new_callable=AsyncMock),
    ):
        solver_fn = oracle()
        result_state = await solver_fn(state, Mock())

        assert result_state == state


@pytest.mark.asyncio
async def test_oracle_with_relative_solve_path():
    """Test that oracle correctly handles relative solve paths."""
    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/fake/solution",
            "solve_path": "/fake/solution/scripts/solve.sh",
            "harbor_config": {"agent": {"timeout_sec": 300}},
        },
    )

    mock_sandbox = Mock()
    exec_calls: list[list[str]] = []

    async def track_exec(cmd: list[str], **_kwargs: object) -> Mock:
        exec_calls.append(cmd)
        return Mock(returncode=0, stdout="", stderr="")

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)

    with (
        patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.copy_directory_to_sandbox", new_callable=AsyncMock),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())

        # First call should be to execute the solution script
        assert exec_calls[0] == ["bash", "-l", "/solution/scripts/solve.sh"]
        # Second call should be cleanup
        assert exec_calls[1] == ["rm", "-rf", "/solution"]


@pytest.mark.asyncio
async def test_copy_directory_to_sandbox():
    """Test helper function that copies directory to sandbox."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("content2")

        mock_sandbox = Mock()
        mock_sandbox.write_file = AsyncMock()

        with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
            await copy_directory_to_sandbox(str(tmp_path), "/test")

            assert mock_sandbox.write_file.call_count == 2
            calls = [call[0] for call in mock_sandbox.write_file.call_args_list]
            paths_and_contents = {call[0]: call[1] for call in calls}

            # All files copied as bytes
            assert "/test/file1.txt" in paths_and_contents
            assert paths_and_contents["/test/file1.txt"] == b"content1"
            assert isinstance(paths_and_contents["/test/file1.txt"], bytes)

            assert "/test/subdir/file2.txt" in paths_and_contents
            assert paths_and_contents["/test/subdir/file2.txt"] == b"content2"
            assert isinstance(paths_and_contents["/test/subdir/file2.txt"], bytes)


@pytest.mark.asyncio
async def test_copy_directory_with_binary_files_to_sandbox():
    """Test copying directory with text and binary files to sandbox."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create text and binary files
        script_content = b"#!/bin/bash\necho test"
        (tmp_path / "script.sh").write_bytes(script_content)
        binary_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
        (tmp_path / "data.bin").write_bytes(binary_data)

        mock_sandbox = Mock()
        mock_sandbox.write_file = AsyncMock()

        with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
            await copy_directory_to_sandbox(str(tmp_path), "/solution")

            assert mock_sandbox.write_file.call_count == 2
            calls = [call[0] for call in mock_sandbox.write_file.call_args_list]
            paths_and_contents = {call[0]: call[1] for call in calls}

            # All files copied as bytes
            assert "/solution/script.sh" in paths_and_contents
            assert paths_and_contents["/solution/script.sh"] == script_content
            assert isinstance(paths_and_contents["/solution/script.sh"], bytes)

            assert "/solution/data.bin" in paths_and_contents
            assert paths_and_contents["/solution/data.bin"] == binary_data
            assert isinstance(paths_and_contents["/solution/data.bin"], bytes)
