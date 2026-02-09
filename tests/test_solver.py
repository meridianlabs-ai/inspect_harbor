"""Tests for Harbor solver."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from inspect_ai.model import ModelName
from inspect_ai.solver import TaskState
from inspect_harbor.harbor._sandbox_utils import (
    cleanup_sandbox_env_vars,
    copy_directory_to_sandbox,
)
from inspect_harbor.harbor._solver import oracle


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
    exec_calls: list[list[str]] = []

    async def track_exec(cmd: list[str], **_kwargs: object) -> Mock:
        exec_calls.append(cmd)
        return Mock(returncode=0, stdout="", stderr="")

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)
    mock_sandbox.write_file = AsyncMock()

    with (
        patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ),
        patch("inspect_harbor.harbor._solver.sandbox", return_value=mock_sandbox),
        patch(
            "inspect_harbor.harbor._solver.copy_directory_to_sandbox",
            new_callable=AsyncMock,
        ) as mock_copy,
        patch("pathlib.Path.exists", return_value=True),
    ):
        solver_fn = oracle()
        result_state = await solver_fn(state, Mock())

        mock_copy.assert_called_once_with(Path("/fake/solution"), "/solution")

        assert len(exec_calls) == 1
        assert exec_calls[0] == ["bash", "-l", "/solution/solve.sh"]

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
            "solution_env": {"API_KEY": "test123", "DEBUG": "true"},
        },
    )

    mock_sandbox = Mock()
    mock_sandbox.exec = AsyncMock(return_value=Mock(returncode=0, stdout="", stderr=""))

    with (
        patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ),
        patch("inspect_harbor.harbor._solver.sandbox", return_value=mock_sandbox),
        patch(
            "inspect_harbor.harbor._solver.copy_directory_to_sandbox",
            new_callable=AsyncMock,
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())

        # Check the calls (solution script execution + env cleanup)
        calls = mock_sandbox.exec.call_args_list
        assert len(calls) == 3  # Solution execution + 2 env cleanups

        # Check solution execution call
        first_call_args = calls[0]
        assert first_call_args[1]["env"] == {"API_KEY": "test123", "DEBUG": "true"}

        # Check cleanup was called for all env vars
        cleanup_calls = [call[0][0] for call in calls[1:]]
        assert ["unset", "API_KEY"] in cleanup_calls
        assert ["unset", "DEBUG"] in cleanup_calls


@pytest.mark.asyncio
async def test_oracle_resolves_env_var_templates(monkeypatch: pytest.MonkeyPatch):
    """Test that oracle resolves environment variable templates like ${VAR}."""
    # Set up test environment variable
    monkeypatch.setenv("TEST_SOLVER_API_KEY", "sk-test-oracle-456")

    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/fake/solution",
            "solve_path": "/fake/solution/solve.sh",
            "solution_env": {
                "OPENAI_API_KEY": "${TEST_SOLVER_API_KEY}",
                "MODEL_NAME": "gpt-4o",
                "DEBUG": "true",
            },
        },
    )

    mock_sandbox = Mock()
    mock_sandbox.exec = AsyncMock(return_value=Mock(returncode=0, stdout="", stderr=""))

    with (
        patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ),
        patch("inspect_harbor.harbor._solver.sandbox", return_value=mock_sandbox),
        patch(
            "inspect_harbor.harbor._solver.copy_directory_to_sandbox",
            new_callable=AsyncMock,
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())

        # Check the calls (solution script execution + env cleanup)
        calls = mock_sandbox.exec.call_args_list
        assert len(calls) == 4  # Solution execution + 3 env cleanups

        # Check solution execution call - verify template was resolved
        first_call_args = calls[0]
        assert (
            first_call_args[1]["env"]
            == {
                "OPENAI_API_KEY": "sk-test-oracle-456",  # Resolved from ${TEST_SOLVER_API_KEY}
                "MODEL_NAME": "gpt-4o",
                "DEBUG": "true",
            }
        )

        # Check cleanup was called for all env vars
        cleanup_calls = [call[0][0] for call in calls[1:]]
        assert ["unset", "OPENAI_API_KEY"] in cleanup_calls
        assert ["unset", "MODEL_NAME"] in cleanup_calls
        assert ["unset", "DEBUG"] in cleanup_calls


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
        patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ),
        patch("inspect_harbor.harbor._solver.sandbox", return_value=mock_sandbox),
        patch(
            "inspect_harbor.harbor._solver.copy_directory_to_sandbox",
            new_callable=AsyncMock,
        ),
        patch("pathlib.Path.exists", return_value=True),
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
        patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ),
        patch("inspect_harbor.harbor._solver.sandbox", return_value=mock_sandbox),
        patch(
            "inspect_harbor.harbor._solver.copy_directory_to_sandbox",
            new_callable=AsyncMock,
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())

        assert len(exec_calls) == 1
        assert exec_calls[0] == ["bash", "-l", "/solution/scripts/solve.sh"]


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

        with patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ):
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

        with patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ):
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


@pytest.mark.asyncio
async def test_oracle_missing_solution_dir_metadata():
    """Test oracle raises error when solution_dir metadata is missing."""
    from inspect_harbor.harbor._solver import CopySolutionDirError, oracle

    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={},  # Missing solution_dir
    )

    solver_fn = oracle()

    with pytest.raises(
        CopySolutionDirError, match="solution_dir not found in metadata"
    ):
        await solver_fn(state, Mock())


@pytest.mark.asyncio
async def test_oracle_missing_solve_path_metadata():
    """Test oracle raises error when solve_path metadata is missing."""
    from inspect_harbor.harbor._solver import CopySolutionDirError, oracle

    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={"solution_dir": "/fake/solution"},  # Missing solve_path
    )

    solver_fn = oracle()

    with pytest.raises(CopySolutionDirError, match="solve_path not found in metadata"):
        await solver_fn(state, Mock())


@pytest.mark.asyncio
async def test_oracle_solution_directory_not_found():
    """Test oracle raises error when solution directory doesn't exist."""
    from inspect_harbor.harbor._solver import CopySolutionDirError, oracle

    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/nonexistent/solution",
            "solve_path": "/nonexistent/solution/solve.sh",
        },
    )

    solver_fn = oracle()

    with pytest.raises(CopySolutionDirError, match="Solution directory not found"):
        await solver_fn(state, Mock())


