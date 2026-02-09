"""Tests for Harbor scorer."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from inspect_ai.scorer import Target
from inspect_ai.solver import TaskState
from inspect_harbor.harbor._sandbox_utils import (
    cleanup_sandbox_directories,
    cleanup_sandbox_env_vars,
    copy_directory_to_sandbox,
    resolve_env_vars,
)
from inspect_harbor.harbor._scorer import (
    CopyTestsDirError,
    RewardFileEmptyError,
    RewardFileNotFoundError,
    VerifierOutputParseError,
    _parse_reward_file,
    harbor_scorer,
)


@pytest.mark.asyncio
async def test_parse_reward_txt_valid():
    """Test parsing valid reward.txt with float value."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(return_value="0.85")

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        reward_value, reward_dict = await _parse_reward_file(exit_code=0)

        assert reward_value == 0.85
        assert reward_dict is None
        mock_sandbox.read_file.assert_called_once_with("/logs/verifier/reward.txt")


@pytest.mark.asyncio
async def test_parse_reward_txt_empty():
    """Test parsing empty reward.txt raises RewardFileEmptyError."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(return_value="   ")

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with pytest.raises(RewardFileEmptyError, match="Reward file is empty"):
            await _parse_reward_file(exit_code=0)


@pytest.mark.asyncio
async def test_parse_reward_txt_invalid():
    """Test parsing reward.txt with invalid content raises VerifierOutputParseError."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(return_value="not a number")

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with pytest.raises(
            VerifierOutputParseError, match="Failed to parse reward.txt as float"
        ):
            await _parse_reward_file(exit_code=0)


@pytest.mark.asyncio
async def test_parse_reward_json_with_reward_key():
    """Test parsing reward.json with 'reward' key."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(
        side_effect=[
            FileNotFoundError(),  # reward.txt not found
            json.dumps({"reward": 1.0, "other": 0.5}),  # reward.json found
        ]
    )

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        reward_value, reward_dict = await _parse_reward_file(exit_code=0)

        assert reward_value == 1.0
        assert reward_dict == {"reward": 1.0, "other": 0.5}


@pytest.mark.asyncio
async def test_parse_reward_json_with_other_keys():
    """Test parsing reward.json with other keys (uses first value)."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(
        side_effect=[
            FileNotFoundError(),  # reward.txt not found
            json.dumps({"score": 0.75}),  # reward.json found
        ]
    )

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        reward_value, reward_dict = await _parse_reward_file(exit_code=0)

        assert reward_value == 0.75
        assert reward_dict == {"score": 0.75}


@pytest.mark.asyncio
async def test_parse_reward_json_with_mixed_types():
    """Test parsing reward.json with mixed value types (float, str, int, bool)."""
    mock_sandbox = Mock()
    mixed_reward = {
        "reward": 0.8,
        "status": "passed",
        "attempts": 3,
        "success": True,
        "details": {"accuracy": 0.9},
    }
    mock_sandbox.read_file = AsyncMock(
        side_effect=[
            FileNotFoundError(),  # reward.txt not found
            json.dumps(mixed_reward),  # reward.json found with mixed types
        ]
    )

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        reward_value, reward_dict = await _parse_reward_file(exit_code=0)

        assert reward_value == 0.8
        assert reward_dict is not None
        assert reward_dict == mixed_reward


@pytest.mark.asyncio
async def test_parse_reward_json_empty():
    """Test parsing empty reward.json raises RewardFileEmptyError."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(
        side_effect=[
            FileNotFoundError(),  # reward.txt not found
            "   ",  # reward.json empty
        ]
    )

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with pytest.raises(RewardFileEmptyError, match="Reward file is empty"):
            await _parse_reward_file(exit_code=0)


@pytest.mark.asyncio
async def test_parse_reward_json_invalid():
    """Test parsing invalid reward.json raises VerifierOutputParseError."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(
        side_effect=[
            FileNotFoundError(),  # reward.txt not found
            "not valid json",  # reward.json invalid
        ]
    )

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with pytest.raises(
            VerifierOutputParseError, match="Failed to parse reward.json"
        ):
            await _parse_reward_file(exit_code=0)


