"""Tests for Harbor solver."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from inspect_ai.model import ModelName
from inspect_ai.solver import TaskState
from inspect_harbor._sandbox_utils import copy_directory_to_sandbox
from inspect_harbor._solver import oracle


@pytest.mark.asyncio
async def test_oracle_executes_solution_script():
    """Test that oracle solver executes the solve.sh script."""
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
    mock_sandbox.exec = AsyncMock(return_value=Mock(returncode=0, stdout="", stderr=""))
    mock_sandbox.write_file = AsyncMock()

    with (
        patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.copy_directory_to_sandbox", new_callable=AsyncMock) as mock_copy,
    ):
        solver_fn = oracle()
        result_state = await solver_fn(state, Mock())

        mock_copy.assert_called_once_with("/fake/solution", "/solution")

        mock_sandbox.exec.assert_called_once()
        call_args = mock_sandbox.exec.call_args
        assert call_args[0][0] == ["bash", "/solution/solve.sh"]

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

        call_args = mock_sandbox.exec.call_args
        assert call_args[1]["env"] == {"API_KEY": "test123", "DEBUG": "true"}


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
    mock_sandbox.exec = AsyncMock(return_value=Mock(returncode=0, stdout="", stderr=""))

    with (
        patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.sandbox", return_value=mock_sandbox),
        patch("inspect_harbor._solver.copy_directory_to_sandbox", new_callable=AsyncMock),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())

        call_args = mock_sandbox.exec.call_args
        assert call_args[0][0] == ["bash", "/solution/scripts/solve.sh"]


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
            assert "/test/file1.txt" in paths_and_contents
            assert paths_and_contents["/test/file1.txt"] == "content1"
            assert "/test/subdir/file2.txt" in paths_and_contents
            assert paths_and_contents["/test/subdir/file2.txt"] == "content2"