@pytest.mark.asyncio
async def test_oracle_solve_path_not_relative_to_solution_dir():
    """Test oracle raises error when solve_path is not relative to solution_dir."""
    from inspect_harbor.harbor._solver import CopySolutionDirError, oracle

    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/fake/solution",
            "solve_path": "/completely/different/path/solve.sh",  # Not relative
        },
    )

    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    with (
        patch("inspect_harbor.harbor._solver.sandbox", return_value=mock_sandbox),
        patch("pathlib.Path.exists", return_value=True),
        pytest.raises(
            CopySolutionDirError,
            match="Solve path .* is not relative to solution directory",
        ),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())


@pytest.mark.asyncio
async def test_oracle_cleans_up_env_vars_after_execution():
    """Test that oracle cleans up environment variables after executing solution."""
    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/fake/solution",
            "solve_path": "/fake/solution/solve.sh",
            "solution_env": {
                "API_KEY": "test-key-789",
                "MODEL": "test-model",
                "DEBUG": "true",
            },
        },
    )

    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    # Track exec calls to verify env cleanup was called
    exec_calls: list[list[str]] = []

    async def track_exec(cmd: list[str], **_kwargs: object) -> Mock:
        exec_calls.append(cmd)
        return Mock(returncode=0, stdout="", stderr="")

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)

    with (
        patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ),
        patch("inspect_harbor.harbor._solver.sandbox", return_value=mock_sandbox),
        patch(
            "inspect_harbor.harbor._solver.copy_directory_to_sandbox",
            new_callable=AsyncMock,
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())

        # Verify cleanup was called AFTER solution execution
        # Expected calls:
        # 1. bash solve.sh
        # 2. unset API_KEY
        # 3. unset MODEL
        # 4. unset DEBUG
        assert len(exec_calls) == 4
        assert exec_calls[0] == ["bash", "-l", "/solution/solve.sh"]
        env_cleanup_calls = exec_calls[1:]
        assert ["unset", "API_KEY"] in env_cleanup_calls
        assert ["unset", "MODEL"] in env_cleanup_calls
        assert ["unset", "DEBUG"] in env_cleanup_calls


@pytest.mark.asyncio
async def test_oracle_no_env_cleanup_when_no_env_vars():
    """Test that oracle doesn't call env cleanup when solution_env is not set."""
    state = TaskState(
        model=ModelName("mockprovider/test-model"),
        sample_id="test-sample",
        epoch=0,
        input="test input",
        messages=[],
        metadata={
            "solution_dir": "/fake/solution",
            "solve_path": "/fake/solution/solve.sh",
            # No solution_env
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
        patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ),
        patch("inspect_harbor.harbor._solver.sandbox", return_value=mock_sandbox),
        patch(
            "inspect_harbor.harbor._solver.copy_directory_to_sandbox",
            new_callable=AsyncMock,
        ),
        patch("pathlib.Path.exists", return_value=True),
    ):
        solver_fn = oracle()
        await solver_fn(state, Mock())

        # Should only have solution script execution (no env cleanup)
        assert len(exec_calls) == 1
        assert exec_calls[0] == ["bash", "-l", "/solution/solve.sh"]


@pytest.mark.asyncio
async def test_cleanup_sandbox_env_vars_unit():
    """Test cleanup_sandbox_env_vars function directly."""
    mock_sandbox = Mock()
    mock_exec_result = Mock()
    mock_exec_result.success = True
    mock_sandbox.exec = AsyncMock(return_value=mock_exec_result)

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        await cleanup_sandbox_env_vars(["VAR1", "VAR2", "VAR3"])

        assert mock_sandbox.exec.call_count == 3
        calls = mock_sandbox.exec.call_args_list

        assert calls[0][0][0] == ["unset", "VAR1"]
        assert calls[1][0][0] == ["unset", "VAR2"]
        assert calls[2][0][0] == ["unset", "VAR3"]