@pytest.mark.asyncio
async def test_parse_reward_neither_file_exists():
    """Test neither reward file exists raises RewardFileNotFoundError."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(
        side_effect=[
            FileNotFoundError(),  # reward.txt not found
            FileNotFoundError(),  # reward.json not found
        ]
    )

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with pytest.raises(
            RewardFileNotFoundError, match="No reward file found.*exit code was 1"
        ):
            await _parse_reward_file(exit_code=1)


@pytest.mark.asyncio
async def test_copy_directory_to_sandbox(tmp_path: Path):
    """Test copying directory to sandbox."""
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test.sh").write_text("#!/bin/bash\necho 'test'")
    (test_dir / "test.py").write_text("import pytest")

    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        await copy_directory_to_sandbox(test_dir, "/tests")

        assert mock_sandbox.write_file.call_count == 2

        calls = mock_sandbox.write_file.call_args_list
        calls_dict = {call[0][0]: call[0][1] for call in calls}

        # All files copied as bytes
        assert "/tests/test.sh" in calls_dict
        assert isinstance(calls_dict["/tests/test.sh"], bytes)
        assert "/tests/test.py" in calls_dict
        assert isinstance(calls_dict["/tests/test.py"], bytes)


@pytest.mark.asyncio
async def test_copy_nested_directory_to_sandbox(tmp_path: Path):
    """Test copying nested directory structure to sandbox."""
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test.sh").write_text("#!/bin/bash")

    nested_dir = test_dir / "utils"
    nested_dir.mkdir()
    (nested_dir / "helper.py").write_text("def helper(): pass")

    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        await copy_directory_to_sandbox(test_dir, "/tests")

        assert mock_sandbox.write_file.call_count == 2

        calls = mock_sandbox.write_file.call_args_list
        calls_dict = {call[0][0]: call[0][1] for call in calls}

        # All files copied as bytes
        assert "/tests/test.sh" in calls_dict
        assert isinstance(calls_dict["/tests/test.sh"], bytes)
        assert "/tests/utils/helper.py" in calls_dict
        assert isinstance(calls_dict["/tests/utils/helper.py"], bytes)


@pytest.mark.asyncio
async def test_copy_binary_files_to_sandbox(tmp_path: Path):
    """Test copying text and binary files to sandbox."""
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

    # Create a text file
    text_content = b"This is a text file"
    (test_dir / "readme.txt").write_bytes(text_content)

    # Create a binary file (simulated PNG header)
    binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"
    (test_dir / "image.png").write_bytes(binary_content)

    # Create another binary file (simulated compiled Python)
    pyc_content = b"\x42\x0d\x0d\x0a\x00\x00\x00\x00"
    (test_dir / "module.pyc").write_bytes(pyc_content)

    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        await copy_directory_to_sandbox(test_dir, "/tests")

        # Should copy all 3 files
        assert mock_sandbox.write_file.call_count == 3

        calls = mock_sandbox.write_file.call_args_list
        calls_dict = {call[0][0]: call[0][1] for call in calls}

        # Verify all files copied as bytes
        assert "/tests/readme.txt" in calls_dict
        assert calls_dict["/tests/readme.txt"] == text_content
        assert isinstance(calls_dict["/tests/readme.txt"], bytes)

        assert "/tests/image.png" in calls_dict
        assert calls_dict["/tests/image.png"] == binary_content
        assert isinstance(calls_dict["/tests/image.png"], bytes)

        assert "/tests/module.pyc" in calls_dict
        assert calls_dict["/tests/module.pyc"] == pyc_content
        assert isinstance(calls_dict["/tests/module.pyc"], bytes)


@pytest.mark.asyncio
async def test_cleanup_sandbox_directories():
    """Test cleanup removes specified directories."""
    mock_sandbox = Mock()
    mock_exec_result = Mock()
    mock_exec_result.success = True
    mock_sandbox.exec = AsyncMock(return_value=mock_exec_result)

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        await cleanup_sandbox_directories("/tests", "/logs/verifier")

        # Should call rm -rf for both directories
        assert mock_sandbox.exec.call_count == 2
        calls = mock_sandbox.exec.call_args_list

        # Check /tests directory removal
        assert calls[0][0][0] == ["rm", "-rf", "/tests"]

        # Check /logs/verifier directory removal
        assert calls[1][0][0] == ["rm", "-rf", "/logs/verifier"]


@pytest.mark.asyncio
async def test_cleanup_sandbox_directories_handles_errors():
    """Test cleanup handles errors gracefully without raising exceptions."""
    mock_sandbox = Mock()
    # Simulate exec failures
    mock_sandbox.exec = AsyncMock(side_effect=RuntimeError("Sandbox exec failed"))

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        # Should not raise exception
        await cleanup_sandbox_directories("/tests", "/logs/verifier")

        # Should still attempt both cleanups despite errors
        assert mock_sandbox.exec.call_count == 2


@pytest.mark.asyncio
async def test_cleanup_sandbox_directories_partial_failure():
    """Test cleanup continues even if first removal fails."""
    mock_sandbox = Mock()
    # First call fails, second succeeds
    mock_exec_success = Mock()
    mock_exec_success.success = True
    mock_sandbox.exec = AsyncMock(
        side_effect=[OSError("Permission denied"), mock_exec_success]
    )

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        # Should not raise exception
        await cleanup_sandbox_directories("/tests", "/logs/verifier")

        # Should attempt both cleanups
        assert mock_sandbox.exec.call_count == 2


@pytest.mark.asyncio
async def test_harbor_scorer_stores_reward_dict_in_metadata(tmp_path: Path):
    """Test that harbor_scorer stores reward_dict in Score.metadata when using JSON."""
    # Create temporary test directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_script = tests_dir / "test.sh"
    test_script.write_text("#!/bin/bash\necho 'test'")

    # Setup mock state
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {
        "tests_dir": str(tests_dir),
        "test_path": str(test_script),
        "verifier_timeout_sec": 60,
    }

    mock_target = Mock(spec=Target)

    # Setup mock sandbox
    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    # Mock exec for test script execution
    mock_exec_result = Mock()
    mock_exec_result.returncode = 0
    mock_exec_result.stdout = "test output"
    mock_exec_result.stderr = ""
    mock_sandbox.exec = AsyncMock(return_value=mock_exec_result)

    # Mock reward file reading - return JSON with multiple keys
    reward_json = {"reward": 0.8, "accuracy": 0.9, "completion": 0.7}
    mock_sandbox.read_file = AsyncMock(
        side_effect=[
            FileNotFoundError(),  # reward.txt not found
            json.dumps(reward_json),  # reward.json found
        ]
    )

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ):
            scorer = harbor_scorer()
            result = await scorer(mock_state, mock_target)

            # Verify scoring completed successfully
            assert result is not None
            assert result.value == 0.8
            assert result.answer == "PASS"
            assert result.metadata is not None
            assert result.metadata["reward_dict"] == reward_json


@pytest.mark.asyncio
async def test_scorer_missing_tests_dir_metadata():
    """Test scorer raises error when tests_dir metadata is missing."""
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {}  # Missing tests_dir
    mock_target = Mock(spec=Target)

    scorer = harbor_scorer()

    with pytest.raises(CopyTestsDirError, match="tests_dir not found in metadata"):
        await scorer(mock_state, mock_target)


@pytest.mark.asyncio
async def test_scorer_missing_test_path_metadata():
    """Test scorer raises error when test_path metadata is missing."""
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {"tests_dir": "/some/path"}  # Missing test_path
    mock_target = Mock(spec=Target)

    scorer = harbor_scorer()

    with pytest.raises(CopyTestsDirError, match="test_path not found in metadata"):
        await scorer(mock_state, mock_target)


@pytest.mark.asyncio
async def test_scorer_tests_directory_not_found():
    """Test scorer raises error when tests directory doesn't exist."""
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {
        "tests_dir": "/nonexistent/tests",
        "test_path": "/nonexistent/tests/test.sh",
    }
    mock_target = Mock(spec=Target)

    scorer = harbor_scorer()

    with pytest.raises(CopyTestsDirError, match="Tests directory not found"):
        await scorer(mock_state, mock_target)


