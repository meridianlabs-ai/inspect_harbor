"""Tests for Harbor scorer."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from inspect_harbor._sandbox_utils import copy_directory_to_sandbox
from inspect_harbor._scorer import (
    RewardFileEmptyError,
    RewardFileNotFoundError,
    VerifierOutputParseError,
    _parse_reward_file,
)


@pytest.mark.asyncio
async def test_parse_reward_txt_valid():
    """Test parsing valid reward.txt with float value."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(return_value="0.85")

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
        result = await _parse_reward_file(exit_code=0)

        assert result == 0.85
        mock_sandbox.read_file.assert_called_once_with("/logs/verifier/reward.txt")


@pytest.mark.asyncio
async def test_parse_reward_txt_empty():
    """Test parsing empty reward.txt raises RewardFileEmptyError."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(return_value="   ")

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
        with pytest.raises(RewardFileEmptyError, match="Reward file is empty"):
            await _parse_reward_file(exit_code=0)


@pytest.mark.asyncio
async def test_parse_reward_txt_invalid():
    """Test parsing reward.txt with invalid content raises VerifierOutputParseError."""
    mock_sandbox = Mock()
    mock_sandbox.read_file = AsyncMock(return_value="not a number")

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
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

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
        result = await _parse_reward_file(exit_code=0)

        assert result == 1.0


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

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
        result = await _parse_reward_file(exit_code=0)

        assert result == 0.75


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

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
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

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
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

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
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

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
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

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
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

    with patch("inspect_harbor._sandbox_utils.sandbox", return_value=mock_sandbox):
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