@pytest.mark.asyncio
async def test_scorer_test_path_not_relative_to_tests_dir(tmp_path: Path):
    """Test scorer raises error when test_path is not relative to tests_dir."""
    # Create a real tests directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {
        "tests_dir": str(tests_dir),
        "test_path": "/completely/different/path/test.sh",  # Not relative
    }
    mock_target = Mock(spec=Target)

    scorer = harbor_scorer()

    with pytest.raises(
        CopyTestsDirError,
        match="Test path .* is not relative to tests directory",
    ):
        await scorer(mock_state, mock_target)


@pytest.mark.asyncio
async def test_harbor_scorer_calls_cleanup_after_scoring(tmp_path: Path):
    """Test that harbor_scorer calls cleanup after scoring completes."""
    # Create temporary test directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_script = tests_dir / "test.sh"
    test_script.write_text("#!/bin/bash\necho 'test'")

    # Setup mock state
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {
        "tests_dir": str(tests_dir),
        "test_path": str(test_script),
        "verifier_timeout_sec": 60,
    }

    mock_target = Mock(spec=Target)

    # Setup mock sandbox
    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    # Mock exec for test script execution
    mock_exec_result = Mock()
    mock_exec_result.returncode = 0
    mock_exec_result.stdout = "test output"
    mock_exec_result.stderr = ""

    # Track exec calls: first for test script, then for cleanup (2 rm calls)
    exec_calls: list[list[str]] = []

    async def track_exec(cmd: list[str], **_kwargs: object) -> Mock:
        exec_calls.append(cmd)
        return mock_exec_result

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)

    # Mock reward file reading
    mock_sandbox.read_file = AsyncMock(return_value="1.0")

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ):
            scorer = harbor_scorer()
            result = await scorer(mock_state, mock_target)

            # Verify scoring completed successfully
            assert result is not None
            assert result.value == 1.0
            assert result.answer == "PASS"
            assert result.metadata is None  # reward.txt returns None for reward_dict

            # Verify cleanup was called AFTER scoring
            # Should have: [mkdir /logs/agent, mkdir /logs/verifier, bash test.sh, rm /tests, rm /logs/verifier]
            assert len(exec_calls) == 5
            assert exec_calls[0] == ["mkdir", "-p", "/logs/agent"]  # Setup logs
            assert exec_calls[1] == ["mkdir", "-p", "/logs/verifier"]  # Setup logs
            assert exec_calls[2] == ["bash", "-l", "/tests/test.sh"]  # Test execution
            assert exec_calls[3] == ["rm", "-rf", "/tests"]  # Cleanup /tests
            assert exec_calls[4] == [
                "rm",
                "-rf",
                "/logs/verifier",
            ]  # Cleanup /logs/verifier


def test_resolve_env_vars_with_template(monkeypatch: pytest.MonkeyPatch):
    """Test resolving environment variables with ${VAR} template syntax."""
    monkeypatch.setenv("TEST_API_KEY", "sk-test-123")
    monkeypatch.setenv("TEST_MODEL", "gpt-4")

    env_dict = {
        "OPENAI_API_KEY": "${TEST_API_KEY}",
        "MODEL_NAME": "${TEST_MODEL}",
    }

    resolved = resolve_env_vars(env_dict)

    assert resolved["OPENAI_API_KEY"] == "sk-test-123"
    assert resolved["MODEL_NAME"] == "gpt-4"


def test_resolve_env_vars_with_literal():
    """Test resolving environment variables with literal (non-template) values."""
    env_dict = {
        "OPENAI_API_KEY": "sk-literal-key",
        "MODEL_NAME": "gpt-4o",
        "TIMEOUT": "300",
    }

    resolved = resolve_env_vars(env_dict)

    assert resolved["OPENAI_API_KEY"] == "sk-literal-key"
    assert resolved["MODEL_NAME"] == "gpt-4o"
    assert resolved["TIMEOUT"] == "300"


def test_resolve_env_vars_mixed(monkeypatch: pytest.MonkeyPatch):
    """Test resolving mix of template and literal values."""
    monkeypatch.setenv("TEST_KEY", "secret-value")

    env_dict = {
        "API_KEY": "${TEST_KEY}",
        "MODEL": "gpt-4o",
        "TIMEOUT": "600",
    }

    resolved = resolve_env_vars(env_dict)

    assert resolved["API_KEY"] == "secret-value"
    assert resolved["MODEL"] == "gpt-4o"
    assert resolved["TIMEOUT"] == "600"


def test_resolve_env_vars_missing_variable():
    """Test that missing environment variable raises ValueError."""
    env_dict = {"API_KEY": "${NONEXISTENT_VAR}"}

    with pytest.raises(
        ValueError, match="Environment variable 'NONEXISTENT_VAR' not found"
    ):
        resolve_env_vars(env_dict)


def test_resolve_env_vars_empty_dict():
    """Test resolving empty dictionary returns empty dictionary."""
    resolved = resolve_env_vars({})
    assert resolved == {}


@pytest.mark.asyncio
async def test_harbor_scorer_passes_verifier_env_to_exec(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test that harbor_scorer passes resolved verifier_env to sandbox().exec()."""
    # Set up test environment variable
    monkeypatch.setenv("TEST_SCORER_API_KEY", "sk-test-scorer-123")

    # Create temporary test directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_script = tests_dir / "test.sh"
    test_script.write_text("#!/bin/bash\necho 'test'")

    # Setup mock state with verifier_env
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {
        "tests_dir": str(tests_dir),
        "test_path": str(test_script),
        "verifier_timeout_sec": 60,
        "verifier_env": {
            "OPENAI_API_KEY": "${TEST_SCORER_API_KEY}",
            "MODEL_NAME": "gpt-4o",
        },
    }

    mock_target = Mock(spec=Target)

    # Setup mock sandbox
    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    # Track exec calls to verify env was passed
    exec_calls: list[dict[str, Any]] = []

    async def track_exec(cmd: list[str], **kwargs: object) -> Mock:
        exec_calls.append({"cmd": cmd, "kwargs": kwargs})
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        return mock_result

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)
    mock_sandbox.read_file = AsyncMock(return_value="1.0")

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox",
            return_value=mock_sandbox,
        ):
            scorer = harbor_scorer()
            result = await scorer(mock_state, mock_target)

            # Verify scoring completed successfully
            assert result is not None
            assert result.value == 1.0

            # Find the test execution call (should be the one with bash -l)
            test_exec_call = next(
                call for call in exec_calls if call["cmd"][0] == "bash"
            )

            # Verify env was passed with resolved values
            assert "env" in test_exec_call["kwargs"]
            passed_env = test_exec_call["kwargs"]["env"]
            assert passed_env["OPENAI_API_KEY"] == "sk-test-scorer-123"
            assert passed_env["MODEL_NAME"] == "gpt-4o"


@pytest.mark.asyncio
async def test_harbor_scorer_no_verifier_env(tmp_path: Path):
    """Test that harbor_scorer works when verifier_env is not in metadata."""
    # Create temporary test directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_script = tests_dir / "test.sh"
    test_script.write_text("#!/bin/bash\necho 'test'")

    # Setup mock state WITHOUT verifier_env
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {
        "tests_dir": str(tests_dir),
        "test_path": str(test_script),
        "verifier_timeout_sec": 60,
    }

    mock_target = Mock(spec=Target)

    # Setup mock sandbox
    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    # Track exec calls
    exec_calls: list[dict[str, Any]] = []

    async def track_exec(cmd: list[str], **kwargs: object) -> Mock:
        exec_calls.append({"cmd": cmd, "kwargs": kwargs})
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        return mock_result

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)
    mock_sandbox.read_file = AsyncMock(return_value="1.0")

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ):
            scorer = harbor_scorer()
            result = await scorer(mock_state, mock_target)

            # Verify scoring completed successfully
            assert result is not None
            assert result.value == 1.0

            # Find the test execution call
            test_exec_call = next(
                call for call in exec_calls if call["cmd"][0] == "bash"
            )

            # Verify env was passed as None (not in metadata)
            assert "env" in test_exec_call["kwargs"]
            assert test_exec_call["kwargs"]["env"] is None


@pytest.mark.asyncio
async def test_harbor_scorer_empty_verifier_env(tmp_path: Path):
    """Test that harbor_scorer handles empty verifier_env dict."""
    # Create temporary test directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_script = tests_dir / "test.sh"
    test_script.write_text("#!/bin/bash\necho 'test'")

    # Setup mock state with empty verifier_env
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {
        "tests_dir": str(tests_dir),
        "test_path": str(test_script),
        "verifier_timeout_sec": 60,
        "verifier_env": {},
    }

    mock_target = Mock(spec=Target)

    # Setup mock sandbox
    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    # Track exec calls
    exec_calls: list[dict[str, Any]] = []

    async def track_exec(cmd: list[str], **kwargs: object) -> Mock:
        exec_calls.append({"cmd": cmd, "kwargs": kwargs})
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        return mock_result

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)
    mock_sandbox.read_file = AsyncMock(return_value="1.0")

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
        ):
            scorer = harbor_scorer()
            result = await scorer(mock_state, mock_target)

            # Verify scoring completed successfully
            assert result is not None
            assert result.value == 1.0

            # Find the test execution call
            test_exec_call = next(
                call for call in exec_calls if call["cmd"][0] == "bash"
            )

            # Verify env was passed as None (empty dict)
            assert "env" in test_exec_call["kwargs"]
            assert test_exec_call["kwargs"]["env"] is None


@pytest.mark.asyncio
async def test_cleanup_sandbox_env_vars():
    """Test cleanup_sandbox_env_vars unsets specified environment variables."""
    mock_sandbox = Mock()
    mock_exec_result = Mock()
    mock_exec_result.success = True
    mock_sandbox.exec = AsyncMock(return_value=mock_exec_result)

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        await cleanup_sandbox_env_vars(["API_KEY", "SECRET_TOKEN", "MODEL_NAME"])

        # Should call unset for each environment variable
        assert mock_sandbox.exec.call_count == 3
        calls = mock_sandbox.exec.call_args_list

        # Check each unset call
        assert calls[0][0][0] == ["unset", "API_KEY"]
        assert calls[1][0][0] == ["unset", "SECRET_TOKEN"]
        assert calls[2][0][0] == ["unset", "MODEL_NAME"]


@pytest.mark.asyncio
async def test_cleanup_sandbox_env_vars_handles_errors():
    """Test cleanup_sandbox_env_vars handles errors gracefully without raising exceptions."""
    mock_sandbox = Mock()
    # Simulate exec failures
    mock_sandbox.exec = AsyncMock(side_effect=RuntimeError("Sandbox exec failed"))

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        # Should not raise exception
        await cleanup_sandbox_env_vars(["VAR1", "VAR2"])

        # Should still attempt both cleanups despite errors
        assert mock_sandbox.exec.call_count == 2


@pytest.mark.asyncio
async def test_cleanup_sandbox_env_vars_partial_failure():
    """Test cleanup_sandbox_env_vars continues even if first unset fails."""
    mock_sandbox = Mock()
    # First call fails, second succeeds
    mock_exec_success = Mock()
    mock_exec_success.success = True
    mock_sandbox.exec = AsyncMock(
        side_effect=[OSError("Variable not found"), mock_exec_success]
    )

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        # Should not raise exception
        await cleanup_sandbox_env_vars(["VAR1", "VAR2"])

        # Should attempt both cleanups
        assert mock_sandbox.exec.call_count == 2


@pytest.mark.asyncio
async def test_cleanup_sandbox_env_vars_empty_list():
    """Test cleanup_sandbox_env_vars handles empty list gracefully."""
    mock_sandbox = Mock()
    mock_sandbox.exec = AsyncMock()

    with patch(
        "inspect_harbor.harbor._sandbox_utils.sandbox", return_value=mock_sandbox
    ):
        await cleanup_sandbox_env_vars([])

        # Should not call exec for empty list
        assert mock_sandbox.exec.call_count == 0


@pytest.mark.asyncio
async def test_harbor_scorer_cleans_up_env_vars_after_scoring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test that harbor_scorer cleans up environment variables after scoring."""
    # Set up test environment variable
    monkeypatch.setenv("TEST_CLEANUP_KEY", "sk-test-cleanup-456")

    # Create temporary test directory
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_script = tests_dir / "test.sh"
    test_script.write_text("#!/bin/bash\necho 'test'")

    # Setup mock state with verifier_env
    mock_state = Mock(spec=TaskState)
    mock_state.metadata = {
        "tests_dir": str(tests_dir),
        "test_path": str(test_script),
        "verifier_timeout_sec": 60,
        "verifier_env": {
            "OPENAI_API_KEY": "${TEST_CLEANUP_KEY}",
            "MODEL_NAME": "gpt-4o",
        },
    }

    mock_target = Mock(spec=Target)

    # Setup mock sandbox
    mock_sandbox = Mock()
    mock_sandbox.write_file = AsyncMock()

    # Track exec calls to verify env cleanup was called
    exec_calls: list[list[str]] = []

    async def track_exec(cmd: list[str], **_kwargs: object) -> Mock:
        exec_calls.append(cmd)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        return mock_result

    mock_sandbox.exec = AsyncMock(side_effect=track_exec)
    mock_sandbox.read_file = AsyncMock(return_value="1.0")

    with patch("inspect_harbor.harbor._scorer.sandbox", return_value=mock_sandbox):
        with patch(
            "inspect_harbor.harbor._sandbox_utils.sandbox",
            return_value=mock_sandbox,
        ):
            scorer = harbor_scorer()
            result = await scorer(mock_state, mock_target)

            # Verify scoring completed successfully
            assert result is not None
            assert result.value == 1.0

            # Verify cleanup was called AFTER scoring
            # Expected calls:
            # 1. mkdir /logs/agent
            # 2. mkdir /logs/verifier
            # 3. bash test.sh
            # 4. rm /tests
            # 5. rm /logs/verifier
            # 6. unset OPENAI_API_KEY
            # 7. unset MODEL_NAME
            assert len(exec_calls) == 7
            assert exec_calls[0] == ["mkdir", "-p", "/logs/agent"]
            assert exec_calls[1] == ["mkdir", "-p", "/logs/verifier"]
            assert exec_calls[2] == ["bash", "-l", "/tests/test.sh"]
            assert exec_calls[3] == ["rm", "-rf", "/tests"]
            assert exec_calls[4] == ["rm", "-rf", "/logs/verifier"]
            # Check cleanup was called for all env vars
            env_cleanup_calls = exec_calls[5:]
            assert ["unset", "OPENAI_API_KEY"] in env_cleanup_calls
            assert ["unset", "MODEL_NAME"] in env_cleanup_calls
